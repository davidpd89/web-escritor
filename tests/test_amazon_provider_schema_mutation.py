import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_amazon_market import select_offers

BOOK = {'id': 'x', 'titulo': 'Coraline', 'autores': ['Neil Gaiman'], 'isbn13': '9788498382372'}
NOW = datetime(2026, 10, 21, tzinfo=timezone.utc)

class ProviderSchemaMutationTests(unittest.TestCase):
    def test_invalid_item_shapes_are_ignored(self):
        cases = [
            {'searchResult': {'items': [None]}},
            {'searchResult': {'items': ['texto']}},
            {'searchResult': {'items': [{'asin': '8498382378', 'itemInfo': []}]}},
            {'searchResult': {'items': [{'asin': '8498382378', 'itemInfo': {'title': []}}]}},
            {'searchResult': {'items': [{'asin': '8498382378', 'itemInfo': {'title': {'displayValue': 'Coraline'}, 'byLineInfo': {'contributors': None}}}]}},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                self.assertEqual(select_offers(BOOK, payload, 'contrato-21', NOW), [])

if __name__ == '__main__':
    unittest.main()
