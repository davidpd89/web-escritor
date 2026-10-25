import json
import pathlib
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = ['fragmento/index.html', 'las-manecillas-del-recuerdo/fragmentos/index.html']

class Extract(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.blocks = []
        self.active = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical.append(attrs.get('href'))
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.active = True
            self.blocks.append('')
    def handle_data(self, data):
        if self.active:
            self.blocks[-1] += data
    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False

class FragmentSchema(unittest.TestCase):
    def test_identity(self):
        for name in PAGES:
            with self.subTest(page=name):
                parser = Extract()
                parser.feed((ROOT / name).read_text(encoding='utf-8'))
                self.assertEqual(len(parser.canonical), 1)
                self.assertTrue(parser.blocks)
                nodes = []
                for block in parser.blocks:
                    data = json.loads(block)
                    nodes.extend(data.get('@graph', [data]))
                pages = [node for node in nodes if node.get('@type') == 'WebPage']
                self.assertEqual(len(pages), 1)
                self.assertEqual(pages[0]['url'], parser.canonical[0])
                self.assertTrue(pages[0]['url'].startswith('https://davidportodiaz.com/'))
                self.assertEqual(pages[0].get('inLanguage'), 'es')

if __name__ == '__main__':
    unittest.main()