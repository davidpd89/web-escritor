#!/usr/bin/env python3
"""Identidad WebSite frente a portada canónica y sitemap publicado."""
import json
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'autor.html', 'ai/index.html']
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'

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

def nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)

home = Document()
home.feed((ROOT / 'index.html').read_text(encoding='utf-8'))
assert home.canonical, 'index.html: falta canonical de portada'
expected = home.canonical
sitemap = ET.parse(ROOT / 'sitemap.xml').getroot()
urls = {e.findtext(NS + 'loc') for e in sitemap.findall(NS + 'url')}
errors = []
if expected not in urls:
    errors.append(f'index.html: canonical de portada {expected!r} ausente de sitemap.xml')
checked = 0
for rel in PAGES:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f'{rel}: documento inexistente')
        continue
    doc = Document()
    try:
        doc.feed(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        errors.append(f'{rel}: JSON-LD inválido: {exc}')
        continue
    for node in nodes(doc.blocks):
        types = node.get('@type', [])
        types = [types] if isinstance(types, str) else types
        if 'WebSite' not in types:
            continue
        checked += 1
        url = node.get('url')
        if url and url != expected:
            errors.append(f'{rel}: WebSite.url={url!r}, portada={expected!r}')
        entity_id = node.get('@id')
        if entity_id and urldefrag(entity_id).url != expected:
            errors.append(f'{rel}: WebSite.@id={entity_id!r}, portada={expected!r}')
assert checked > 0, 'No se encontraron nodos WebSite en las páginas comprobadas'
if errors:
    sys.exit('IDENTIDAD WEBSITE/SITEMAP:\n' + '\n'.join(errors))
print(f'OK: {checked} nodos WebSite contrastados con {expected}')
