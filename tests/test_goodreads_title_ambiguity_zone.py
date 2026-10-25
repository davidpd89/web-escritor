import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_goodreads import select_goodreads_rating

BOOK = {'id': 'lib-1', 'isbn13': '9788498382372', 'titulo': 'Coraline', 'autores': ['Neil Gaiman']}
URL = 'https://www.goodreads.com/book/show/123-coraline'

class TitleAmbiguity(unittest.TestCase):
    def rate(self, title):
        item = {'isbn': BOOK['isbn13'], 'name': title, 'author': [{'name': 'Neil Gaiman'}], 'aggregateRating': {'ratingValue': 4.2, 'ratingCount': 100}}
        return select_goodreads_rating(BOOK, {'books': [item], 'url': URL})

    def test_unrelated_prefixed_titles_are_rejected(self):
        for title in ('Coraline II', 'Coraline y otra historia', 'Coraline: novela diferente'):
            with self.subTest(title=title):
                self.assertIsNone(self.rate(title), 'Título potencialmente distinto aceptado: ' + title)

    def test_exact_title_is_accepted(self):
        self.assertIsNotNone(self.rate('Coraline'))

if __name__ == '__main__':
    unittest.main()
