#!/usr/bin/env python3
"""Ficha bibliográfica para los autores con libros suficientes que aún no la tienen.

Misma regla que la ingesta nocturna (`ensure_author_records` en reading_intake_pipeline): la ingesta la aplica cada
noche; este script la aplica una vez sobre el catálogo actual. `--check` falla si falta alguna ficha.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from reading_intake_fetch import write_if_changed  # noqa: E402
from reading_intake_pipeline import ensure_author_records, mark_corporate_authors  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    catalogue = json.loads((args.root / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    path = args.root / 'data/reading-authors.json'
    authors = json.loads(path.read_text(encoding='utf-8'))
    added = ensure_author_records(authors, catalogue, date.today().isoformat())
    marked = mark_corporate_authors(authors)
    if args.check:
        if added or marked:
            print(f'{len(added)} autores sin ficha y {len(marked)} firmas corporativas sin marcar; ejecutar '
                  'scripts/backfill-reading-author-pages.py', file=sys.stderr)
            return 1
        print('Fichas de autor al día')
        return 0
    if added or marked:
        write_if_changed(path, authors)
    print(f'{len(added)} fichas de autor añadidas; {len(marked)} firmas marcadas como organización')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
