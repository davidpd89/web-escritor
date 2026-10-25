import struct
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class Meta(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'meta':
            a = dict(attrs)
            key = a.get('property') or a.get('name')
            if key:
                self.values[key] = a.get('content', '')

def jpeg_dimensions(path):
    data = path.read_bytes()
    if data[:2] != b'\xff\xd8':
        raise AssertionError(f'{path}: cabecera JPEG incorrecta')
    offset = 2
    while offset < len(data):
        if data[offset] != 255:
            offset += 1
            continue
        while offset < len(data) and data[offset] == 255:
            offset += 1
        marker = data[offset]
        offset += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            break
        size = struct.unpack_from('>H', data, offset)[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height, width = struct.unpack_from('>HH', data, offset + 3)
            return width, height
        offset += size
    raise AssertionError(f'{path}: no se encontraron dimensiones JPEG')

class HomeSocialImage(unittest.TestCase):
    def test_home_og_image_metadata_matches_file(self):
        parser = Meta()
        parser.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
        values = parser.values
        image = values.get('og:image', '')
        parsed = urlsplit(image)
        self.assertEqual(parsed.hostname, 'davidportodiaz.com', f'index.html: dominio de og:image inesperado: {image}')
        path = ROOT / parsed.path.lstrip('/')
        self.assertTrue(path.is_file(), f'index.html: og:image inexistente: {path}')
        self.assertEqual(path.suffix.lower(), '.jpg', f'index.html: formato no contemplado: {path}')
        actual = jpeg_dimensions(path)
        declared = (int(values['og:image:width']), int(values['og:image:height']))
        self.assertEqual(actual, declared, f'index.html: dimensiones reales {actual}, declaradas {declared}')
        self.assertTrue(values.get('og:image:alt', '').strip(), 'index.html: falta descripción de imagen Open Graph')
        self.assertEqual(values.get('twitter:image'), image, 'index.html: Twitter y Open Graph anuncian imágenes distintas')

if __name__ == '__main__':
    unittest.main()
