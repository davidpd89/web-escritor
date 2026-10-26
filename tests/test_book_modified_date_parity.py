import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Schemas(HTMLParser):
    def __init__(self):
        super().__init__()
        self.capture = False
        self.parts = []
        self.entities = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.capture = True
            self.parts = []

    def handle_data(self, text):
        if self.capture:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if tag == 'script' and self.capture:
            document = json.loads(''.join(self.parts))
            self.entities.extend(document.get('@graph', [document]))
            self.capture = False

class ModifiedDateParity(unittest.TestCase):
    def test_dates_match_published_pages(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        checked = 0
        for book in data['libros']:
            if book['estado'] != 'publicado':
                continue
            page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
            with self.subTest(page=str(page)):
                self.assertTrue(page.is_file(), f'{page}: falta HTML')
                parser = Schemas()
                parser.feed(page.read_text(encoding='utf-8'))
                pages = [e for e in parser.entities if e.get('@type') == 'WebPage']
                self.assertEqual(len(pages), 1, f'{page}: WebPage ausente o duplicado')
                expected = book['fecha_actualizacion']
                self.assertEqual(pages[0].get('dateModified'), expected, f'{page}: dateModified no coincide con {expected}')
                checked += 1
        self.assertGreater(checked, 0, 'No se comprobaron fechas')

if __name__ == '__main__':
    unittest.main()
