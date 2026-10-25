import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class JsonScripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.collect = False
        self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.collect = True
            self.blocks.append('')
    def handle_data(self, data):
        if self.collect:
            self.blocks[-1] += data
    def handle_endtag(self, tag):
        if tag == 'script':
            self.collect = False

class AuthorBookParityTests(unittest.TestCase):
    def test_book_destinations(self):
        parser = JsonScripts()
        parser.feed((ROOT / 'libros/index.html').read_text(encoding='utf-8'))
        nodes = []
        for block in parser.blocks:
            obj = json.loads(block)
            nodes.extend(obj.get('@graph', [obj]))
        lists = [node for node in nodes if node.get('@type') == 'ItemList']
        self.assertTrue(lists)
        books = [entry['item'] for node in lists for entry in node.get('itemListElement', []) if entry.get('item', {}).get('@type') == 'Book']
        self.assertGreaterEqual(len(books), 2)
        for book in books:
            with self.subTest(book=book['name']):
                url = urlsplit(book['url'])
                self.assertEqual(url.scheme, 'https')
                self.assertEqual(url.hostname, 'davidportodiaz.com')
                self.assertFalse(url.query or url.fragment)
                target = (ROOT / unquote(url.path).lstrip('/') / 'index.html').resolve()
                self.assertTrue(target.is_relative_to(ROOT.resolve()))
                self.assertTrue(target.is_file(), str(target))

if __name__ == '__main__':
    unittest.main()