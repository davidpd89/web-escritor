#!/usr/bin/env python3
from collections import defaultdict
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
limit = 256 * 1024
failures = []
measured = defaultdict(list)
missing = []

for entry in registry['entries']:
    if entry.get('status', registry['defaults'].get('status')) != 'public':
        continue
    rel = entry.get('sourceFile', '')
    if not rel.endswith('.html'):
        continue
    path = ROOT / rel
    if not path.is_file():
        missing.append(rel)
        continue
    size = len(path.read_bytes().replace(b'\r\n', b'\n'))
    family = entry.get('territory') or entry.get('type') or 'other'
    measured[family].append((rel, size))
    if size > limit:
        failures.append(f'{rel}: {size} > {limit} bytes')

assert measured, 'No se encontraron páginas públicas'
assert not missing, 'Faltan archivos públicos: ' + repr(sorted(set(missing)))
for family, rows in sorted(measured.items()):
    largest = max(rows, key=lambda row: row[1])
    print(f'{family}: {len(rows)} páginas; máximo {largest[0]}={largest[1]} B')
assert not failures, '\n'.join(failures)
print('PASS presupuesto HTML transversal')
