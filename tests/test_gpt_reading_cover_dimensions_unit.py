import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_dimensions_builder', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs))

class DimensionsTests(unittest.TestCase):
    def test_dimensions_and_loading_for_real_books(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = builder.validate(data, ROOT)
        self.assertTrue(books, 'Catálogo sin libros')
        for book in books:
            for lazy in (False, True):
                with self.subTest(book=book['id'], lazy=lazy):
                    parser = ImageParser()
                    parser.feed(builder.image(book, lazy=lazy))
                    self.assertEqual(len(parser.images), 1, book['id'])
                    img = parser.images[0]
                    self.assertEqual(int(img['width']), book['portada_ancho'], book['id'])
                    self.assertEqual(int(img['height']), book['portada_alto'], book['id'])
                    self.assertGreater(int(img['width']), 0, book['id'])
                    self.assertGreater(int(img['height']), 0, book['id'])
                    self.assertEqual(img['src'], book['portada_local'], book['id'])
                    if lazy:
                        self.assertEqual(img.get('loading'), 'lazy', book['id'])
                    else:
                        self.assertEqual(img.get('fetchpriority'), 'high', book['id'])

if __name__ == '__main__':
    unittest.main()
