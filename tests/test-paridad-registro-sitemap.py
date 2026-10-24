#!/usr/bin/env python3
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
origin = 'https://davidportodiaz.com'
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
root = ET.parse(ROOT / 'sitemap.xml').getroot()
locs = [x.text for x in root.iter() if x.tag.endswith('}loc') or x.tag == 'loc']
counts = Counter(locs)
errors = []
checked = 0
for raw in registry['entries']:
    entry = {**registry.get('defaults', {}), **raw}
    source = entry.get('sourceFile')
    if not source or not source.endswith('.html'):
        continue
    path = ROOT / source
    if not path.is_file():
        continue
    content = path.read_text(encoding='utf-8').lower()
    if 'http-equiv="refresh"' in content or 'name="robots" content="noindex' in content:
        continue
    url = origin + entry['url']
    expected = entry['status'] == 'public' and entry.get('sitemap') is True
    if expected:
        checked += 1
    if expected and counts[url] != 1:
        errors.append(f'{entry["id"]}: esperado una vez, encontrado {counts[url]}')
    if entry.get('sitemap') is False and counts[url]:
        errors.append(f'{entry["id"]}: sitemap deshabilitado pero URL presente')
assert checked > 10, 'No se ha inspeccionado un corpus público suficiente'
assert not errors, '\n'.join(errors[:100])
print(f'OK paridad sitemap: {checked} rutas públicas comprobadas')
