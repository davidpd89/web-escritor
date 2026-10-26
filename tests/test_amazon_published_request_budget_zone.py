import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_amazon_market import refresh_offers


class AmazonPublishedRequestBudget(unittest.TestCase):
    def test_only_published_books_consume_request_budget(self):
        books = [
            {'id': 'a', 'estado': 'publicado', 'isbn13': '9788498382372'},
            {'id': 'b', 'estado': 'borrador', 'isbn13': '9788498382372'},
            {'id': 'c', 'estado': 'publicado', 'isbn13': '9788425374012'},
            {'id': 'd', 'estado': 'pendiente', 'isbn13': '9788498382372'}
        ]
        calls = []
        def provider(book):
            calls.append(book['id'])
            return {'itemsResult': {'items': []}}
        result, stats = refresh_offers(
            {'libros': books}, {'offers': []}, provider,
            'davidporto-21', datetime(2026, 10, 26, tzinfo=timezone.utc),
            budget=1
        )
        self.assertEqual(len(calls), 1, 'Amazon: se excedió el presupuesto de una petición')
        self.assertIn(calls[0], {'a', 'c'}, 'Amazon: se consultó un libro no publicado')
        self.assertEqual(stats['attempted'], 1)
        self.assertEqual(result['offers'], [])

    def test_zero_budget_does_not_call_provider(self):
        calls = []
        result, stats = refresh_offers(
            {'libros': [{'id': 'a', 'estado': 'publicado', 'isbn13': '9788498382372'}]},
            {'offers': []}, lambda book: calls.append(book),
            'davidporto-21', datetime(2026, 10, 26, tzinfo=timezone.utc),
            budget=0
        )
        self.assertEqual(calls, [], 'Amazon: budget=0 provocó solicitudes')
        self.assertEqual(stats['attempted'], 0)
        self.assertEqual(result['offers'], [])


if __name__ == '__main__':
    unittest.main()
