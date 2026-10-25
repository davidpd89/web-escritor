import json
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = date(2026, 10, 25)

class FuturePublicationTests(unittest.TestCase):
    def test_future_books_are_not_presented_as_already_released(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = data['libros']
        for book in books:
            with self.subTest(book=book.get('id')):
                release = book.get('fecha_publicacion')
                if not release:
                    continue
                published = date.fromisoformat(release[:10])
                if published > TODAY:
                    self.assertNotEqual(book.get('estado'), 'publicado', 'Libro futuro marcado como publicado: ' + str(book.get('id')))

if __name__ == '__main__':
    unittest.main()