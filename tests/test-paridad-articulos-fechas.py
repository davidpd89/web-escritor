#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
checked = 0
failures = []
for raw in registry['entries']:
    entry = {**registry.get('defaults', {}), **raw}
    source = entry.get('sourceFile', '')
    if entry['status'] != 'public' or not source.endswith('.html'):
        continue
    path = ROOT / source
    if not path.is_file():
        continue
    body = path.read_text(encoding='utf-8')
    visible = set(re.findall(r'<time\b[^>]*datetime=[\x22\x27](\d{4}-\d{2}-\d{2})', body, re.I))
    if not visible:
        continue
    for script in re.findall(r'<script\b[^>]*type=[\x22\x27]application/ld\+json[\x22\x27][^>]*>(.*?)</script>', body, re.I | re.S):
        document = json.loads(script)
        nodes = document if isinstance(document, list) else document.get('@graph', [document])
        for node in nodes:
            if not isinstance(node, dict):
                continue
            types = node.get('@type', [])
            if isinstance(types, str):
                types = [types]
            if not set(types).intersection({'Article', 'BlogPosting', 'NewsArticle'}):
                continue
            published = str(node.get('datePublished', ''))[:10]
            if not published:
                continue
            checked += 1
            if published not in visible:
                failures.append(f'{source}: datePublished={published}, time={sorted(visible)}')
assert checked > 0, 'No se encontraron artículos con fecha comprobable'
assert not failures, '\n'.join(failures[:100])
print(f'OK fechas editoriales: {checked} artículos')
