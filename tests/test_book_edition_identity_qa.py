import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


class BookEditionIdentityQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.facts = json.loads((ROOT / 'editorial-facts.json').read_text(encoding='utf-8'))

    def test_identifiers_and_canonical_retailers(self):
        for key, book in self.facts['books'].items():
            with self.subTest(book=key):
                isbn = book.get('isbn')
                self.assertTrue(isbn)
                self.assertEqual(len(isbn.replace('-', '')), 13)
                self.assertTrue(isbn.replace('-', '').isdigit())
                for field in ('purchaseUrl', 'canonicalRetailerUrl'):
                    if field in book:
                        parsed = urlparse(book[field])
                        self.assertEqual(parsed.scheme, 'https')
                        self.assertTrue(parsed.hostname)
                        self.assertFalse(parsed.username)
                        self.assertFalse(parsed.password)

    def test_distinct_kindle_edition(self):
        for key, book in self.facts['books'].items():
            kindle = book.get('kindleEdition')
            if not kindle:
                continue
            with self.subTest(book=key):
                self.assertEqual(kindle['format'], 'EBook')
                self.assertNotEqual(book['isbn'].replace('-', ''), kindle['isbn13'].replace('-', ''))
                self.assertNotEqual(book['canonicalRetailerUrl'], kindle['canonicalRetailerUrl'])
                self.assertNotEqual(book['purchaseUrl'], kindle['purchaseUrl'])
                self.assertGreater(book['numberOfPages'], 0)
                self.assertGreater(kindle['printLengthPages'], 0)
                for edition in (book, kindle):
                    self.assertIs(type(edition['priceEUR']), float)
                    self.assertGreater(edition['priceEUR'], 0)
                    self.assertEqual(urlparse(edition['canonicalRetailerUrl']).scheme, 'https')
                self.assertIn(kindle['asin'], kindle['canonicalRetailerUrl'])


if __name__ == '__main__':
    unittest.main()
