#!/usr/bin/env python3
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_map_qa', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
raw = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
books = mod.validate(raw, ROOT)
original = (ROOT / 'mapa-del-sitio/index.html').read_text(encoding='utf-8')
assert books and '</main>' in original

first = mod.render_map(original, books)
second = mod.render_map(first, books)
third = mod.render_map(second, books)
assert first == second == third, 'El bloque generado deriva al regenerarse'
assert first.count('<!-- reading-catalogue-map:start -->') == 1
assert first.count('<!-- reading-catalogue-map:end -->') == 1
for book in books:
    assert mod.url(book) in first, book['id']

empty = mod.render_map(first, [])
assert '<!-- reading-catalogue-map:start -->' not in empty
assert empty.count('</main>') == 1
print(f'PASS: fragmento estable para {len(books)} libros')
