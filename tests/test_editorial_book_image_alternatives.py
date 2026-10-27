import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('libros/index.html', 'libros/samuel-entre-mundos/index.html', 'las-manecillas-del-recuerdo/index.html')
BOOK_TERMS = ('samuel', 'manecillas', 'recuerdo')

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs))

class BookImageAlternatives(unittest.TestCase):
    def test_identifiable_book_images_have_descriptive_alt(self):
        checked = 0
        for rel in PAGES:
            parser = Images()
            parser.feed((ROOT / rel).read_text(encoding='utf-8'))
            for image in parser.images:
                source = (image.get('src') or '').lower()
                if not any(term in source for term in BOOK_TERMS):
                    continue
                if image.get('role') == 'presentation' or image.get('aria-hidden') == 'true':
                    continue
                alt = image.get('alt')
                self.assertIsNotNone(alt, f'{rel}: imagen {source} sin atributo alt')
                self.assertTrue(alt.strip(), f'{rel}: imagen informativa {source} con alt vacío')
                self.assertGreaterEqual(len(alt.strip()), 5, f'{rel}: alternativa demasiado corta para {source}: {alt!r}')
                checked += 1
        self.assertGreater(checked, 0, 'No se encontraron imágenes identificables de obras en las fichas HTML')

if __name__ == '__main__':
    unittest.main()
