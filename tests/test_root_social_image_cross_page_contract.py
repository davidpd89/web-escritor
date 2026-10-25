import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('index.html', 'autor.html', 'prensa.html', 'premios.html', 'eventos.html')

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        a = dict(attrs)
        key = a.get('property') or a.get('name')
        if key:
            self.meta.setdefault(key.lower(), []).append(a.get('content', ''))

    def one(self, key, page):
        values = self.meta.get(key, [])
        if len(values) != 1:
            raise AssertionError(f'{page}: se esperaba una etiqueta {key}, encontradas {len(values)}')
        return values[0]

class SocialImageIntegration(unittest.TestCase):
    def test_social_images_across_root_pages(self):
        dimensions = {}
        for page in PAGES:
            parser = Metadata()
            parser.feed((ROOT / page).read_text(encoding='utf-8'))
            image = parser.one('og:image', page)
            twitter = parser.one('twitter:image', page)
            self.assertEqual(twitter, image, f'{page}: twitter:image y og:image difieren')
            parsed = urlsplit(image)
            self.assertEqual(parsed.scheme, 'https', f'{page}: og:image sin HTTPS: {image}')
            self.assertEqual(parsed.hostname, 'davidportodiaz.com', f'{page}: og:image fuera del dominio oficial: {image}')
            self.assertFalse(parsed.query or parsed.fragment, f'{page}: og:image con parámetros o fragmento: {image}')
            path = (ROOT / unquote(parsed.path).lstrip('/')).resolve()
            self.assertTrue(path.is_relative_to(ROOT), f'{page}: ruta de imagen fuera del repositorio: {image}')
            self.assertTrue(path.is_file(), f'{page}: og:image inexistente: {image}')
            with path.open('rb') as stream:
                header = stream.read(3)
            self.assertEqual(header, bytes.fromhex('ffd8ff'), f'{page}: og:image no contiene JPEG: {image}')
            width = int(parser.one('og:image:width', page))
            height = int(parser.one('og:image:height', page))
            self.assertGreater(width, 0, f'{page}: anchura OG inválida')
            self.assertGreater(height, 0, f'{page}: altura OG inválida')
            for key in ('og:image:alt', 'twitter:image:alt'):
                self.assertGreater(len(parser.one(key, page).strip()), 10, f'{page}: descripción {key} insuficiente')
            current = (width, height)
            if image in dimensions:
                self.assertEqual(current, dimensions[image], f'{page}: dimensiones contradictorias para {image}')
            dimensions[image] = current

if __name__ == '__main__':
    unittest.main()