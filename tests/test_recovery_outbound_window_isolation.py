import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com/'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))

class OutboundIsolation(unittest.TestCase):
    def test_external_new_tabs(self):
        parser = Links()
        parser.feed((ROOT / '404.html').read_text(encoding='utf-8'))
        external = []
        for a in parser.links:
            href = a.get('href', '')
            url = urlparse(urljoin(ORIGIN, href))
            if url.scheme not in ('http', 'https') or url.netloc == urlparse(ORIGIN).netloc:
                continue
            external.append(a)
            if a.get('target', '').lower() != '_blank':
                continue
            rel = set(a.get('rel', '').lower().split())
            self.assertTrue({'noopener', 'noreferrer'} & rel, f'404.html: enlace externo {href} abre pestaña sin aislamiento; rel={rel}')
        self.assertTrue(external, '404.html: no se encontraron enlaces externos reales para comprobar')

if __name__ == '__main__':
    unittest.main()