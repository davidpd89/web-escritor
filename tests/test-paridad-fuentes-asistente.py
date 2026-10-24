#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
assistant = json.loads((ROOT / 'data/assistant-source-registry.json').read_text(encoding='utf-8'))
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
by_id = {x['id']: {**registry.get('defaults', {}), **x} for x in registry['entries']}
errors = []
seen = set()
for source in assistant['sources']:
    sid = source['id']
    if sid in seen:
        errors.append(f'{sid}: fuente duplicada')
    seen.add(sid)
    entry = by_id.get(sid)
    if not entry:
        errors.append(f'{sid}: no existe en el registro global')
        continue
    if entry['status'] != 'public':
        errors.append(f'{sid}: fuente no pública')
    if entry['url'] != source['url']:
        errors.append(f'{sid}: URL del asistente distinta de la autoridad')
    path = ROOT / entry.get('sourceFile', '')
    if not path.is_file():
        errors.append(f'{sid}: archivo publicado inexistente')
    elif path.suffix == '.html':
        html = path.read_text(encoding='utf-8').lower()
        if 'name="robots" content="noindex' in html:
            errors.append(f'{sid}: fuente noindex expuesta al asistente')
assert len(seen) >= 5, 'Catálogo del asistente inesperadamente vacío'
assert not errors, '\n'.join(errors)
print(f'OK fuentes asistente: {len(seen)} entradas')
