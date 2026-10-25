#!/usr/bin/env python3
"""Integridad de title y description en HTML institucional publicado."""
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'autor.html', 'ai/index.html', 'accesibilidad/index.html', 'redes-sociales/index.html']

class Head(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_title = False
        self.titles = []
        self.descriptions = []
        self.robots = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'head':
            self.in_head = True
        elif tag == 'body':
            self.in_head = False
        if not self.in_head:
            return
        if tag == 'title':
            self.in_title = True
            self.titles.append('')
        if tag == 'meta':
            name = a.get('name', '').lower()
            if name == 'description':
                self.descriptions.append(a.get('content', ''))
            elif name == 'robots':
                self.robots.append(a.get('content', ''))

    def handle_data(self, data):
        if self.in_title:
            self.titles[-1] += data

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        elif tag == 'head':
            self.in_head = False

errors = []
seen = {}
checked = 0
for rel in PAGES:
    path = ROOT / rel
    if not path.is_file():
        errors.append(f'{rel}: HTML inexistente')
        continue
    head = Head()
    head.feed(path.read_text(encoding='utf-8'))
    if any('noindex' in [v.strip().lower() for v in value.split(',')] for value in head.robots):
        continue
    checked += 1
    title = [v.strip() for v in head.titles]
    descriptions = [v.strip() for v in head.descriptions]
    if len(title) != 1 or not title[0]:
        errors.append(f'{rel}: title={title!r}; se exige uno no vacío')
    if len(descriptions) != 1 or not descriptions[0]:
        errors.append(f'{rel}: description={descriptions!r}; se exige una no vacía')
    if len(title) == len(descriptions) == 1 and title[0] and descriptions[0]:
        pair = (title[0].casefold(), descriptions[0].casefold())
        if pair in seen:
            errors.append(f'{rel}: title y description duplicados respecto a {seen[pair]}: {pair!r}')
        seen[pair] = rel
assert checked > 0, 'No se comprobaron documentos indexables'
if errors:
    sys.exit('METADATOS INSTITUCIONALES:\n' + '\n'.join(errors))
print(f'OK: {checked} documentos indexables con metadatos íntegros')
