import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_goodreads import select_goodreads_rating

BOOK = {'id': 'lib-1', 'isbn13': '9788498382372', 'titulo': 'Coraline', 'autores': ['Neil Gaiman']}
ITEM = {'isbn': '9788498382372', 'name': 'Coraline', 'author': [{'name': 'Neil Gaiman'}], 'aggregateRating': {'ratingValue': 4.2, 'ratingCount': 100}}
URL = 'https://www.goodreads.com/book/show/123-coraline'

class NonfiniteRatings(unittest.TestCase):
    def test_nonfinite_values_are_rejected(self):
        for field in ('ratingValue', 'ratingCount'):
            for value in ('NaN', 'Infinity', '-Infinity', float('nan'), float('inf'), float('-inf')):
                with self.subTest(field=field, value=str(value)):
                    item = copy.deepcopy(ITEM)
                    item['aggregateRating'][field] = value
                    self.assertIsNone(select_goodreads_rating(BOOK, {'books': [item], 'url': URL}))

    def test_finite_reference_is_accepted(self):
        self.assertIsNotNone(select_goodreads_rating(BOOK, {'books': [ITEM], 'url': URL}))

if __name__ == '__main__':
    unittest.main()
