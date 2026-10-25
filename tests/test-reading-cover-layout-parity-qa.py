import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs))

class ReadingCoverLayoutParity(unittest.TestCase):
    def test_published_covers_reserve_correct_space(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        published = [b for b in data['libros'] if b['estado'] == 'publicado']
        self.assertTrue(published)
        for book in published:
            with self.subTest(book=book['slug']):
                path = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
                parser = Images()
                parser.feed(path.read_text(encoding='utf-8'))
                cover = [img for img in parser.images if img.get('src', '').split('?')[0] == book['portada_local']]
                self.assertTrue(cover, 'Portada ausente en la ficha')
                self.assertTrue(any(img.get('width') == str(book['portada_ancho']) and img.get('height') == str(book['portada_alto']) for img in cover), 'Dimensiones ausentes o diferentes de los datos')

if __name__ == '__main__':
    unittest.main()