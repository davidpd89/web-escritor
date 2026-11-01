import json
from datetime import date
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def priced():
    """Amazon prices now live per format in the catalogue (formatos_compra)."""
    catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    return [(book, option) for book in catalogue['libros']
            for option in book.get('formatos_compra', []) if 'precio_centimos' in option]


class PublishedOfferChronology(unittest.TestCase):
    def test_price_dates(self):
        # Prices do not expire: they stay until the nightly sweep brings a newer one.
        self.assertTrue(priced(), 'reading-catalogue.json: no hay fechas de precio que comprobar')
        today = date.today()
        for book, option in priced():
            label = f'{book["id"]}/{option["formato"]}'
            with self.subTest(price=label):
                checked = date.fromisoformat(option['fecha_verificacion'])
                revision = date.fromisoformat(book['precios_amazon_revision'])
                self.assertLessEqual(checked, revision, f'{label}: precio posterior a la última revisión')
                self.assertLessEqual(revision, today, f'{label}: revisión en el futuro')
                self.assertIsInstance(option['precio_centimos'], int, f'{label}: precio no entero')
                self.assertGreaterEqual(option['precio_centimos'], 100, f'{label}: precio sospechoso')

if __name__ == '__main__':
    unittest.main()
