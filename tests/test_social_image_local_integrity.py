import importlib.util
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('pagefind_media', ROOT / 'scripts/build-pagefind-index.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        a = dict(attrs)
        key = a.get('property') or a.get('name')
        if key in ('og:image', 'og:image:secure_url', 'twitter:image'):
            self.images.append((key, a.get('content', '')))

class SocialImageIntegrity(unittest.TestCase):
    def test_public_social_images_exist(self):
        checked = 0
        for rel in BUILDER.eligible_pages(ROOT):
            parser = Metadata()
            parser.feed((ROOT / rel).read_text(encoding='utf-8'))
            for key, value in parser.images:
                parsed = urlsplit(value)
                if parsed.netloc and parsed.hostname not in ('davidportodiaz.com', 'www.davidportodiaz.com'):
                    continue
                self.assertIn(parsed.scheme, ('', 'https'), f'{rel}: {key} usa esquema {parsed.scheme!r}')
                self.assertFalse(parsed.fragment, f'{rel}: {key} contiene fragmento')
                path = unquote(parsed.path)
                self.assertTrue(path.startswith('/'), f'{rel}: {key} no tiene ruta absoluta: {value}')
                target = (ROOT / path.lstrip('/')).resolve()
                self.assertTrue(target.is_relative_to(ROOT), f'{rel}: {key} escapa de la raíz: {value}')
                self.assertTrue(target.is_file(), f'{rel}: {key} apunta a imagen inexistente: {value}')
                checked += 1
        self.assertGreater(checked, 0, 'No se encontraron imágenes sociales locales en páginas públicas')

if __name__ == '__main__':
    unittest.main()
