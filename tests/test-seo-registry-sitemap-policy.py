#!/usr/bin/env python3
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'
NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
defaults = registry.get('defaults', {})
xml = ET.parse(ROOT / 'sitemap.xml')
urls = {
    node.text.strip()
    for node in xml.findall('.//s:url/s:loc', NS)
    if node.text
}

excluded = {}
for original in registry.get('entries', []):
    entry = {**defaults, **original}
    route = entry.get('url')
    if not isinstance(route, str) or not route.startswith('/') or '#' in route:
        continue
    if entry.get('status') != 'public' or entry.get('sitemap') is False:
        excluded[ORIGIN + route] = {
            'status': entry.get('status'),
            'sitemap': entry.get('sitemap'),
            'sourceFile': entry.get('sourceFile'),
        }

assert excluded, 'El fixture real no contiene exclusiones que verificar'
leaks = {url: info for url, info in excluded.items() if url in urls}
assert not leaks, f'Rutas excluidas presentes en sitemap.xml: {leaks}'
print(f'OK: {len(excluded)} exclusiones del registro respetadas por sitemap.xml')
