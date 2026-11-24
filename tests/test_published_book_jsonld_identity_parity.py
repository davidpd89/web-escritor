import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from contrato_libros import incumplen  # noqa: E402

SITE = 'https://davidportodiaz.com'

class StructuredData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type', '').lower() == 'application/ld+json':
            self.active = True
            self.blocks.append('')

    def handle_data(self, data):
        if self.active:
            self.blocks[-1] += data

    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False

def nodes(data):
    if isinstance(data, list):
        for item in data:
            yield from nodes(item)
    elif isinstance(data, dict):
        if '@graph' in data:
            yield from nodes(data['@graph'])
        else:
            yield data


class JsonLdIdentityParity(unittest.TestCase):
    def test_published_books_keep_name_and_isbn_in_json_ld(self):
        """Cada ficha publicada con ISBN repite título e ISBN en su JSON-LD; el fallo nombra el libro (id), no la ruta."""
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        bad, checked = {}, 0
        for book in catalogue['libros']:
            if book['estado'] != 'publicado' or not book.get('isbn13'):
                continue
            path = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
            if not path.is_file():
                bad[book['id']] = f'falta la ficha publicada {path.relative_to(ROOT).as_posix()}'
                continue
            parser = StructuredData()
            parser.feed(path.read_text(encoding='utf-8'))
            try:
                books = [node for block in parser.blocks for node in nodes(json.loads(block))
                         if node.get('@type') == 'Book' and node.get('url') == f'{SITE}/recomendaciones/libros/{book["slug"]}/']
            except ValueError as exc:
                bad[book['id']] = f'JSON-LD ilegible: {exc}'
                continue
            if len(books) != 1:
                bad[book['id']] = 'se esperaban un único Book y URL canónica'
                continue
            actual = books[0]
            if actual.get('name') != book['titulo']:
                bad[book['id']] = f'título JSON-LD {actual.get("name")!r}, esperado {book["titulo"]!r}'
            elif actual.get('isbn') != book['isbn13']:
                bad[book['id']] = f'ISBN JSON-LD {actual.get("isbn")!r}, esperado {book["isbn13"]!r}'
            checked += 1
        incumplen('identidad JSON-LD de la ficha', bad)
        self.assertGreater(checked, 0, 'No se comprobaron fichas publicadas con ISBN')


if __name__ == '__main__':
    unittest.main()
