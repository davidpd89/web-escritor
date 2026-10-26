import importlib.util
import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_builder_publisher_links', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current = [dict(attrs).get('href'), '']
    def handle_data(self, data):
        if self.current is not None:
            self.current[1] += data
    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append(tuple(self.current))
            self.current = None

class PublisherLinkHomogeneity(unittest.TestCase):
    def test_published_books_use_existing_publisher_destinations(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        checked = 0
        destinations = {}
        for book in data['libros']:
            if book['estado'] != 'publicado':
                continue
            slug = book.get('editorial_slug') or book.get('editorial_catalogo_slug')
            if not slug:
                continue
            family = 'editoriales' if book.get('editorial_slug') else 'recomendaciones/editoriales'
            expected = f'/{family}/{slug}/'
            parser = Links()
            parser.feed(builder.publisher_link(book))
            self.assertEqual(len(parser.links), 1, f'{book["slug"]}: falta un enlace editorial único')
            href, label = parser.links[0]
            self.assertEqual(href, expected, f'{book["slug"]}: destino editorial incorrecto: {href}')
            self.assertEqual(label.strip(), book['editorial'], f'{book["slug"]}: nombre editorial distinto')
            self.assertTrue((ROOT / family / slug / 'index.html').is_file(), f'{book["slug"]}: destino inexistente: {expected}')
            key = (family, slug)
            if key in destinations:
                self.assertEqual(destinations[key], href, f'{book["slug"]}: destino no homogéneo')
            destinations[key] = href
            checked += 1
        self.assertGreater(checked, 0, 'No se encontraron libros publicados con editorial enlazada')

if __name__ == '__main__':
    unittest.main()