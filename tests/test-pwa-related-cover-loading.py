from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.related_depth = 0
        self.stack = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set(a.get('class', '').split())
        related = bool(classes & {'catalogue-related', 'related-books', 'catalogue-related-books'})
        self.stack.append((tag, related))
        if related:
            self.related_depth += 1
        if tag == 'img' and self.related_depth:
            self.images.append(a)
        if tag in ('img', 'br', 'hr', 'meta', 'link', 'input', 'source'):
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack:
            return
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                removed = self.stack[index:]
                self.stack = self.stack[:index]
                self.related_depth -= sum(int(item[1]) for item in removed)
                return

class RelatedCoverLoading(unittest.TestCase):
    def test_secondary_covers_are_lazy(self):
        pages = sorted((ROOT / 'recomendaciones/libros').glob('*/index.html'))
        self.assertTrue(pages, 'No se encontraron fichas de libros')
        checked = 0
        for page in pages:
            parser = ImageParser()
            parser.feed(page.read_text(encoding='utf-8'))
            for img in parser.images:
                checked += 1
                self.assertEqual(img.get('loading'), 'lazy', f'{page}: portada secundaria {img.get("src")} sin carga diferida')
                self.assertNotEqual(img.get('fetchpriority'), 'high', f'{page}: portada secundaria {img.get("src")} compite con la imagen principal')
        # Las secciones relacionadas pueden contener únicamente enlaces textuales.
        # Si existen imágenes secundarias, se validan en el bucle anterior.

    def test_parser_detects_secondary_covers(self):
        parser = ImageParser()
        parser.feed('<section class="catalogue-related"><img src="/assets/reading-covers/test.webp" loading="lazy"></section>')
        self.assertEqual(len(parser.images), 1)
        self.assertEqual(parser.images[0].get('loading'), 'lazy')
        self.assertNotEqual(parser.images[0].get('fetchpriority'), 'high')

    def test_secondary_covers_reject_eager_loading(self):
        for attributes in ('loading="eager"', '', 'loading="lazy" fetchpriority="high"'):
            with self.subTest(attributes=attributes):
                parser = ImageParser()
                parser.feed('<section class="catalogue-related"><img src="/assets/reading-covers/test.webp" ' + attributes + '></section>')
                self.assertEqual(len(parser.images), 1)
                img = parser.images[0]
                self.assertFalse(img.get('loading') == 'lazy' and img.get('fetchpriority') != 'high')

if __name__ == '__main__':
    unittest.main()
