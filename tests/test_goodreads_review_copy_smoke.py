import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class GoodreadsReviewCopySmoke(unittest.TestCase):
    def test_review_labels_match_their_destination(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        checked = 0
        for book in data['libros']:
            if book.get('estado') != 'publicado':
                continue
            for review in book.get('resenas', []):
                url = review.get('url', '')
                parsed = urlsplit(url)
                if parsed.hostname not in {'goodreads.com', 'www.goodreads.com'}:
                    continue
                checked += 1
                label = review.get('titulo', '')
                context = f"data/reading-catalogue.json libro={book['id']} url={url}"
                self.assertTrue(isinstance(label, str) and label.strip(), f'{context}: enlace Goodreads sin texto')
                self.assertNotRegex(label, r'(?i)\b(?:lorem ipsum|pendiente|todo|tbd)\b', f'{context}: texto provisional {label!r}')
                if parsed.path.rstrip('/') == '/search':
                    self.assertRegex(label, r'(?i)buscar|búsqueda|encontrar|consultar', f'{context}: búsqueda presentada sin indicar su naturaleza: {label!r}')
                elif parsed.path.startswith('/book/show/'):
                    self.assertRegex(label, r'(?i)reseñas|opiniones|valoraciones|puntuaci[oó]n|goodreads', f'{context}: ficha de reseñas con texto ambiguo: {label!r}')
        self.assertGreater(checked, 0, 'data/reading-catalogue.json: no se encontraron referencias Goodreads publicadas')

if __name__ == '__main__':
    unittest.main()
