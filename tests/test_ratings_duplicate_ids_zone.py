import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_ratings_refresh import refresh

class DuplicateBookIdentifiers(unittest.TestCase):
    def test_duplicate_ids_with_different_isbn_are_rejected(self):
        books = [
            {'id': 'lib-1', 'estado': 'publicado', 'isbn13': '9788498382372', 'titulo': 'Coraline', 'autores': ['Neil Gaiman']},
            {'id': 'lib-1', 'estado': 'publicado', 'isbn13': '9788425374012', 'titulo': 'Otro libro', 'autores': ['Otra autora']}
        ]
        calls = []
        def provider(isbn):
            calls.append(isbn)
            return {'books': []}
        with self.assertRaises(ValueError):
            refresh({'libros': books}, {'ratings': [], 'offers': []}, provider, now=datetime(2026, 10, 25, tzinfo=timezone.utc), budget=10, source='goodreads')
        self.assertEqual(calls, [])

if __name__ == '__main__':
    unittest.main()
