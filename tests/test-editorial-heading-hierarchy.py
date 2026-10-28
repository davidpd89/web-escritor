import pathlib
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = ['cuaderno/index.html', 'cuaderno/que-es-el-portal-fantasy/index.html', 'fragmento/index.html', 'las-manecillas-del-recuerdo/index.html', 'las-manecillas-del-recuerdo/fragmentos/index.html']

class Headings(HTMLParser):
    def __init__(self):
        super().__init__()
        self.levels = []
        self.main_levels = []
        self.main_count = 0
        self.in_main = False
        self.hidden = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.main_count += 1
            self.in_main = True
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            attrs = dict(attrs)
            self.current = int(tag[1])
            self.levels.append(self.current)
            if self.in_main:
                self.main_levels.append(self.current)
            if self.current == 1:
                self.hidden.append(attrs.get('hidden') is not None or attrs.get('aria-hidden') == 'true')
    def handle_endtag(self, tag):
        if tag == 'main':
            self.in_main = False
        if tag.startswith('h') and len(tag) == 2 and tag[1].isdigit():
            self.current = None

class HeadingHierarchy(unittest.TestCase):
    def test_heading_structure(self):
        for name in PAGES:
            with self.subTest(page=name):
                parser = Headings()
                parser.feed((ROOT / name).read_text(encoding='utf-8'))
                self.assertEqual(parser.levels.count(1), 1)
                self.assertEqual(parser.main_count, 1, f'{name}: debe existir un único main')
                self.assertTrue(parser.main_levels, f'{name}: main no contiene encabezados')
                self.assertEqual(parser.main_levels[0], 1, f'{name}: main debe comenzar con H1')
                self.assertEqual(parser.hidden, [False])
                for before, after in zip(parser.main_levels, parser.main_levels[1:]):
                    self.assertLessEqual(after - before, 1, f'{name}: H{before} -> H{after}')

if __name__ == '__main__':
    unittest.main()