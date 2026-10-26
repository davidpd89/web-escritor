#!/usr/bin/env python3
"""Ancestros de navegación homogéneos en herramientas publicadas."""
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['contador-palabras', 'limpiador-manuscritos', 'dialogo', 'legibilidad']
ORIGIN = 'https://davidportodiaz.com'

class StructuredScripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.active = False

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.active = True
            self.blocks.append('')

    def handle_data(self, data):
        if self.active:
            self.blocks[-1] += data

    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False

def find_breadcrumbs(obj):
    if isinstance(obj, list):
        for item in obj:
            yield from find_breadcrumbs(item)
    elif isinstance(obj, dict):
        types = obj.get('@type', [])
        types = [types] if isinstance(types, str) else types
        if 'BreadcrumbList' in types:
            yield obj
        for value in obj.values():
            if isinstance(value, (dict, list)):
                yield from find_breadcrumbs(value)

for slug in PAGES:
    path = ROOT / 'herramientas' / slug / 'index.html'
    parser = StructuredScripts()
    parser.feed(path.read_text(encoding='utf-8'))
    breadcrumbs = []
    for block in parser.blocks:
        breadcrumbs.extend(find_breadcrumbs(json.loads(block)))
    assert breadcrumbs, f'{path}: falta BreadcrumbList'
    for breadcrumb in breadcrumbs:
        items = sorted(breadcrumb.get('itemListElement', []), key=lambda x: x.get('position', 0))
        assert len(items) >= 3, f'{path}: migas incompletas: {items!r}'
        expected = [('Inicio', ORIGIN + '/'), ('Herramientas', ORIGIN + '/herramientas/')]
        for index, (name, url) in enumerate(expected):
            actual = items[index]
            assert actual.get('name') == name and actual.get('item') == url, f'{path}: miga {index + 1}: {actual!r}, esperado {(name, url)!r}'
        assert items[-1].get('item') == ORIGIN + f'/herramientas/{slug}/', f'{path}: última miga incorrecta: {items[-1]!r}'
print(f'OK: {len(PAGES)} herramientas conservan ancestros coherentes')
