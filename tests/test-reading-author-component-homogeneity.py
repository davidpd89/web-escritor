import importlib.util
import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_builder_author_component', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class AuthorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs).get('href'))
    def handle_data(self, data):
        self.text.append(data)

class AuthorComponentHomogeneity(unittest.TestCase):
    def test_real_authors_have_consistent_profiles(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        authors = builder.author_records(ROOT)
        by_name = {a['nombre']: a for a in authors}
        checked = 0
        for book in data['libros']:
            if book['estado'] != 'publicado':
                continue
            parser = AuthorParser()
            parser.feed(builder.author_links(book, authors))
            visible = ''.join(parser.text).replace('↗', '').strip()
            expected_text = ', '.join(book['autores'])
            self.assertEqual(visible, expected_text, f'{book["slug"]}: nombres u orden de autores alterados')
            expected_links = [builder.author_url(by_name[name]) for name in book['autores'] if name in by_name]
            self.assertEqual(parser.links, expected_links, f'{book["slug"]}: enlaces de autor inconsistentes')
            for href in expected_links:
                self.assertTrue((ROOT / href.lstrip('/') / 'index.html').is_file(), f'{book["slug"]}: perfil de autor inexistente: {href}')
            checked += 1
        self.assertGreater(checked, 0, 'No se encontraron fichas publicadas para comprobar autores')

if __name__ == '__main__':
    unittest.main()