import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_ratings_refresh import refresh


class GoodreadsZeroBudget(unittest.TestCase):
    def test_zero_budget_preserves_ratings_without_requests(self):
        book = {
            'id': 'lib-0001', 'estado': 'publicado',
            'isbn13': '9788498382372', 'titulo': 'Coraline',
            'autores': ['Neil Gaiman']
        }
        rating = {
            'libro_id': 'lib-0001', 'fuente': 'goodreads',
            'puntuacion': 4.1, 'numero_valoraciones': 100,
            'url': 'https://www.goodreads.com/book/show/6785288-coraline',
            'actualizado_en': '2026-10-20T00:00:00Z',
            'caduca_en': '2026-10-27T00:00:00Z'
        }
        existing = {'schema_version': 1, 'offers': [], 'ratings': [rating]}
        original = copy.deepcopy(existing)
        provider = Mock(side_effect=AssertionError('Petición Goodreads inesperada'))
        result, stats = refresh(
            {'libros': [book]}, existing, provider,
            now=datetime(2026, 10, 26, tzinfo=timezone.utc),
            budget=0, source='goodreads'
        )
        provider.assert_not_called()
        self.assertEqual(stats['attempted'], 0)
        self.assertEqual(stats['updated'], 0)
        self.assertEqual(result, original, 'Goodreads: budget=0 alteró el mercado existente')


if __name__ == '__main__':
    unittest.main()
