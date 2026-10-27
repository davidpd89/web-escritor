#!/usr/bin/env python3
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
a = json.loads((ROOT / 'data/assistant-source-registry.json').read_text(encoding='utf-8'))
r = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
defaults = r.get('defaults', {})
entries = {e['id']: e for item in r['entries'] if (e := {**defaults, **item})}
errors = []
seen = set()
for source in a['sources']:
    sid = source['id']
    url = source['url']
    if sid in seen:
        errors.append(f'ID duplicado: {sid}')
    seen.add(sid)
    entry = entries.get(sid)
    if not entry:
        errors.append(f'{sid}: ausente de content-registry')
        continue
    if source.get('visibility') != 'public' or entry.get('status') != 'public':
        errors.append(f'{sid}: fuente no pública')
    if url != entry.get('url'):
        errors.append(f'{sid}: URL divergente: {url} != {entry.get("url")}')
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith('/'):
        errors.append(f'{sid}: destino no local: {url}')
        continue
    source_file = entry.get('sourceFile')
    if not source_file or not source_file.endswith('.html'):
        errors.append(f'{sid}: falta HTML publicable asociado')
    elif not (ROOT / source_file).is_file():
        errors.append(f'{sid}: no existe {source_file}')
assert len(seen) >= 10, 'Corpus RAG demasiado pequeño o vacío'
assert not errors, '\n'.join(errors[:100])
print(f'PASS assistant sources: {len(seen)} rutas verificadas')
