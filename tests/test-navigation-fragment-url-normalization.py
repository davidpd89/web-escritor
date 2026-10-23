import unittest
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://davidportodiaz.com'
PAGES = ['index.html', 'autor.html', 'mapa-del-sitio/index.html', 'las-manecillas-del-recuerdo/fragmentos/index.html']


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a':
            if attrs.get('name'):
                self.ids.add(attrs['name'])
            if attrs.get('href'):
                self.hrefs.append(attrs['href'])


@lru_cache(None)
def parsed(file):
    if not file.is_file():
        return None
    parser = Links()
    parser.feed(file.read_text(encoding='utf-8'))
    return parser


def filename(path):
    relative = unquote(path).lstrip('/')
    target = ROOT / relative
    if path.endswith('/'):
        return target / 'index.html'
    if target.suffix:
        return target
    return target / 'index.html'


class NormalizedFragments(unittest.TestCase):
    def test_real_internal_fragment_links(self):
        checked = 0
        for source in PAGES:
            page = ROOT / source
            origin = '/' + source.removesuffix('index.html') if source.endswith('index.html') else '/' + source
            for href in parsed(page).hrefs:
                target = urlsplit(urljoin(BASE + origin, href))
                if target.netloc not in ('davidportodiaz.com', 'www.davidportodiaz.com') or not target.fragment:
                    continue
                with self.subTest(source=source, href=href):
                    dest = parsed(filename(target.path))
                    self.assertIsNotNone(dest, href)
                    self.assertIn(unquote(target.fragment), dest.ids, href)
                    checked += 1
        self.assertGreaterEqual(checked, 15)

    def test_url_normalization_examples(self):
        self.assertEqual(urlsplit(urljoin(BASE + '/libros/', '../autor.html?origen=libros#contacto')).path, '/autor.html')
        self.assertEqual(unquote('fragmento%2D1'), 'fragmento-1')


if __name__ == '__main__':
    unittest.main()