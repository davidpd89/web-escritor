import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_goodreads import select_goodreads_rating

BOOK = {'id': 'lib-1', 'isbn13': '9788498382372', 'titulo': 'Coraline', 'autores': ['Neil Gaiman']}
URL = 'https://www.goodreads.com/book/show/123-coraline'

class ResponseContainerTypes(unittest.TestCase):
    def test_malformed_book_collections_are_rejected_safely(self):
        for books in (None, {}, 123, True, 'Coraline', {'isbn': BOOK['isbn13']}):
            with self.subTest(books=repr(books)):
                self.assertIsNone(select_goodreads_rating(BOOK, {'books': books, 'url': URL}))

    def test_empty_list_is_a_valid_unrated_response(self):
        self.assertIsNone(select_goodreads_rating(BOOK, {'books': [], 'url': URL}))

if __name__ == '__main__':
    unittest.main()
