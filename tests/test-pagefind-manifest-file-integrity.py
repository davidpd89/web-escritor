#!/usr/bin/env python3
"""Comprueba las referencias reales del manifiesto publicado de Pagefind."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest_path = ROOT / 'pagefind/eligible-manifest.json'
data = json.loads(manifest_path.read_text(encoding='utf-8'))
pages = data['pages']

assert isinstance(pages, list), f'{manifest_path}: pages no es una lista'
assert pages, f'{manifest_path}: no contiene documentos indexables'
assert data['page_count'] == len(pages), (
    f'{manifest_path}: page_count={data["page_count"]}, '
    f'pero pages contiene {len(pages)} elementos'
)

seen = set()
errors = []
for item in pages:
    if not isinstance(item, str) or not item:
        errors.append(f'Ruta inválida: {item!r}')
        continue
    if item in seen:
        errors.append(f'Documento duplicado: {item}')
    seen.add(item)
    relative = Path(item)
    if relative.is_absolute() or '..' in relative.parts or relative.suffix.lower() != '.html':
        errors.append(f'Ruta HTML inválida: {item}')
        continue
    target = ROOT / relative
    if not target.is_file():
        errors.append(f'{item}: documento indexado inexistente')
    elif target.stat().st_size == 0:
        errors.append(f'{item}: documento indexado vacío')

assert not errors, '\n'.join(errors)
print(f'PASS: {len(pages)} documentos de Pagefind existen y son únicos')
