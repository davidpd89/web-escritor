import ipaddress
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ('recomendaciones', 'editoriales', 'libros')
URL_KEYS = {'url', 'image', 'contentUrl', 'embedUrl', 'sameAs', 'item', 'logo', 'thumbnailUrl'}

class JSONLDParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type', '').lower() == 'application/ld+json':
            self.current = []

    def handle_data(self, value):
        if self.current is not None:
            self.current.append(value)

    def handle_endtag(self, tag):
        if tag == 'script' and self.current is not None:
            self.blocks.append(json.loads(''.join(self.current)))
            self.current = None

def urls(value, key=''):
    if isinstance(value, dict):
        for name, child in value.items():
            yield from urls(child, name)
    elif isinstance(value, list):
        for child in value:
            yield from urls(child, key)
    elif isinstance(value, str) and key in URL_KEYS and value.startswith(('http:', 'https:')):
        yield value

class TestURLPrivacy(unittest.TestCase):
    def test_published_structured_urls(self):
        checked = 0
        for family in FAMILIES:
            for path in sorted((ROOT / family).rglob('*.html')):
                parser = JSONLDParser()
                parser.feed(path.read_text(encoding='utf-8'))
                for block in parser.blocks:
                    for value in urls(block):
                        with self.subTest(page=str(path.relative_to(ROOT)), url=value):
                            parsed = urlsplit(value)
                            self.assertEqual(parsed.scheme, 'https', f'{path}: URL no HTTPS: {value}')
                            self.assertFalse(parsed.username or parsed.password, f'{path}: credenciales publicadas: {value}')
                            host = (parsed.hostname or '').lower()
                            self.assertTrue(host, f'{path}: URL sin host: {value}')
                            self.assertNotIn(host, ('localhost', 'localhost.localdomain'), f'{path}: host local publicado: {value}')
                            self.assertFalse(host.endswith(('.local', '.internal', '.localhost')), f'{path}: host privado: {value}')
                            try:
                                address = ipaddress.ip_address(host)
                            except ValueError:
                                pass
                            else:
                                self.assertTrue(address.is_global, f'{path}: IP no pública: {value}')
                            checked += 1
        self.assertGreater(checked, 0, 'No se encontraron URL estructuradas para auditar')

if __name__ == '__main__':
    unittest.main()