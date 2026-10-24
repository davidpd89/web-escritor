#!/usr/bin/env python3
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
errors = []
checked = 0
for raw in registry['entries']:
    entry = {**registry.get('defaults', {}), **raw}
    source = entry.get('sourceFile', '')
    if entry['status'] != 'public' or not source.endswith('.html'):
        continue
    path = ROOT / source
    if not path.is_file():
        continue
    page = path.read_text(encoding='utf-8')
    for block in re.findall(r'<script\b[^>]*type=[\x22\x27]application/ld\+json[\x22\x27][^>]*>(.*?)</script>', page, re.I | re.S):
        doc = json.loads(block)
        nodes = doc if isinstance(doc, list) else doc.get('@graph', [doc])
        for node in nodes:
            if not isinstance(node, dict):
                continue
            kinds = node.get('@type', [])
            if isinstance(kinds, str):
                kinds = [kinds]
            if 'Event' not in kinds or not node.get('startDate'):
                continue
            checked += 1
            fragment = unquote(str(node.get('@id', '')).split('#')[-1])
            match = re.search(r'\bid=[\x22\x27]' + re.escape(fragment) + r'[\x22\x27]', page)
            if not fragment or not match:
                errors.append(f'{source}: evento {fragment} sin ancla')
                continue
            excerpt = page[match.start():match.start() + 4500]
            dates = re.findall(r'<time\b[^>]*datetime=[\x22\x27]([^\x22\x27]+)', excerpt, re.I)
            civil = str(node['startDate'])[:10]
            if dates and not any(value[:10] == civil for value in dates):
                errors.append(f'{source}#{fragment}: JSON-LD {civil} frente a HTML {dates[:5]}')
assert checked > 0, 'No se localizaron eventos estructurados'
assert not errors, '\n'.join(errors[:100])
print(f'OK fechas de eventos: {checked} nodos')
