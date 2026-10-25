import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.in_main = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'main':
            self.in_main = True
        if tag == 'img' and self.in_main:
            self.images.append(a)

    def handle_endtag(self, tag):
        if tag == 'main':
            self.in_main = False

class TestDocumentaryImages(unittest.TestCase):
    def test_image_contract(self):
        total = 0
        for filename in ('eventos.html', 'ferias.html'):
            parser = Images()
            parser.feed((ROOT / filename).read_text(encoding='utf-8'))
            for image in parser.images:
                src = image.get('src', '')
                with self.subTest(page=filename, image=src):
                    parsed = urlsplit(src)
                    self.assertFalse(parsed.scheme or parsed.netloc)
                    self.assertTrue(parsed.path.startswith('/assets/'))
                    file = ROOT / unquote(parsed.path).lstrip('/')
                    self.assertTrue(file.is_file(), f'Imagen inexistente: {file}')
                    self.assertGreater(int(image.get('width', 0)), 0)
                    self.assertGreater(int(image.get('height', 0)), 0)
                    self.assertGreater(len(image.get('alt', '').strip()), 15)
                    self.assertIn(image.get('loading'), ('lazy', 'eager'))
                    total += 1
        self.assertGreater(total, 0, 'No se auditaron fotografías')

if __name__ == '__main__':
    unittest.main()
