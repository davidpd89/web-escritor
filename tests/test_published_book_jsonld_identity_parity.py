import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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

catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
checked = 0
for book in catalogue['libros']:
    if book['estado'] != 'publicado' or not book.get('isbn13'):
        continue
    path = ROOT / 'recomendaciones/libros' / book['slug'] / 'index.html'
    assert path.is_file(), f'{path}: falta la ficha publicada de {book["titulo"]}'
    parser = StructuredData()
    parser.feed(path.read_text(encoding='utf-8'))
    books = [node for block in parser.blocks for node in nodes(json.loads(block)) if node.get('@type') == 'Book' and node.get('url') == f'{SITE}/recomendaciones/libros/{book["slug"]}/']
    assert len(books) == 1, f'{path}: se esperaban un único Book y URL canónica'
    actual = books[0]
    assert actual.get('name') == book['titulo'], f'{path}: título JSON-LD {actual.get("name")!r}, esperado {book["titulo"]!r}'
    assert actual.get('isbn') == book['isbn13'], f'{path}: ISBN JSON-LD {actual.get("isbn")!r}, esperado {book["isbn13"]!r}'
    checked += 1
assert checked > 0, 'No se comprobaron fichas publicadas con ISBN'
print(f'PASS: identidad JSON-LD de {checked} libros publicados')
