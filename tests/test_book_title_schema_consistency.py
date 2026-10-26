import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class JSONLD(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reading = False
        self.parts = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.reading = True
            self.parts = []

    def handle_data(self, value):
        if self.reading:
            self.parts.append(value)

    def handle_endtag(self, tag):
        if tag == 'script' and self.reading:
            document = json.loads(''.join(self.parts))
            self.items.extend(document.get('@graph', [document]))
            self.reading = False

class BookTitleConsistency(unittest.TestCase):
    def test_published_titles_match_schema(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        count = 0
        for book in catalogue['libros']:
            if book['estado'] != 'publicado':
                continue
            page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
            with self.subTest(page=str(page)):
                self.assertTrue(page.is_file(), f'{page}: ficha inexistente')
                parser = JSONLD()
                parser.feed(page.read_text(encoding='utf-8'))
                entities = [item for item in parser.items if item.get('@type') == 'Book']
                self.assertEqual(len(entities), 1, f'{page}: entidad Book ausente o duplicada')
                self.assertEqual(entities[0].get('name'), book['titulo'], f'{page}: título publicado distinto de {book["titulo"]!r}')
                count += 1
        self.assertGreater(count, 0, 'No se revisaron fichas publicadas')

if __name__ == '__main__':
    unittest.main()
