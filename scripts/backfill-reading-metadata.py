#!/usr/bin/env python3
"""Rellena en libros ya publicados lo que la ficha oficial de Penguin Libros ya expone:
PVP, categorías adicionales (palabras clave editoriales) y la sinopsis completa si falta.
Solo añade; no cambia nada más.

Uso: python scripts/backfill-reading-metadata.py [--apply] [--max N]
Sin modelos ni APIs de pago; respeta robots, caché y presupuesto de CachedHTTP.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reading_editorial_sources import CachedHTTP, SourceError, penguin_edition
from reading_intake_fetch import read_json, write_if_changed
from reading_taxonomy import extra_categories

ROOT = Path(__file__).resolve().parents[1]
HOST = 'https://www.penguinlibros.com/es/'


def product_url(book):
    return next((u for u in (book.get('fuente_publicacion_url'), book.get('fuente_bibliografica_url')) if u and u.startswith(HOST)), None)


def add_categories(catalogue, book, record):
    known = {c['id']: c for c in catalogue['categorias']}
    current = {r['categoria_id'] for r in catalogue['libro_categorias'] if r['libro_id'] == book['id']}
    blocked = set(book.get('categorias_excluidas', []))
    added = []
    for ident, name, kind in extra_categories(record):
        if ident in current or ident in blocked:
            continue
        if ident not in known:
            catalogue['categorias'].append({'id': ident, 'slug': ident, 'nombre': name, 'tipo': kind,
                                            'descripcion': 'Clasificación editorial: ' + name + '.',
                                            'orden': 150 + len(known), 'activa': True})
            known[ident] = catalogue['categorias'][-1]
        catalogue['libro_categorias'].append({'libro_id': book['id'], 'categoria_id': ident})
        added.append(ident)
    return added


def fill_book(catalogue, book, record, url, today):
    changes = {}
    if record.get('pvp_centimos') and book.get('pvp_centimos') != record['pvp_centimos']:
        book.update(pvp_centimos=record['pvp_centimos'], pvp_fecha_verificacion=today)
        changes['pvp'] = record['pvp_centimos']
    # Una ficha sin sinopsis completa recibe la oficial y su fuente; una ya escrita o un resumen propio no se tocan.
    if not book.get('sinopsis_completa') and book.get('sinopsis_tipo') != 'resumen_propio' and record.get('sinopsis_completa'):
        book.update(sinopsis_completa=record['sinopsis_completa'], sinopsis_fuente_url=url)
        changes['sinopsis'] = len(record['sinopsis_completa'])
    added = add_categories(catalogue, book, record)
    if added:
        changes['categorias'] = added
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--max', type=int, default=60)
    args = parser.parse_args()
    today = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    path = ROOT / 'data/reading-catalogue.json'
    catalogue = read_json(path)
    http = CachedHTTP(ROOT / '.ci/reading-editorial-cache/http', ['www.penguinlibros.com'], budget=args.max, delay=1.5)
    report = {'libros': 0, 'pvp': 0, 'sinopsis': 0, 'categorias_nuevas': 0, 'errores': []}
    for book in catalogue['libros']:
        url = product_url(book)
        if not url:
            continue
        report['libros'] += 1
        try:
            record = penguin_edition(http.get(url, ttl=86400).decode('utf-8', errors='replace'), url)
        except (SourceError, OSError, ValueError, TimeoutError) as exc:
            report['errores'].append({'id': book['id'], 'error': str(exc)[:120]})
            continue
        changes = fill_book(catalogue, book, record, url, today)
        for key in ('pvp', 'sinopsis'):
            report[key] += key in changes
        report['categorias_nuevas'] += len(changes.get('categorias', []))
        print(f"{book['id']}: {changes}")
    print(json.dumps(report, ensure_ascii=False))
    if args.apply:
        write_if_changed(path, catalogue)


if __name__ == '__main__':
    main()
