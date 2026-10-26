#!/usr/bin/env python3
"""Controla el presupuesto de CSS referenciado por el mapa del sitio."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'mapa-del-sitio/index.html'
LIMIT = 512 * 1024

class CSSParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag != 'link':
            return
        a = dict(attrs)
        rel = set(a.get('rel', '').lower().split())
        if 'stylesheet' in rel or ('preload' in rel and a.get('as', '').lower() == 'style'):
            self.urls.append(a.get('href', ''))

parser = CSSParser()
parser.feed(PAGE.read_text(encoding='utf-8'))
assert parser.urls, f'{PAGE}: no se han encontrado recursos CSS'

seen = set()
total = 0
errors = []
for url in parser.urls:
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc:
        continue
    resource = unquote(parsed.path)
    if not resource.startswith('/') or not resource.endswith('.css'):
        errors.append(f'{PAGE}: recurso CSS local inválido: {url}')
        continue
    if resource in seen:
        continue
    seen.add(resource)
    target = ROOT / resource.lstrip('/')
    if not target.is_file():
        errors.append(f'{PAGE}: CSS inexistente: {url}')
        continue
    size = target.stat().st_size
    if size == 0:
        errors.append(f'{PAGE}: CSS vacío: {url}')
    total += size

assert not errors, '\n'.join(errors)
assert total <= LIMIT, (
    f'{PAGE}: CSS referenciado={total} bytes; presupuesto={LIMIT} bytes; '
    f'recursos únicos={len(seen)}'
)
print(f'PASS: {len(seen)} recursos CSS, {total} bytes de {LIMIT} permitidos')
