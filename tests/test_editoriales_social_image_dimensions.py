import re
import struct
import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]


def dimensions(path):
    data = path.read_bytes()
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return struct.unpack('>II', data[16:24])
    if data[:3] == b'\xff\xd8\xff':
        offset = 2
        while offset + 4 <= len(data):
            if data[offset] != 255:
                raise AssertionError(f'{path}: segmento JPEG inválido')
            while offset < len(data) and data[offset] == 255:
                offset += 1
            marker = data[offset]
            offset += 1
            if marker in (0xD8, 0xD9, 0x01) or 0xD0 <= marker <= 0xD7:
                continue
            length = struct.unpack('>H', data[offset:offset + 2])[0]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                height, width = struct.unpack('>HH', data[offset + 3:offset + 7])
                return width, height
            offset += length
    raise AssertionError(f'{path}: formato de imagen no reconocido')


def property_value(html, name):
    match = re.search(r'<meta\s+property="' + re.escape(name) + r'"\s+content="([^"]+)"', html)
    return match.group(1) if match else None


class EditorialImageDimensions(unittest.TestCase):
    def test_dimensions_match_binary(self):
        pages = sorted((ROOT / 'editoriales').rglob('index.html'))
        self.assertTrue(pages, 'editoriales: faltan páginas')
        for page in pages:
            html = page.read_text(encoding='utf-8')
            image = property_value(html, 'og:image')
            self.assertTrue(image, f'{page}: falta og:image')
            image_path = ROOT / unquote(urlsplit(image).path).lstrip('/')
            self.assertTrue(image_path.is_file(), f'{page}: no existe {image_path}')
            actual = dimensions(image_path)
            declared = []
            for field in ('og:image:width', 'og:image:height'):
                value = property_value(html, field)
                self.assertIsNotNone(value, f'{page}: falta {field}')
                self.assertRegex(value, r'^[1-9][0-9]*$', f'{page}: {field} inválido: {value}')
                declared.append(int(value))
            self.assertEqual(tuple(declared), actual, f'{page}: dimensiones declaradas {declared}, archivo {actual}')


if __name__ == '__main__':
    unittest.main()