import json
from collections import Counter
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def priced():
    """Amazon prices now live per format in the catalogue (formatos_compra)."""
    catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    return [(book, option) for book in catalogue['libros']
            for option in book.get('formatos_compra', []) if 'precio_centimos' in option]


class MarketFormatUniqueness(unittest.TestCase):
    def test_one_price_per_book_and_format(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        self.assertTrue(priced(), 'reading-catalogue.json: no hay formatos con precio que comprobar')
        for book in catalogue['libros']:
            counts = Counter(o['formato'] for o in book.get('formatos_compra', []))
            for fmt, n in counts.items():
                self.assertEqual(n, 1, f'{book["id"]}, formato {fmt}: {n} entradas contradictorias')

if __name__ == '__main__':
    unittest.main()
