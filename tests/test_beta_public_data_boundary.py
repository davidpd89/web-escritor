import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('lectores-beta/index.html', 'lectores-beta/enviar-manuscrito/index.html')

class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []
        self.forms = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'input':
            self.inputs.append(a)
        elif tag == 'form':
            self.forms.append(a)
        elif tag == 'a':
            self.links.append(a)

class PublicDataBoundaryTest(unittest.TestCase):
    def test_public_pages_do_not_expose_private_submissions(self):
        for path in PAGES:
            with self.subTest(page=path):
                html = (ROOT / path).read_text(encoding='utf-8')
                parser = Audit()
                parser.feed(html)
                self.assertFalse([i for i in parser.inputs if i.get('type', '').lower() == 'file'], f'{path}: subida pública de manuscritos inesperada')
                self.assertFalse([f for f in parser.forms if urlparse(f.get('action', '')).netloc], f'{path}: formulario con destino externo declarado')
                self.assertFalse([a for a in parser.links if a.get('href', '').lower().startswith('mailto:')], f'{path}: dirección de contacto expuesta directamente en HTML')
                self.assertNotRegex(html, r'(?i)(?:beta-reader|beta-reader-email|participant-email|manuscript-owner-email)\s*[=:]\s*[\x22\x27][^\x22\x27]+@', f'{path}: posible dato personal publicado')
                self.assertNotRegex(html, r'(?i)<script[^>]+src=[\x22\x27]https?://[^\x22\x27]+', f'{path}: script externo directo inesperado')

if __name__ == '__main__':
    unittest.main()
