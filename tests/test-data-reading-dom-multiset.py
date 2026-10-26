from __future__ import annotations
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
raw = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
expected = Counter(book['id'] for book in raw['libros'] if book['estado'] == 'publicado')

class Cards(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'data-catalogue-book' in a:
            assert tag == 'li', f'Tarjeta con elemento inesperado: {tag}'
            assert a.get('data-book-id'), 'Tarjeta sin ID'
            self.ids.append(a['data-book-id'])

parser = Cards()
parser.feed((ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8'))
actual = Counter(parser.ids)
missing = expected - actual
extra = actual - expected
assert not missing, f'Libros publicados sin tarjeta: {missing}'
assert not extra, f'Tarjetas extra o duplicadas: {extra}'
assert expected, 'Catálogo publicado vacío'
print(f'OK: {sum(expected.values())} libros y tarjetas sin divergencias')
