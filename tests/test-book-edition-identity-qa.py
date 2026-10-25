import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def isbn13_valid(value):
    digits = ''.join(c for c in value if c.isdigit())
    if len(digits) != 13:
        return False
    total = sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(digits[:12]))
    return (10 - total % 10) % 10 == int(digits[-1])


class BookEditionIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.books = json.loads((ROOT / 'editorial-facts.json').read_text(encoding='utf-8'))['books']

    def test_independent_editions(self):
        book = self.books['lasManecillasDelRecuerdo']
        kindle = book['kindleEdition']
        self.assertTrue(isbn13_valid(book['isbn']))
        self.assertTrue(isbn13_valid(kindle['isbn13']))
        self.assertNotEqual(''.join(filter(str.isdigit, book['isbn'])), kindle['isbn13'])
        self.assertNotEqual(book['canonicalRetailerUrl'], kindle['canonicalRetailerUrl'])
        self.assertNotEqual(book['purchaseUrl'], kindle['purchaseUrl'])
        self.assertEqual(book['format'], 'Paperback')
        self.assertEqual(kindle['format'], 'EBook')
        self.assertNotEqual(book['numberOfPages'], kindle['printLengthPages'])

    def test_commercial_urls(self):
        for book in self.books.values():
            urls = []
            for key in ('purchaseUrl', 'canonicalRetailerUrl', 'sourceUrl'):
                if book.get(key):
                    urls.append(book[key])
            urls.extend(book.get('purchaseUrls', {}).values())
            if 'kindleEdition' in book:
                urls.extend(book['kindleEdition'][key] for key in ('purchaseUrl', 'canonicalRetailerUrl', 'sourceUrl'))
            for url in urls:
                with self.subTest(url=url):
                    parsed = urlsplit(url)
                    self.assertEqual(parsed.scheme, 'https')
                    self.assertTrue(parsed.hostname)
                    self.assertFalse(parsed.username)
                    self.assertFalse(parsed.password)


if __name__ == '__main__':
    unittest.main()