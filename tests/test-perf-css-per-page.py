#!/usr/bin/env python3
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
LIMIT = 420 * 1024

class Styles(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = set()
    def handle_starttag(self, tag, attributes):
        if tag != 'link':
            return
        attrs = dict(attributes)
        if 'stylesheet' in (attrs.get('rel') or '').lower().split():
            self.refs.add(attrs.get('href', ''))

failures = []
count = 0
seen = set()
for item in registry['entries']:
    if item.get('status', registry['defaults'].get('status')) != 'public':
        continue
    rel = item.get('sourceFile', '')
    if not rel.endswith('.html') or rel in seen:
        continue
    seen.add(rel)
    source = ROOT / rel
    assert source.is_file(), rel
    parser = Styles()
    parser.feed(source.read_text(encoding='utf-8'))
    files = set()
    for href in parser.refs:
        url = urlsplit(href)
        if url.scheme or url.netloc or not url.path:
            continue
        target = (ROOT / unquote(url.path).lstrip('/')).resolve() if url.path.startswith('/') else (source.parent / unquote(url.path)).resolve()
        if target.is_relative_to(ROOT):
            assert target.is_file(), f'{rel}: CSS inexistente {href}'
            files.add(target)
    size = sum(len(path.read_bytes().replace(b'\r\n', b'\n')) for path in files)
    count += 1
    if size > LIMIT:
        failures.append(f'{rel}: {size} B en {len(files)} CSS')
assert count > 20, f'Muestra insuficiente: {count}'
assert not failures, '\n'.join(failures)
print(f'PASS {count} páginas con presupuesto CSS')
