import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs).get('href', ''))
    def handle_data(self, data):
        self.parts.append(data)

class LegalCopy(unittest.TestCase):
    def test_privacy_and_unsubscribe(self):
        parser = Links()
        parser.feed((ROOT / 'lectores-beta/index.html').read_text(encoding='utf-8'))
        text = re.sub(r'\s+', ' ', ' '.join(parser.parts)).casefold()
        self.assertIn('puedes darte de baja', text, '/lectores-beta/: falta explicar el derecho de baja')
        self.assertIn('política de privacidad', text, '/lectores-beta/: falta la referencia a privacidad')
        for destination in ('/privacidad.html', '/prensa.html#contacto'):
            with self.subTest(destination=destination):
                self.assertIn(destination, parser.links, f'/lectores-beta/: falta el enlace {destination}')
                parts = urlsplit(destination)
                relative = unquote(parts.path).lstrip('/')
                target = ROOT / relative
                if parts.path.endswith('/'):
                    target = target / 'index.html'
                self.assertTrue(target.is_file(), f'/lectores-beta/: destino inexistente {destination}')
                if parts.fragment:
                    html = target.read_text(encoding='utf-8')
                    self.assertRegex(html, r'\bid\s*=\s*[\"\']' + re.escape(parts.fragment) + r'[\"\']', f'/lectores-beta/: ancla inexistente {destination}')

if __name__ == '__main__':
    unittest.main()