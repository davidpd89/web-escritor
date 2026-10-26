#!/usr/bin/env python3
"""Verifica la coherencia de los metadatos publicados de Pagefind."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'pagefind'
manifest = json.loads((base / 'eligible-manifest.json').read_text(encoding='utf-8'))
entry = json.loads((base / 'pagefind-entry.json').read_text(encoding='utf-8'))

assert isinstance(entry.get('version'), str) and entry['version'].strip(), (
    'pagefind/pagefind-entry.json: versión ausente'
)
assert isinstance(entry.get('languages'), dict), (
    'pagefind/pagefind-entry.json: languages inválido'
)
assert 'es' in entry['languages'], (
    'pagefind/pagefind-entry.json: falta el idioma español'
)

spanish = entry['languages']['es']
assert isinstance(spanish.get('hash'), str) and spanish['hash'], (
    'pagefind/pagefind-entry.json: hash español ausente'
)
assert isinstance(spanish.get('wasm'), str) and spanish['wasm'], (
    'pagefind/pagefind-entry.json: identificador WASM ausente'
)
assert isinstance(spanish.get('page_count'), int) and spanish['page_count'] > 0, (
    'pagefind/pagefind-entry.json: page_count español inválido'
)

expected = manifest['page_count']
actual = spanish['page_count']
assert actual == expected, (
    f'pagefind/pagefind-entry.json: es.page_count={actual}; '
    f'eligible-manifest.json: page_count={expected}'
)
assert expected == len(manifest['pages']), (
    f'eligible-manifest.json: declara {expected} páginas, '
    f'pero enumera {len(manifest["pages"])}'
)
print(f'PASS: Pagefind y manifiesto coinciden en {actual} documentos')
