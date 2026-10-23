#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))

class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
    def handle_starttag(self, tag, attributes):
        if tag == 'img':
            self.images.append(dict(attributes))

failures = []
checked = 0
seen = set()
for entry in registry['entries']:
    if entry.get('status', registry['defaults'].get('status')) != 'public':
        continue
    rel = entry.get('sourceFile', '')
    if not rel.endswith('.html') or rel in seen:
        continue
    seen.add(rel)
    page = ROOT / rel
    assert page.is_file(), rel
    parser = Images()
    parser.feed(page.read_text(encoding='utf-8'))
    for attrs in parser.images:
        if attrs.get('loading', '').lower() != 'lazy':
            continue
        checked += 1
        try:
            reserved = int(attrs.get('width', '0')) > 0 and int(attrs.get('height', '0')) > 0
        except ValueError:
            reserved = False
        reserved = reserved or 'aspect-ratio:' in attrs.get('style', '').replace(' ', '').lower()
        if not reserved:
            failures.append(f'{rel}: lazy sin reserva verificable: {attrs.get("src", "sin-src")}')
assert checked > 0, 'No se localizaron imágenes lazy'
assert not failures, '\n'.join(failures[:100])
print(f'PASS {checked} imágenes lazy con reserva geométrica')
