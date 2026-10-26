import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_social_builder', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class Metadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'meta':
            attrs = dict(attrs)
            key = attrs.get('property') or attrs.get('name')
            if key:
                self.meta[key] = attrs.get('content', '')

class SocialImageTests(unittest.TestCase):
    def test_book_pages_use_their_own_existing_covers(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = builder.validate(data, ROOT)
        template = (ROOT / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
        self.assertTrue(books, 'No hay fichas para verificar')
        for book in books:
            with self.subTest(book=book['id']):
                html = builder.render_book(data, book, template)
                parser = Metadata()
                parser.feed(html)
                meta = parser.meta
                expected = builder.SITE + book['portada_local']
                self.assertEqual(meta.get('og:image'), expected, book['id'] + ': og:image')
                self.assertEqual(meta.get('twitter:image'), expected, book['id'] + ': twitter:image')
                self.assertEqual(meta.get('og:image:width'), str(book['portada_ancho']), book['id'])
                self.assertEqual(meta.get('og:image:height'), str(book['portada_alto']), book['id'])
                self.assertIn(book['titulo'], meta.get('og:image:alt', ''), book['id'])
                self.assertIn(book['titulo'], meta.get('twitter:image:alt', ''), book['id'])
                self.assertTrue((ROOT / book['portada_local'].lstrip('/')).is_file(), book['id'] + ': portada inexistente')

if __name__ == '__main__':
    unittest.main()
