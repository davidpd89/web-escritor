#!/usr/bin/env python3
from pathlib import Path
import gzip
import json

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
paths = set()
for entry in registry['entries']:
    if entry.get('status', registry['defaults'].get('status')) == 'public':
        rel = entry.get('sourceFile', '')
        if rel.endswith(('.html', '.xml', '.json')):
            paths.add(ROOT / rel)
for directory in ('assets', 'data'):
    for suffix in ('*.css', '*.js', '*.mjs', '*.json'):
        paths.update((ROOT / directory).rglob(suffix))
paths.add(ROOT / 'styles.css')
paths.add(ROOT / 'script.js')
paths.add(ROOT / 'sitemap.xml')
paths.add(ROOT / 'editoriales-sitemap.xml')

failures = []
checked = 0
for path in sorted(paths):
    if not path.is_file():
        continue
    data = path.read_bytes().replace(b'\r\n', b'\n')
    if len(data) < 4096:
        continue
    checked += 1
    packed = gzip.compress(data, compresslevel=9, mtime=0)
    ratio = len(packed) / len(data)
    if ratio > 0.85:
        failures.append(f'{path.relative_to(ROOT)}: gzip ratio {ratio:.3f}')

assert checked > 20, f'Muestra insuficiente: {checked}'
assert not failures, '\n'.join(failures)
print(f'PASS compresibilidad de {checked} archivos')
