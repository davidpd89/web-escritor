import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.chunks = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.active = dict(attrs).get('type') == 'application/ld+json'
            self.chunks = []

    def handle_data(self, data):
        if self.active:
            self.chunks.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.blocks.append(json.loads(''.join(self.chunks)))
            self.active = False

def books(value):
    if isinstance(value, list):
        for item in value:
            yield from books(item)
    elif isinstance(value, dict):
        kind = value.get('@type', [])
        if kind == 'Book' or isinstance(kind, list) and 'Book' in kind:
            yield value
        for child in value.values():
            yield from books(child)

def normalized(value):
    return re.sub(r'[^0-9]', '', str(value))

class TestISBNParity(unittest.TestCase):
    def test_primary_editions(self):
        cases = [
            ('libros/samuel-entre-mundos/index.html', '9791387659776'),
            ('las-manecillas-del-recuerdo/index.html', '9798905149351'),
        ]
        catalogue = (ROOT / 'libros/index.html').read_text(encoding='utf-8')
        for path, isbn in cases:
            with self.subTest(page=path):
                html = (ROOT / path).read_text(encoding='utf-8')
                parser = Scripts()
                parser.feed(html)
                values = [normalized(b['isbn']) for block in parser.blocks for b in books(block) if b.get('isbn')]
                self.assertIn(isbn, values, f'{path}: ISBN {isbn} ausente del Book JSON-LD')
                self.assertIn(isbn, normalized(html), f'{path}: ISBN {isbn} ausente de la ficha')
                self.assertIn(isbn, normalized(catalogue), f'libros/index.html: ISBN {isbn} ausente del catálogo')

if __name__ == '__main__':
    unittest.main()