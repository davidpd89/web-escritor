import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'pagefind/eligible-manifest.json'
HOST = 'davidportodiaz.com'
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif', '.svg'}

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'meta':
            return
        a = dict(attrs)
        key = (a.get('property') or a.get('name') or '').lower()
        if key in {'og:image', 'og:image:url', 'twitter:image'}:
            self.images.append((key, a.get('content', '')))

class SocialImages(unittest.TestCase):
    def test_indexed_images_resolve_safely(self):
        pages = json.loads(MANIFEST.read_text(encoding='utf-8'))['pages']
        self.assertIn('mapa-del-sitio/index.html', pages)
        checked = 0
        for route in pages:
            source = ROOT / route
            self.assertTrue(source.is_file(), f'{route}: HTML ausente')
            parser = Metadata()
            parser.feed(source.read_text(encoding='utf-8'))
            for key, value in parser.images:
                checked += 1
                parsed = urlsplit(value)
                self.assertNotIn(parsed.scheme.lower(), {'http', 'data', 'javascript', 'blob'}, f'{route}: {key} inseguro: {value}')
                self.assertFalse(parsed.username or parsed.password, f'{route}: credenciales en {key}: {value}')
                if parsed.scheme:
                    self.assertEqual(parsed.scheme.lower(), 'https', f'{route}: {key}: {value}')
                    self.assertEqual(parsed.hostname, HOST, f'{route}: {key} externo: {value}')
                else:
                    self.assertFalse(parsed.netloc, f'{route}: {key} con origen externo: {value}')
                    self.assertTrue(parsed.path.startswith('/'), f'{route}: {key} no es ruta local absoluta: {value}')
                self.assertFalse(parsed.query or parsed.fragment, f'{route}: {key} contiene parámetros no representados por el archivo: {value}')
                relative = unquote(parsed.path).lstrip('/')
                self.assertNotIn('..', Path(relative).parts, f'{route}: traversal en {key}: {value}')
                target = ROOT / relative
                self.assertIn(target.suffix.lower(), EXTENSIONS, f'{route}: extensión de imagen inesperada: {value}')
                self.assertTrue(target.is_file(), f'{route}: {key} apunta a imagen inexistente: {value}')
                self.assertGreater(target.stat().st_size, 0, f'{route}: imagen vacía: {value}')
        self.assertGreater(checked, 0, 'El corpus no contiene imágenes sociales verificadas')

if __name__ == '__main__':
    unittest.main()