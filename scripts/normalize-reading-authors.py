#!/usr/bin/env python3
"""Una persona por autor en el catálogo de lecturas.

Aplica `split_authors` a los libros ya publicados («A / B», «A y B», usuarios de redes y nombres
repetidos). Las fichas bibliográficas que se quedan sin libros se retiran, y las nuevas se crean
con la misma función que usa la ingesta. Las biografías manuales no se tocan.
`--check` falla si queda algo por normalizar (contrato de datos).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from reading_intake_core import split_authors  # noqa: E402
from reading_intake_fetch import write_if_changed  # noqa: E402
from reading_intake_pipeline import update_authors  # noqa: E402
from reading_ratings_refresh import write_changed  # noqa: E402


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    cat_path, auth_path = ROOT / 'data/reading-catalogue.json', ROOT / 'data/reading-authors.json'
    catalogue, authors = read(cat_path), read(auth_path)
    changed = []
    for book in catalogue['libros']:
        fixed = split_authors(book['autores'])
        if fixed != book['autores']:
            changed.append((book['id'], book['autores'], fixed))
            book['autores'] = fixed
    if args.check:
        for ident, old, new in changed:
            print(f'{ident}: {old} -> {new}')
        if changed:
            print('Autores sin normalizar; ejecutar scripts/normalize-reading-authors.py', file=sys.stderr)
            return 1
        print(f'Autores normalizados: {len(catalogue["libros"])} libros')
        return 0
    if not changed:
        print('Nada que normalizar')
        return 0
    used = {name for book in catalogue['libros'] for name in book['autores']}
    retired = [a['nombre'] for a in authors['autores'] if a.get('tipo') == 'bibliografico' and a['nombre'] not in used]
    authors['autores'] = [a for a in authors['autores'] if a['nombre'] in used or a.get('tipo') != 'bibliografico']
    ids = {ident for ident, _, _ in changed}
    update_authors(authors, catalogue, [b for b in catalogue['libros'] if b['id'] in ids], date.today().isoformat())
    # Mismo serializador que el refresco de precios: conserva el orden de claves del catálogo.
    write_changed(cat_path, catalogue)
    write_if_changed(auth_path, authors)
    for ident, old, new in changed:
        print(f'{ident}: {old} -> {new}')
    print(f'{len(changed)} libros normalizados; fichas retiradas: {retired}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
