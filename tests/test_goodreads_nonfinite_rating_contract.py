import copy
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_goodreads import select_goodreads_rating

BOOK = {'id': 'x', 'titulo': 'Coraline', 'autores': ['Neil Gaiman'], 'isbn13': '9788498382372'}
BASE = {'url': 'https://www.goodreads.com/book/show/123-coraline', 'books': [{'@type': 'Book', 'isbn': '9788498382372', 'name': 'Coraline', 'author': [{'name': 'Neil Gaiman'}], 'aggregateRating': {'ratingValue': '4.1', 'ratingCount': '300'}}]}

class GoodreadsNumericBoundaryTests(unittest.TestCase):
    def test_invalid_vote_counts(self):
        for value in ('inf', '-inf', 'nan', '1e309', float('inf'), float('nan'), -5, True, '3.5'):
            with self.subTest(value=str(value)):
                response = copy.deepcopy(BASE)
                response['books'][0]['aggregateRating']['ratingCount'] = value
                self.assertIsNone(select_goodreads_rating(BOOK, response))

    def test_invalid_score_values(self):
        for value in ('inf', '-inf', 'nan', '1e309', float('nan'), float('inf'), 0, 5.01, True):
            with self.subTest(value=str(value)):
                response = copy.deepcopy(BASE)
                response['books'][0]['aggregateRating']['ratingValue'] = value
                self.assertIsNone(select_goodreads_rating(BOOK, response))

if __name__ == '__main__':
    unittest.main()
