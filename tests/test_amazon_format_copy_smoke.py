import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_amazon_market import asin_from_url

FORMATS = {'tapa-blanda', 'tapa-dura', 'ebook', 'audiolibro'}

class AmazonFormatCopySmoke(unittest.TestCase):
    def test_published_purchase_formats_are_distinct_and_recognisable(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        checked = 0
        for book in catalogue['libros']:
            if book.get('estado') != 'publicado':
                continue
            formats = book.get('formatos_compra', [])
            if not formats:
                continue
            seen = set()
            for entry in formats:
                checked += 1
                fmt = entry.get('formato')
                context = f"data/reading-catalogue.json libro={book['id']} formato={fmt!r}"
                self.assertIn(fmt, FORMATS, f'{context}: denominación comercial no reconocida')
                self.assertNotIn(fmt, seen, f'{context}: opción comercial duplicada')
                seen.add(fmt)
                url = entry.get('url')
                self.assertIsInstance(url, str, f'{context}: destino ausente')
                self.assertIsNotNone(asin_from_url(url), f'{context}: el formato anunciado no tiene destino Amazon reconocible: {url!r}')
        self.assertGreater(checked, 0, 'data/reading-catalogue.json: no se comprobaron formatos comerciales publicados')

if __name__ == '__main__':
    unittest.main()
