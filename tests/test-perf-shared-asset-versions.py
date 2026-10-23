#!/usr/bin/env python3
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))

class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'script' and attrs.get('src'):
            self.urls.append(attrs['src'])
        if tag == 'link' and 'stylesheet' in (attrs.get('rel') or '').lower().split():
            self.urls.append(attrs.get('href', ''))

versions = defaultdict(lambda: defaultdict(set))
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
    p = References()
    p.feed(page.read_text(encoding='utf-8'))
    for raw in p.urls:
        url = urlsplit(raw)
        if url.scheme or url.netloc or not url.path.startswith('/'):
            continue
        if not url.path.endswith(('.css', '.js', '.mjs')):
            continue
        versions[url.path][url.query].add(rel)

errors = []
for asset, variants in sorted(versions.items()):
    users = set().union(*variants.values())
    if len(users) >= 5 and len(variants) > 1:
        detail = ', '.join(f'{query or "sin-version"}={len(pages)}' for query, pages in sorted(variants.items()))
        errors.append(f'{asset}: {detail}')
assert versions, 'Inventario de recursos vacío'
assert not errors, '\n'.join(errors)
print(f'PASS {len(versions)} identidades CSS/JS')
