import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class BookEntities(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.buffer = []
        self.books = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.active = True
            self.buffer = []

    def handle_data(self, text):
        if self.active:
            self.buffer.append(text)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            document = json.loads(''.join(self.buffer))
            self.books.extend(e for e in document.get('@graph', [document]) if e.get('@type') == 'Book')
            self.active = False

class PublishedAuthorParity(unittest.TestCase):
    def test_authors_match_master_catalogue(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        checked = 0
        for book in data['libros']:
            if book['estado'] != 'publicado':
                continue
            page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
            with self.subTest(page=str(page)):
                self.assertTrue(page.is_file(), f'{page}: falta ficha')
                parser = BookEntities()
                parser.feed(page.read_text(encoding='utf-8'))
                self.assertEqual(len(parser.books), 1, f'{page}: entidad Book ausente o duplicada')
                raw = parser.books[0].get('author', [])
                if isinstance(raw, dict):
                    raw = [raw]
                actual = [a.get('name') if isinstance(a, dict) else a for a in raw]
                expected = book['autores']
                self.assertCountEqual(actual, expected, f'{page}: autores {actual!r} distintos de {expected!r}')
                checked += 1
        self.assertGreater(checked, 0, 'No se revisó ninguna autoría')

if __name__ == '__main__':
    unittest.main()
