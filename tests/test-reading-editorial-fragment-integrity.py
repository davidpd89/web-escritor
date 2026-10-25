import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ('lecturas', 'libros', 'recomendaciones', 'editoriales')
ORIGIN = 'https://davidportodiaz.com'

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])

class FragmentTests(unittest.TestCase):
    def test_local_fragments_resolve(self):
        pages = [p for family in FAMILIES for p in (ROOT / family).rglob('*.html')]
        self.assertTrue(pages)
        cache = {}
        checked = 0
        for source in pages:
            parser = Links()
            parser.feed(source.read_text(encoding='utf-8'))
            source_url = ORIGIN + '/' + source.relative_to(ROOT).as_posix().removesuffix('index.html')
            for href in parser.links:
                target_url = urlsplit(urljoin(source_url, href))
                if target_url.hostname != 'davidportodiaz.com' or not target_url.fragment:
                    continue
                relative = unquote(target_url.path).lstrip('/')
                destination = ROOT / relative
                if destination.suffix != '.html':
                    destination /= 'index.html'
                destination = destination.resolve()
                if not destination.is_relative_to(ROOT.resolve()) or not destination.is_file():
                    continue
                if destination not in cache:
                    target_parser = Links()
                    target_parser.feed(destination.read_text(encoding='utf-8'))
                    cache[destination] = target_parser.ids
                checked += 1
                with self.subTest(source=str(source.relative_to(ROOT)), href=href):
                    self.assertIn(unquote(target_url.fragment), cache[destination])
        self.assertGreater(checked, 0)

if __name__ == '__main__':
    unittest.main()