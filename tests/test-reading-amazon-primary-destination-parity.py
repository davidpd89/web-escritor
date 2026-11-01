#!/usr/bin/env python3
"""Paridad de los enlaces principales Amazon de fichas publicadas."""
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.active = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.active = {'attrs': dict(attrs), 'text': ''}

    def handle_data(self, data):
        if self.active is not None:
            self.active['text'] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.active is not None:
            self.links.append(self.active)
            self.active = None

spec = importlib.util.spec_from_file_location('reading_builder', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
errors = []
checked = 0

for book in catalogue['libros']:
    if book['estado'] != 'publicado':
        continue
    # The verified ASIN (/dp/) wins over the ISBN search, as on the page.
    expected = builder.amazon_destination(book)
    if not expected:
        continue
    path = ROOT / 'recomendaciones' / 'libros' / book['slug'] / 'index.html'
    if not path.is_file():
        errors.append(f'{path.relative_to(ROOT)}: ficha inexistente')
        continue
    parser = Links()
    parser.feed(path.read_text(encoding='utf-8'))
    purchases = [link for link in parser.links if 'Comprar en Amazon' in link['text']]
    checked += 1
    if not any(link['attrs'].get('href') == expected for link in purchases):
        actual = [link['attrs'].get('href') for link in purchases]
        errors.append(f'{path.relative_to(ROOT)}: compra esperada {expected!r}; destinos encontrados {actual!r}')

assert checked > 0, 'No hay libros publicados con destino principal Amazon verificable'
assert not errors, '\n'.join(errors[:50])
print(f'PASS: {checked} destinos principales Amazon verificados')