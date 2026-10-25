import json
import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []
    def handle_starttag(self, tag, attrs):
        if tag == 'meta':
            a = dict(attrs)
            if a.get('property', '').lower() == 'og:image':
                self.values.append(a.get('content', ''))

class GeneratedBookOgImageAuthority(unittest.TestCase):
    def test_published_social_images(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = [b for b in data['libros'] if b['estado'] == 'publicado']
        self.assertTrue(books, 'No hay libros publicados')
        checked = 0
        for book in books:
            page = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
            self.assertTrue(page.is_file(), f'{book["id"]}: ficha ausente')
            parser = Metadata()
            parser.feed(page.read_text(encoding='utf-8'))
            for url in parser.values:
                checked += 1
                with self.subTest(page=str(page), image=url):
                    parsed = urlsplit(url)
                    self.assertEqual((parsed.scheme, parsed.netloc), ('https', 'davidportodiaz.com'), f'{page}: og:image insegura {url}')
                    self.assertFalse(parsed.query or parsed.fragment, f'{page}: og:image no canónica {url}')
                    target = (ROOT / unquote(parsed.path).lstrip('/')).resolve()
                    self.assertTrue(target.is_relative_to(ROOT.resolve()), f'{page}: ruta fuera del sitio {url}')
                    self.assertTrue(target.is_file(), f'{page}: og:image inexistente {url}')
                    with Image.open(target) as image:
                        self.assertGreater(image.width, 0, f'{page}: imagen sin anchura {url}')
                        self.assertGreater(image.height, 0, f'{page}: imagen sin altura {url}')
                        image.verify()
        self.assertGreater(checked, 0, 'Ninguna ficha publicada declara og:image; revisar el generador')

if __name__ == '__main__':
    unittest.main()
