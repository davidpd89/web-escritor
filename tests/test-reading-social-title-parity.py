import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('reading_build', ROOT / 'scripts/build-reading-catalogue.py')
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        attrs = dict(attrs)
        key = attrs.get('property') or attrs.get('name')
        if key in ('og:title', 'twitter:title'):
            self.meta[key] = attrs.get('content', '')

class SocialTitleTest(unittest.TestCase):
    def test_social_titles_keep_bibliographic_punctuation(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = [b for b in data['libros'] if b['estado'] == 'publicado']
        self.assertTrue(books)
        for book in books:
            path = ROOT / BUILD.url(book).lstrip('/') / 'index.html'
            with self.subTest(path=str(path)):
                self.assertTrue(path.is_file(), f'{path}: ficha inexistente')
                parser = MetaParser()
                parser.feed(path.read_text(encoding='utf-8'))
                for key in ('og:title', 'twitter:title'):
                    self.assertIn(key, parser.meta, f'{path}: falta {key}')
                    value = parser.meta[key]
                    title = book['titulo'].strip()
                    self.assertTrue(value == title or value.startswith(title + ' | ') or value.startswith(title + ' — ') or value.startswith(title + ' - '), f'{path}: {key} modifica el título {title!r}: {value!r}')

if __name__ == '__main__':
    unittest.main()
