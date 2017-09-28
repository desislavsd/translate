import sublime, sublime_plugin, re
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib import error
from json import loads

api = 'https://translate.googleapis.com/translate_a/single?'

headers = {
	'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'
}
		

settings = False

class TranslateCommand(sublime_plugin.TextCommand):

	def run(self, edit):
		
		settings = sublime.load_settings("translate.sublime-settings")

		# READ USER SETTINGS
		bg_en_only = settings.get('bg_en_only') or False
		source_lang = settings.get('source_lang') or 'auto'
		target_lang = settings.get('target_lang') or 'bg'

		v = self.view
		regions = v.sel() # selections

		for region in regions:

			# if no selection -> translate the closest word
			pt = region.empty() and region or v.word(region)
			phrase = v.substr(pt)
			# if the word is shorter than 1 -> do nothing
			if len(phrase.strip()) > 1:
				invert = re.search('[а-я]', phrase, flags=re.IGNORECASE)
				params = {
					'client': 'gtx',
					'dt'	: 'bd',
					'dj'	: 1,
					'sl'	: bg_en_only and ('bg' if invert else 'en') or source_lang,
					'tl'	: bg_en_only and ('en' if invert else 'bg') or target_lang,
					'q'		: phrase
				}
				sublime.status_message( 'translate: ' + params['sl'] + ' => ' + params['tl'])
				# PREPARE THE REQUEST
				req = Request(api + urlencode(params) + '&dt=t', headers = headers)

				# TRY TO MAKE THE REQUEST; TIMEOUT IS IN SECONDS
				try:
					json = urlopen(req, timeout = 4).read()

				# CATCH ERRORS IF ANY
				except error.HTTPError as err:
					if err.code == 404:
						return sublime.status_message('404')
					else:
						return sublime.status_message(str(err))

				res = loads(json.decode('utf-8'), '')

				items = [''.join(map(lambda x: x['trans'], res['sentences'])), '-'];

				if 'dict' in res:
					for list in res['dict']:
						items.extend(list['terms'])
						items.append('-')

				def on_select(i):
					if i > -1:
						# select the whole region that will be replaced
						regions.add(region.cover(pt));
						v.replace(edit, pt, items[i])


				if len(regions) < 2 and len(items) > 4: 
					v.show_popup_menu(items, on_select)
				else:
					on_select(0)

