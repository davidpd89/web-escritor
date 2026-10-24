#!/usr/bin/env python3
import html
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_builder', ROOT / 'scripts/build-pagefind-index.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
by_source = {x['sourceFile']: x for x in registry['entries'] if x.get('sourceFile')}
count = 0
for rel in mod.eligible_pages(ROOT):
    entry = by_source.get(rel)
    if not entry or not entry.get('label'):
        continue
    original = (ROOT / rel).read_text(encoding='utf-8')
    projected = mod.inject_registry_search_title(original, entry)
    needle = 'data-pagefind-meta="title[content]" content="' + html.escape(entry['label'], quote=True) + '"'
    assert projected.count(needle) == 1, f'{rel}: título de búsqueda ausente o duplicado'
    assert original in projected or projected.replace('<meta ' + needle + '>\n', '') == original, f'{rel}: la inyección modificó otro contenido'
    assert projected.lower().count('</head>') == 1, f'{rel}: cabecera alterada'
    count += 1
assert count > 10, 'La prueba no ha recorrido páginas suficientes'
print(f'OK Pagefind: {count} etiquetas contrastadas')
