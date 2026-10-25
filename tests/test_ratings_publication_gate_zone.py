import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_ratings_refresh import refresh

class PublicationGate(unittest.TestCase):
    def test_ready_book_is_not_queried(self):
        book = {'id': 'lib-1', 'estado': 'listo', 'isbn13': '9788498382372', 'titulo': 'Coraline', 'autores': ['Neil Gaiman']}
        calls = []
        def provider(isbn):
            calls.append(isbn)
            return {'items': []}
        result, stats = refresh({'libros': [book]}, {'ratings': [], 'offers': []}, provider, now=datetime(2026, 10, 25, tzinfo=timezone.utc), budget=10)
        self.assertEqual(calls, [])
        self.assertEqual(stats['attempted'], 0)
        self.assertEqual(result['ratings'], [])

if __name__ == '__main__':
    unittest.main()
