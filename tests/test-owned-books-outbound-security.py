import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    'libros/index.html',
    'libros/samuel-entre-mundos/index.html',
    'las-manecillas-del-recuerdo/index.html',
]

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))

class TestOutboundSecurity(unittest.TestCase):
    def test_external_links(self):
        for page in PAGES:
            parser = Anchors()
            parser.feed((ROOT / page).read_text(encoding='utf-8'))
            external = []
            for link in parser.links:
                href = link.get('href', '') or ''
                url = urlsplit(href)
                if url.scheme not in ('http', 'https'):
                    continue
                if url.hostname in ('davidportodiaz.com', 'www.davidportodiaz.com'):
                    continue
                external.append(link)
                with self.subTest(page=page, href=href):
                    self.assertEqual(url.scheme, 'https', f'{page}: destino externo inseguro {href}')
                    self.assertFalse(url.username or url.password, f'{page}: credenciales en URL externa {href}')
                    if link.get('target', '').lower() == '_blank':
                        rel = set((link.get('rel') or '').lower().split())
                        self.assertTrue({'noopener', 'noreferrer'} <= rel, f'{page}: enlace externo sin aislamiento {href}; rel={rel}')
            self.assertTrue(external, f'{page}: no se encontraron enlaces externos; prueba vacía')

if __name__ == '__main__':
    unittest.main()