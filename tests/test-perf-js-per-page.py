#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
LIMIT = 240 * 1024

class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = set()
    def handle_starttag(self, tag, attributes):
        if tag == 'script':
            ref = dict(attributes).get('src')
            if ref:
                self.refs.add(ref)

errors = []
seen = set()
for item in registry['entries']:
    if item.get('status', registry['defaults'].get('status')) != 'public':
        continue
    rel = item.get('sourceFile', '')
    if not rel.endswith('.html') or rel in seen:
        continue
    seen.add(rel)
    page = ROOT / rel
    assert page.is_file(), rel
    p = Scripts()
    p.feed(page.read_text(encoding='utf-8'))
    files = set()
    for ref in p.refs:
        url = urlsplit(ref)
        if url.scheme or url.netloc:
            continue
        target = (ROOT / unquote(url.path).lstrip('/')).resolve() if url.path.startswith('/') else (page.parent / unquote(url.path)).resolve()
        if target.is_relative_to(ROOT):
            assert target.is_file(), f'{rel}: script inexistente {ref}'
            files.add(target)
    total = sum(len(f.read_bytes().replace(b'\r\n', b'\n')) for f in files)
    if total > LIMIT:
        errors.append(f'{rel}: {total} B, {len(files)} scripts')
assert len(seen) > 20, 'Inventario demasiado pequeño'
assert not errors, '\n'.join(errors)
print(f'PASS JS inicial en {len(seen)} páginas')
