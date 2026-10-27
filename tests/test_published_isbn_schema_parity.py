import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class StructuredData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []
        self.documents = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.active = True
            self.parts = []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.documents.append(json.loads(''.join(self.parts)))
            self.active = False

def books_in_schema(page):
    parser = StructuredData()
    parser.feed(page.read_text(encoding='utf-8'))
    for document in parser.documents:
        for entity in document.get('@graph', [document]):
            if entity.get('@type') == 'Book':
                yield entity

class PublishedISBNParity(unittest.TestCase):
    def test_isbn_matches_published_book(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        checked = 0
        for book in data['libros']:
            if book['estado'] != 'publicado' or not book.get('isbn13'):
                continue
            page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
            with self.subTest(page=str(page)):
                self.assertTrue(page.is_file(), f'{page}: falta la ficha publicada')
                entities = list(books_in_schema(page))
                self.assertEqual(len(entities), 1, f'{page}: se esperaba una entidad Book')
                self.assertEqual(entities[0].get('isbn'), book['isbn13'], f'{page}: ISBN distinto del catálogo: {book["isbn13"]}')
                checked += 1
        self.assertGreater(checked, 0, 'No se verificó ningún ISBN publicado')

if __name__ == '__main__':
    unittest.main()
