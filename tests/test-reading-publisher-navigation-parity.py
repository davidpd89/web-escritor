#!/usr/bin/env python3
"""Protege la navegación hacia editoriales desde libros publicados."""
import json
from html.parser import HTMLParser
from pathlib import Path

from contrato_libros import incumplen

ROOT = Path(__file__).resolve().parents[1]

class PublisherLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            values = dict(attrs)
            if 'catalogue-publisher' in values.get('class', '').split():
                self.links.append(values.get('href', ''))

catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
errors = []
malos = {}  # id del libro -> motivo
checked = 0

for book in catalogue['libros']:
    if book['estado'] != 'publicado':
        continue
    if book.get('editorial_slug'):
        expected = '/editoriales/' + book['editorial_slug'] + '/'
    elif book.get('editorial_catalogo_slug'):
        expected = '/recomendaciones/editoriales/' + book['editorial_catalogo_slug'] + '/'
    else:
        continue
    relative = Path('recomendaciones/libros') / book['slug'] / 'index.html'
    path = ROOT / relative
    if not path.is_file():
        malos[book['id']] = 'ficha inexistente'
        continue
    parser = PublisherLinks()
    parser.feed(path.read_text(encoding='utf-8'))
    checked += 1
    if expected not in parser.links:
        malos[book['id']] = f'editorial esperada {expected}; enlaces {parser.links}'
    target = ROOT / expected.lstrip('/') / 'index.html'
    if not target.is_file():
        malos[book['id']] = f'destino editorial inexistente: {expected}'

assert checked > 0, 'No se encontraron libros publicados con editorial enlazada'
incumplen('enlace a la editorial desde la ficha', malos)
assert not errors, '\n'.join(errors[:60])
print(f'PASS: {checked} enlaces editoriales verificados')