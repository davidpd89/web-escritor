import json
import unittest
from pathlib import Path
from html.parser import HTMLParser
import unicodedata

ROOT = Path(__file__).resolve().parents[1]

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs))

class GeneratedCoverAccessibleIdentity(unittest.TestCase):
    def test_published_book_covers(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        published = [b for b in data['libros'] if b['estado'] == 'publicado']
        self.assertTrue(published, 'Catálogo sin libros publicados')
        for book in published:
            path = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
            with self.subTest(book=book['id']):
                self.assertTrue(path.is_file(), f'{book["id"]}: ficha inexistente {path}')
                parser = Images()
                parser.feed(path.read_text(encoding='utf-8'))
                cover = book.get('portada_local', '')
                if not cover:
                    continue
                matches = [img for img in parser.images if img.get('src', '').split('?')[0] == cover]
                self.assertTrue(matches, f'{path}: portada {cover} ausente')
                self.assertTrue(any(normalize(book['titulo']) in normalize(img.get('alt', '') or img.get('aria-label', '')) for img in matches), f'{path}: portada sin identificación accesible de {book["titulo"]}')

if __name__ == '__main__':
    unittest.main()
