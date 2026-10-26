#!/usr/bin/env python3
"""Protege la navegación hacia editoriales desde libros publicados."""
import json
from html.parser import HTMLParser
from pathlib import Path

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
        errors.append(f'{relative}: ficha inexistente')
        continue
    parser = PublisherLinks()
    parser.feed(path.read_text(encoding='utf-8'))
    checked += 1
    if expected not in parser.links:
        errors.append(f'{relative}: editorial esperada {expected}; enlaces {parser.links}')
    target = ROOT / expected.lstrip('/') / 'index.html'
    if not target.is_file():
        errors.append(f'{relative}: destino editorial inexistente: {expected}')

assert checked > 0, 'No se encontraron libros publicados con editorial enlazada'
assert not errors, '\n'.join(errors[:60])
print(f'PASS: {checked} enlaces editoriales verificados')