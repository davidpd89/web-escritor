import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('reading_build', ROOT / 'scripts/build-reading-catalogue.py')
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

class DescriptionPreservationTest(unittest.TestCase):
    def test_book_descriptions_remain_complete(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = [b for b in data['libros'] if b['estado'] == 'publicado' and b.get('descripcion_breve')]
        self.assertTrue(books, 'No hay descripciones públicas para verificar')
        for book in books:
            path = ROOT / BUILD.url(book).lstrip('/') / 'index.html'
            with self.subTest(book=book['id']):
                self.assertTrue(path.is_file(), f'{path}: falta la ficha')
                parser = TextParser()
                parser.feed(path.read_text(encoding='utf-8'))
                text = ' '.join(' '.join(parser.parts).split())
                expected = ' '.join(book['descripcion_breve'].split())
                self.assertIn(expected, text, f'{path}: descripción truncada o puntuación modificada: {expected!r}')

if __name__ == '__main__':
    unittest.main()
