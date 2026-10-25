import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Structure(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1 = 0
        self.main = 0
        self.links = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == 'h1':
            self.h1 += 1
        if tag == 'main':
            self.main += 1
        if tag == 'a':
            self.current = {'href': data.get('href'), 'label': data.get('aria-label', ''), 'text': ''}
    def handle_data(self, data):
        if self.current is not None:
            self.current['text'] += data
    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(self.current)
            self.current = None

class ReadingAccessibility(unittest.TestCase):
    def test_published_book_structure(self):
        books = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']
        for book in books:
            if book.get('estado') != 'publicado':
                continue
            with self.subTest(book=book['slug']):
                file = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
                parser = Structure()
                parser.feed(file.read_text(encoding='utf-8'))
                self.assertEqual(parser.h1, 1)
                self.assertEqual(parser.main, 1)
                self.assertTrue(parser.links)
                for link in parser.links:
                    self.assertTrue(link['href'])
                    self.assertTrue(link['label'].strip() or link['text'].strip())

if __name__ == '__main__':
    unittest.main()