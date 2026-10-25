#!/usr/bin/env python3
"""Paridad entre canonical y nodos WebPage del JSON-LD institucional."""
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'autor.html', 'ai/index.html', 'accesibilidad/index.html']

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonical = None
        self.blocks = []
        self.ld = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'canonical' in a.get('rel', '').lower().split():
            self.canonical = a.get('href')
        if tag == 'script' and a.get('type', '').lower() == 'application/ld+json':
            self.ld = True
            self.parts = []

    def handle_data(self, data):
        if self.ld:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.ld:
            self.blocks.append(json.loads(''.join(self.parts)))
            self.ld = False

def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)

errors = []
checked = 0
for rel in PAGES:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f'{rel}: falta el HTML publicado')
        continue
    doc = Document()
    try:
        doc.feed(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        errors.append(f'{rel}: JSON-LD inválido: {exc}')
        continue
    if not doc.canonical:
        errors.append(f'{rel}: falta canonical')
        continue
    for node in walk(doc.blocks):
        types = node.get('@type', [])
        types = [types] if isinstance(types, str) else types
        if 'WebPage' not in types:
            continue
        checked += 1
        url = node.get('url')
        if url and url != doc.canonical:
            errors.append(f'{rel}: WebPage.url={url!r}, canonical={doc.canonical!r}')
        entity_id = node.get('@id')
        if entity_id and urldefrag(entity_id).url != doc.canonical:
            errors.append(f'{rel}: WebPage.@id={entity_id!r}, canonical={doc.canonical!r}')
assert checked > 0, 'No se encontraron nodos WebPage en las páginas institucionales'
if errors:
    sys.exit('IDENTIDAD WEBPAGE:\n' + '\n'.join(errors))
print(f'OK: {checked} nodos WebPage comprobados')
