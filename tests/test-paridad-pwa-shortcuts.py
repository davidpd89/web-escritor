#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
public = {
    x['url']: x
    for raw in registry['entries']
    for x in [{**registry.get('defaults', {}), **raw}]
    if x['status'] == 'public'
}
shortcuts = manifest.get('shortcuts', [])
assert shortcuts, 'El manifiesto no contiene shortcuts'
seen = set()
for item in shortcuts:
    url = item['url']
    assert url not in seen, f'Shortcut duplicado: {url}'
    seen.add(url)
    assert url.startswith('/') and not url.startswith('//'), url
    assert url in public, f'Shortcut no registrado: {url}'
    source = public[url].get('sourceFile', '')
    assert source.endswith('.html') and (ROOT / source).is_file(), url
    assert item.get('name', '').strip(), f'Shortcut sin nombre: {url}'
    assert item.get('short_name', '').strip(), f'Shortcut sin nombre corto: {url}'
    assert len(item['short_name']) <= len(item['name']) + 10, url
print(f'OK shortcuts PWA: {len(shortcuts)} destinos')
