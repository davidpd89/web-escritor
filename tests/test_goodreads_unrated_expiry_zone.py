import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_ratings_refresh import refresh

class UnratedExpiry(unittest.TestCase):
    def test_successful_empty_response_does_not_keep_expired_rating(self):
        book = {'id': 'lib-1', 'estado': 'publicado', 'isbn13': '9788498382372', 'titulo': 'Coraline', 'autores': ['Neil Gaiman']}
        old = {'libro_id': 'lib-1', 'fuente': 'goodreads', 'puntuacion': 4.2, 'numero_valoraciones': 100, 'url': 'https://www.goodreads.com/book/show/123', 'actualizado_en': '2026-10-01T00:00:00Z', 'caduca_en': '2026-10-08T00:00:00Z'}
        calls = []
        def provider(isbn):
            calls.append(isbn)
            return {'books': [], 'url': 'https://www.goodreads.com/book/show/123'}
        result, stats = refresh({'libros': [book]}, {'ratings': [old], 'offers': []}, provider, now=datetime(2026, 10, 25, tzinfo=timezone.utc), budget=10, source='goodreads')
        self.assertEqual(calls, [book['isbn13']])
        self.assertEqual(stats['unrated'], 1)
        self.assertFalse(any(r['libro_id'] == 'lib-1' and r.get('fuente') == 'goodreads' for r in result['ratings']))

if __name__ == '__main__':
    unittest.main()
