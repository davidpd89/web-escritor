#!/usr/bin/env python3
"""Protege los destinos Amazon de cada formato de compra."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.anchors.append(dict(attrs))

catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
errors = []
checked = 0

for book in catalogue['libros']:
    if book['estado'] != 'publicado':
        continue
    options = book.get('formatos_compra', [])
    if not options:
        continue
    relative = Path('recomendaciones/libros') / book['slug'] / 'index.html'
    path = ROOT / relative
    if not path.is_file():
        errors.append(f'{relative}: ficha inexistente')
        continue
    parser = Anchors()
    parser.feed(path.read_text(encoding='utf-8'))
    hrefs = {a.get('href') for a in parser.anchors}
    for option in options:
        checked += 1
        expected = option['url']
        parsed = urlsplit(expected)
        tag = parse_qs(parsed.query).get('tag', [])
        if parsed.hostname not in ('amazon.es', 'www.amazon.es') or not tag or not tag[0]:
            errors.append(f'{relative}: {option["formato"]}: destino sin afiliación válida: {expected}')
        # La web añade language=es_ES para que Amazon.es no muestre el recuadro de compra en inglés.
        if expected not in hrefs and expected + ('&' if '?' in expected else '?') + 'language=es_ES' not in hrefs:
            errors.append(f'{relative}: {option["formato"]}: falta el enlace exacto {expected}')

assert checked > 0, 'No hay formatos de compra declarados para comprobar'
assert not errors, '\n'.join(errors[:60])
print(f'PASS: {checked} destinos comerciales por formato')