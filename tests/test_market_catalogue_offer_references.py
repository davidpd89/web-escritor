import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class MarketCatalogueReferences(unittest.TestCase):
    def test_offers_reference_published_books(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        market = json.loads((ROOT / 'assets/reading-market.json').read_text(encoding='utf-8'))
        books = catalogue['libros']
        counts = Counter(book['id'] for book in books)
        by_id = {book['id']: book for book in books}
        self.assertTrue(market['offers'], 'reading-market.json: no hay ofertas publicadas')
        for offer in market['offers']:
            book_id = offer['libro_id']
            with self.subTest(book=book_id):
                self.assertEqual(counts[book_id], 1, f'reading-market.json: oferta {book_id} sin libro único en reading-catalogue.json')
                if counts[book_id] == 1:
                    self.assertEqual(by_id[book_id]['estado'], 'publicado', f'{book_id}: precio publicado para un libro en estado {by_id[book_id]["estado"]!r}')

if __name__ == '__main__':
    unittest.main()
