#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('public_dist', ROOT / 'scripts/build-public-dist.py')
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            href = dict(attrs).get('href', '')
            if href.startswith('/'):
                self.hrefs.append(href)

parser = Links()
parser.feed((ROOT / 'publicar-web/index.html').read_text(encoding='utf-8'))
assert parser.hrefs, 'Checklist sin enlaces navegables'

failures = []
for href in parser.hrefs:
    target = urlsplit(href).path
    relative = target.lstrip('/')
    if target.endswith('/'):
        relative += 'index.html'
    path = ROOT / relative
    if not path.is_file():
        failures.append(f'{href}: destino inexistente')
    elif not builder.is_publishable(relative, ROOT):
        failures.append(f'{href}: destino excluido del despliegue público')

assert not failures, '\n'.join(failures)
print(f'PASS publicar-web: {len(parser.hrefs)} destinos navegables y publicables')
