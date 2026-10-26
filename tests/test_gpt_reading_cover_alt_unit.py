import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_cover_builder', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class Images(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs))

class CoverAltTests(unittest.TestCase):
    def test_published_covers_identify_title_and_edition(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = builder.validate(data, ROOT)
        self.assertTrue(books, 'Catálogo: no se encontraron libros válidos')
        for book in books:
            with self.subTest(book=book['id']):
                parser = Images()
                parser.feed(builder.image(book))
                self.assertEqual(len(parser.images), 1, book['id'])
                alt = parser.images[0].get('alt', '')
                self.assertIn(book['titulo'], alt, book['id'] + ': falta título en alt')
                self.assertIn(book['edicion'], alt, book['id'] + ': falta edición en alt')
                self.assertTrue(alt.startswith('Portada de '), book['id'] + ': alt no identifica la portada')

if __name__ == '__main__':
    unittest.main()
