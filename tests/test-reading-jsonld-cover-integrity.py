import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.active = dict(attrs).get('type') == 'application/ld+json'
    def handle_data(self, data):
        if self.active:
            self.blocks.append(data)
    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False

class CoverIntegrityTests(unittest.TestCase):
    def test_itemlist_covers_exist(self):
        parser = Scripts()
        parser.feed((ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8'))
        lists = [json.loads(block) for block in parser.blocks]
        lists = [obj for obj in lists if obj.get('@type') == 'ItemList']
        self.assertEqual(len(lists), 1)
        items = lists[0]['itemListElement']
        self.assertGreater(len(items), 0)
        for entry in items:
            book = entry['item']
            image = book['image']
            parsed = urlsplit(image)
            with self.subTest(book=book.get('name')):
                self.assertEqual(parsed.scheme, 'https')
                self.assertEqual(parsed.hostname, 'davidportodiaz.com')
                self.assertFalse(parsed.query or parsed.fragment)
                target = (ROOT / unquote(parsed.path).lstrip('/')).resolve()
                self.assertTrue(target.is_relative_to(ROOT.resolve()))
                self.assertTrue(target.is_file(), str(target))
                self.assertGreater(target.stat().st_size, 0)

if __name__ == '__main__':
    unittest.main()