import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]

class AmazonIsbnDestinations(unittest.TestCase):
    def test_real_catalogue_search_links(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = catalogue['libros']
        checked = 0
        for book in books:
            href = book.get('amazon_busqueda_isbn')
            if not href or book.get('estado') != 'publicado':
                continue
            checked += 1
            url = urlsplit(href)
            query = parse_qs(url.query, keep_blank_values=True)
            context = f"data/reading-catalogue.json libro={book.get('id')} href={href}"
            with self.subTest(book=book.get('id')):
                self.assertEqual(url.scheme, 'https', context)
                self.assertEqual(url.hostname, 'www.amazon.es', context)
                self.assertEqual(url.path, '/s', context)
                self.assertEqual(query.get('k'), [str(book['isbn13'])], context)
                self.assertEqual(query.get('tag'), ['davidporto-21'], context)
                self.assertFalse(url.username or url.password or url.port, context)
        self.assertGreater(checked, 0, 'No se examinaron enlaces Amazon de libros publicados')

if __name__ == '__main__':
    unittest.main()