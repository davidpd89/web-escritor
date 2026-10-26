import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'lectores-beta/index.html'

class Forms(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form':
            self.current = {'attrs': a, 'inputs': []}
            self.forms.append(self.current)
        elif tag == 'input' and self.current is not None:
            self.current['inputs'].append(a)

    def handle_endtag(self, tag):
        if tag == 'form':
            self.current = None

class BetaConsentStaticTest(unittest.TestCase):
    def test_separate_consent_and_source(self):
        parser = Forms()
        parser.feed((ROOT / PAGE).read_text(encoding='utf-8'))
        matches = [f for f in parser.forms if f['attrs'].get('id') == 'lectores-beta-form']
        self.assertEqual(len(matches), 1, f'{PAGE}: debe existir exactamente un formulario beta')
        form = matches[0]
        self.assertEqual(form['attrs'].get('data-newsletter-source'), 'lectores-beta', f'{PAGE}: fuente incorrecta')
        consents = [i for i in form['inputs'] if i.get('type') == 'checkbox' and 'required' in i]
        self.assertEqual(len(consents), 1, f'{PAGE}: consentimiento beta obligatorio ausente')
        self.assertEqual(consents[0].get('name'), 'consent', f'{PAGE}: consentimiento sin identidad')
        script = (ROOT / 'assets/newsletter-general.js').read_text(encoding='utf-8')
        block = re.search(r'const PENDING_COPY\s*=\s*\{(.*?)\};', script, re.S)
        self.assertIsNotNone(block, 'assets/newsletter-general.js: no se localiza el registro de fuentes generales')
        self.assertNotRegex(block.group(1), r'[\x27\x22]?lectores-beta[\x27\x22]?\s*:', 'assets/newsletter-general.js: la fuente beta no debe pertenecer al registro general')
        self.assertIn('Object.hasOwn(PENDING_COPY, source)', script, 'assets/newsletter-general.js: falta la restricción de fuentes')

if __name__ == '__main__':
    unittest.main()
