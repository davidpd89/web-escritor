"""Si Amazon clasifica un ASIN con otro formato que el guardado, el precio no se publica y se informa."""
import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_amazon_market import select_offers  # noqa: E402

ASIN = 'B08CYCPBZN'
TAG = 'davidporto-21'
NOW = datetime(2026, 11, 4, tzinfo=timezone.utc)
BOOK = {'id': 'lib-test', 'titulo': 'Coraline', 'autores': ['Neil Gaiman'], 'isbn13': '9788498382372',
        'estado': 'publicado',
        'formatos_compra': [{'url': f'https://www.amazon.es/dp/{ASIN}?tag={TAG}', 'formato': 'tapa-blanda'}]}
ITEM = {'asin': ASIN,
        'itemInfo': {'title': {'displayValue': 'Coraline'},
                     'byLineInfo': {'contributors': [{'name': 'Neil Gaiman', 'role': 'Author'}]},
                     'externalIds': {}, 'classifications': {'binding': {'displayValue': 'Tapa dura'}}},
        'offersV2': {'listings': [{'condition': {'value': 'New'}, 'availability': {'type': 'IN_STOCK'},
                                   'price': {'money': {'amount': 21.75, 'currency': 'EUR'}}}]}}


def run(binding):
    item = copy.deepcopy(ITEM)
    item['itemInfo']['classifications']['binding']['displayValue'] = binding
    found = []
    return select_offers(BOOK, {'searchResult': {'items': [item]}}, TAG, NOW, found), found


class AmazonFormatMismatch(unittest.TestCase):
    def test_conflicting_binding_is_skipped_and_reported(self):
        offers, found = run('Tapa dura')
        self.assertEqual(offers, [])
        self.assertEqual(found, [{'libro_id': 'lib-test', 'asin': ASIN, 'guardado': 'tapa-blanda', 'amazon': 'tapa-dura'}])

    def test_matching_or_unknown_binding_keeps_the_offer(self):
        for binding in ('Tapa blanda', 'Libro de bolsillo', 'Rústica', ''):
            with self.subTest(binding=binding):
                offers, found = run(binding)
                self.assertEqual([o['formato'] for o in offers], ['tapa-blanda'])
                self.assertEqual(found, [])

    def test_default_call_still_works(self):
        item = copy.deepcopy(ITEM)
        self.assertEqual(select_offers(BOOK, {'searchResult': {'items': [item]}}, TAG, NOW), [])


if __name__ == '__main__':
    unittest.main()
