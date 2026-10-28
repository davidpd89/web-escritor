#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
errors = []
seen = set()
checked = 0
for book in catalogue['libros']:
    if book.get('estado') != 'publicado':
        continue
    slug = book.get('slug')
    if not slug or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', slug):
        errors.append(f'Slug inválido: {book.get("titulo")}')
        continue
    if slug in seen:
        errors.append(f'Slug duplicado: {slug}')
    seen.add(slug)
    rel = f'recomendaciones/libros/{slug}/index.html'
    file = ROOT / rel
    checked += 1
    if not file.is_file():
        errors.append(f'Ficha ausente: {rel}')
        continue
    html = file.read_text(encoding='utf-8')
    canonical = f'https://davidportodiaz.com/recomendaciones/libros/{slug}/'
    if not re.search(r'<link\b[^>]*rel=[\x22\x27]canonical[\x22\x27][^>]*href=[\x22\x27]' + re.escape(canonical) + r'[\x22\x27]', html, re.I):
        errors.append(f'Canonical ausente o diferente: {slug}')
assert checked > 0, 'Ningún libro publicado comprobado'
assert not errors, '\n'.join(errors[:100])
print(f'PASS reading generated routes: {checked} libros')
