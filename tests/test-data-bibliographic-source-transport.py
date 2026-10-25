import ipaddress
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('fuente_bibliografica_url', 'fuente_publicacion_url', 'portada_fuente_url', 'sinopsis_fuente_url')

class BibliographicSourceTransport(unittest.TestCase):
    def test_public_book_source_urls(self):
        books = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']
        checked = 0
        for book in books:
            if book.get('estado') != 'publicado':
                continue
            links = [(key, book.get(key)) for key in FIELDS]
            links += [('resenas.url', review.get('url')) for review in book.get('resenas', [])]
            for field, href in links:
                if not href:
                    continue
                checked += 1
                context = f"data/reading-catalogue.json {book.get('id')} {field}: {href}"
                with self.subTest(book=book.get('id'), field=field):
                    self.assertFalse(any(ord(c) < 32 or ord(c) == 127 for c in href), context)
                    url = urlsplit(href)
                    self.assertEqual(url.scheme, 'https', context)
                    self.assertTrue(url.hostname, context)
                    self.assertFalse(url.username or url.password, context)
                    self.assertIsNone(url.port, context)
                    host = url.hostname or ''
                    self.assertNotEqual(host, 'localhost', context)
                    self.assertFalse(host.endswith('.localhost') or host.endswith('.local'), context)
                    try:
                        ipaddress.ip_address(host)
                    except ValueError:
                        self.assertIn('.', host, context)
                    else:
                        self.fail(f'{context}: dirección IP directa no permitida')
        self.assertGreater(checked, 0, 'No se comprobaron fuentes bibliográficas públicas')

if __name__ == '__main__':
    unittest.main()