import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
TARGET = '/assets/eventos/david-porto-diaz-feria-libro-madrid-2026-caseta-337.webp'

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs))

def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if unicodedata.category(c) != 'Mn')

class DocumentaryPhotoIdentity(unittest.TestCase):
    def test_photo_shared_by_agenda_and_press(self):
        descriptions = []
        for page in ('eventos.html', 'prensa.html'):
            parser = Images()
            parser.feed((ROOT / page).read_text(encoding='utf-8'))
            matches = [i for i in parser.images if urlsplit(i.get('src', '')).path == TARGET]
            self.assertEqual(len(matches), 1, f'{page}: fotografía de caseta 337 ausente o duplicada')
            img = matches[0]
            alt = normalize(img.get('alt', '').strip())
            self.assertTrue(alt, f'{page}: fotografía documental sin texto alternativo')
            for token in ('david porto', 'feria del libro', 'madrid', '337'):
                self.assertIn(token, alt, f'{page}: falta {token!r} en el texto alternativo {alt!r}')
            for dimension in ('width', 'height'):
                self.assertGreater(int(img.get(dimension, '0')), 0, f'{page}: dimensión {dimension} ausente')
            descriptions.append(alt)
        path = (ROOT / unquote(TARGET.lstrip('/'))).resolve()
        self.assertTrue(path.is_relative_to(ROOT) and path.is_file(), f'Fotografía compartida inexistente: {TARGET}')
        with path.open('rb') as stream:
            header = stream.read(12)
        self.assertEqual(header[:4], b'RIFF', f'{TARGET}: cabecera WebP inválida')
        self.assertEqual(header[8:12], b'WEBP', f'{TARGET}: contenido no WebP')
        self.assertEqual(len(descriptions), 2)

if __name__ == '__main__':
    unittest.main()