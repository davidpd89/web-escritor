#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / 'pagefind/eligible-manifest.json'
assert manifest_path.is_file(), 'Falta el índice construido de Pagefind'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
raw = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
defaults = raw.get('defaults', {})
# Una entrada de ancla (`/pagina/#seccion`) no representa a la pagina: si la pagina tiene entrada propia,
# esa es la que cuenta (misma regla que scripts/build-pagefind-index.py).
all_entries = [e for item in raw['entries'] if (e := {**defaults, **item}).get('sourceFile')]
page_sources = {e['sourceFile'] for e in all_entries if '#' not in e['url']}
by_source = {e['sourceFile']: e for e in all_entries if e['sourceFile'] not in page_sources or '#' not in e['url']}
errors = []
seen = set()
for rel in manifest['pages']:
    if rel in seen:
        errors.append(f'Entrada repetida: {rel}')
    seen.add(rel)
    file = ROOT / rel
    if not file.is_file():
        errors.append(f'Sin documento: {rel}')
        continue
    entry = by_source.get(rel)
    if entry:
        if entry['status'] != 'public' or entry.get('searchIndex') is False:
            errors.append(f'Página no indexable presente: {rel}')
        url = entry['url']
        expected = '/' + rel[:-10] if rel.endswith('index.html') else '/' + rel
        if url != expected:
            errors.append(f'{rel}: resultado {expected} != ruta editorial {url}')
    else:
        expected = '/' + rel[:-10] if rel.endswith('index.html') else '/' + rel
        if not expected.startswith('/'):
            errors.append(f'Ruta inválida: {rel}')
assert manifest['page_count'] == len(manifest['pages'])
assert len(seen) >= 10, 'Corpus Pagefind vacío'
assert not errors, '\n'.join(errors[:100])
print(f'PASS Pagefind routes: {len(seen)} documentos')
