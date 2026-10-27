import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('eventos.html', 'ferias.html')

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'a':
            if a.get('name'):
                self.ids.add(a['name'])
            if a.get('href'):
                self.hrefs.append(a['href'])

class FragmentContract(unittest.TestCase):
    def test_cross_page_and_self_fragments(self):
        pages = {}
        for name in PAGES:
            parser = Links()
            parser.feed((ROOT / name).read_text(encoding='utf-8'))
            pages[name] = parser
        checked = 0
        for source, document in pages.items():
            for href in document.hrefs:
                url = urlsplit(href)
                if not url.fragment or url.scheme or url.netloc:
                    continue
                target = url.path.lstrip('/') or source
                if target not in pages:
                    continue
                fragment = unquote(url.fragment)
                self.assertIn(fragment, pages[target].ids,
                    f'{source}: enlace {href!r} apunta a un fragmento inexistente en {target}')
                checked += 1
        self.assertGreater(checked, 0, 'eventos.html y ferias.html: no se verificó ningún enlace con fragmento')

if __name__ == '__main__':
    unittest.main()
