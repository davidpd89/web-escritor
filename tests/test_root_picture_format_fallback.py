import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class PictureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.pictures = []
        self.active = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'picture':
            self.active = {'sources': [], 'images': []}
            self.pictures.append(self.active)
        elif self.active is not None and tag == 'source':
            self.active['sources'].append(a)
        elif self.active is not None and tag == 'img':
            self.active['images'].append(a)

    def handle_endtag(self, tag):
        if tag == 'picture':
            self.active = None

def asset(url):
    parsed = urlsplit(url)
    assert not parsed.scheme and not parsed.netloc and parsed.path.startswith('/'), f'URL no local: {url}'
    result = (ROOT / unquote(parsed.path).lstrip('/')).resolve()
    assert result.is_relative_to(ROOT), f'Ruta fuera del repositorio: {url}'
    return result

def check_signature(path, kind):
    with path.open('rb') as stream:
        header = stream.read(32)
    if kind == 'image/webp':
        return header[:4] == b'RIFF' and header[8:12] == b'WEBP'
    if kind == 'image/avif':
        return header[4:8] == b'ftyp' and (b'avif' in header or b'avis' in header)
    return False

class PictureFallback(unittest.TestCase):
    def test_picture_fallbacks(self):
        total = 0
        for page in ('index.html', 'prensa.html'):
            parser = PictureParser()
            parser.feed((ROOT / page).read_text(encoding='utf-8'))
            for number, picture in enumerate(parser.pictures, 1):
                total += 1
                context = f'{page}: picture #{number}'
                self.assertEqual(len(picture['images']), 1, f'{context}: falta imagen de respaldo única')
                img = picture['images'][0]
                self.assertTrue(img.get('alt', '').strip(), f'{context}: portada sin alternativa textual')
                for dimension in ('width', 'height'):
                    self.assertGreater(int(img.get(dimension, '0')), 0, f'{context}: dimensión {dimension} inválida')
                fallback_url = img.get('src', '')
                fallback = asset(fallback_url)
                self.assertTrue(fallback.is_file(), f'{context}: respaldo inexistente {fallback_url}')
                self.assertTrue(check_signature(fallback, 'image/webp'), f'{context}: respaldo no es WebP válido {fallback_url}')
                for source in picture['sources']:
                    mime = source.get('type', '')
                    self.assertIn(mime, ('image/avif', 'image/webp'), f'{context}: formato no reconocido {mime}')
                    candidates = [x.strip().split()[0] for x in source.get('srcset', '').split(',') if x.strip()]
                    self.assertTrue(candidates, f'{context}: source sin candidatos')
                    for url in candidates:
                        path = asset(url)
                        self.assertTrue(path.is_file(), f'{context}: fuente inexistente {url}')
                        self.assertTrue(check_signature(path, mime), f'{context}: firma incompatible con {mime}: {url}')
        self.assertGreater(total, 0, 'No se encontraron elementos picture en index.html o prensa.html')

if __name__ == '__main__':
    unittest.main()