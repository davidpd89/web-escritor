import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def priced():
    """Amazon prices now live per format in the catalogue (formatos_compra)."""
    catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    return [(book, option) for book in catalogue['libros']
            for option in book.get('formatos_compra', []) if 'precio_centimos' in option]


class MarketCatalogueReferences(unittest.TestCase):
    def test_prices_belong_to_published_books(self):
        market = json.loads((ROOT / 'assets/reading-market.json').read_text(encoding='utf-8'))
        self.assertEqual(market['offers'], [], 'reading-market.json: los precios se guardan en el catálogo')
        self.assertTrue(priced(), 'reading-catalogue.json: no hay precios publicados')
        for book, option in priced():
            with self.subTest(book=book['id'], format=option['formato']):
                self.assertEqual(book['estado'], 'publicado', f'{book["id"]}: precio para un libro en estado {book["estado"]!r}')
                self.assertTrue(book.get('precios_amazon_revision'), f'{book["id"]}: precio sin fecha de revisión')

if __name__ == '__main__':
    unittest.main()
