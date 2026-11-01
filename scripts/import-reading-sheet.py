#!/usr/bin/env python3
"""Importación reproducible desde las cinco pestañas reales del catálogo.

El snapshot conserva datos recibidos. La revisión editorial separada autoriza
qué se publica. Los nuevos libros son borradores hasta tener fuentes y portada.
No descarga imágenes, genera sinopsis ni convierte un enlace público en permiso.
"""
import argparse
import importlib.util
import json
import os
import sys
import urllib.request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TABS = ('01_LIBROS', '02_CATEGORIAS', '03_PORTADAS', '04_ENLACES', '05_FUENTES')
spec = importlib.util.spec_from_file_location('reading_import_builder', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def rows(values):
    if not values:
        return []
    headers = values[0]
    if len(set(headers)) != len(headers):
        raise ValueError('Cabeceras repetidas')
    return [dict(zip(headers, row)) for row in values[1:] if row and row[0]]


def read_live(spreadsheet, token):
    from urllib.parse import urlencode
    query = urlencode([('ranges', f"'{tab}'!A1:Z1000") for tab in TABS] + [('valueRenderOption', 'UNFORMATTED_VALUE')])
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet}/values:batchGet?{query}'
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return {tab: item.get('values', []) for tab, item in zip(TABS, payload['valueRanges'])}


AMAZON_FIELDS = ('formatos_compra', 'precios_amazon_revision', 'formatos_amazon_buscados')


def convert(snapshot, review, existing, root):
    sheets = snapshot['sheets']
    if any(tab not in sheets for tab in TABS):
        raise ValueError('Faltan pestañas del catálogo')
    data = {'schema_version': 1, 'categorias': [dict(c) for c in existing['categorias']], 'libros': [], 'libro_categorias': []}
    cat_index = {c['id']: i for i, c in enumerate(data['categorias'])}
    for c in rows(sheets['02_CATEGORIAS']):
        kind = {'subgenero': 'genero', 'tema': 'tematica'}.get(c['tipo'], c['tipo'])
        item = {'id': c['id'], 'slug': c.get('slug_web') or c['id'], 'nombre': c['nombre'], 'tipo': kind, 'descripcion': c['descripcion'], 'orden': int(c['orden']), 'activa': str(c['activa']).casefold() in {'sí', 'si', 'true', '1'}}
        if item['id'] in cat_index:
            data['categorias'][cat_index[item['id']]] = item
        else:
            cat_index[item['id']] = len(data['categorias'])
            data['categorias'].append(item)
    links = rows(sheets['04_ENLACES'])
    covers = rows(sheets['03_PORTADAS'])
    sources = rows(sheets['05_FUENTES'])
    seen = set()
    report = []
    for row in rows(sheets['01_LIBROS']):
        source_id = row['id']
        if source_id in seen:
            raise ValueError('ID repetido en la hoja: ' + source_id)
        seen.add(source_id)
        approved = review.get('reviews', {}).get(source_id, {})
        source = next((s for s in sources if s['libro_id'] == source_id and s.get('url')), {})
        book = {'id': source_id.lower(), 'slug': row['slug'], 'titulo': row['titulo'], 'autores': [a.strip() for a in row.get('autores', row.get('autor', '')).split('|') if a.strip()], 'estado': approved.get('estado', 'borrador')}
        for key, field in [('descripcion_breve', 'descripcion_breve'), ('isbn13', 'isbn13'), ('editorial', 'editorial'), ('idioma', 'idioma')]:
            if row.get(field):
                book[key] = str(row[field])
        book['fecha_actualizacion'] = row.get('fecha_revision') or snapshot['retrieved_at']
        if row.get('numero_paginas'):
            book['numero_paginas'] = int(row['numero_paginas'])
        cover = next((c for c in covers if c['libro_id'] == source_id), {})
        book['portada_fuente_url'] = cover.get('url_imagen_editorial') or ''
        book['fuente_bibliografica_url'] = source.get('url', '')
        book.update({k: v for k, v in approved.items() if k in builder.BOOK_FIELDS and v is not None})
        if book.get('portada_local'):
            path = root / book['portada_local'].lstrip('/')
            if path.is_file():
                with Image.open(path) as image:
                    book['portada_ancho'], book['portada_alto'] = image.size
        if 'fecha_publicacion' in approved:
            if approved['fecha_publicacion']:
                book['fecha_publicacion'] = approved['fecha_publicacion']
                book['fuente_publicacion_url'] = approved.get('fuente_publicacion_url') or book['fuente_bibliografica_url']
        elif row.get('fecha_publicacion_edicion'):
            book['fecha_publicacion'] = row['fecha_publicacion_edicion']
            book['fuente_publicacion_url'] = book['fuente_bibliografica_url']
        age_source = next((s for s in sources if s['libro_id'] == source_id and s.get('campo') == 'edad orientativa'), {})
        if row.get('edad_orientativa') and age_source.get('url') and 'edad_recomendada' not in approved:
            book['edad_recomendada'] = row['edad_orientativa']
            book['fuente_edad_url'] = age_source['url']
        # The nightly Amazon sweep owns these fields; the sheet never rewinds them.
        previous = next((b for b in existing['libros'] if b['id'] == book['id']), {})
        book.update({k: previous[k] for k in AMAZON_FIELDS if k in previous})
        book_links = [link for link in links if link['libro_id'] == source_id and link.get('url')]
        book['resenas'] = [{'titulo': link['titulo_visible'], 'url': link['url'], 'fecha_verificacion': link['fecha_consulta']} for link in book_links if link['tipo'].startswith('resenas')]
        fragment = next((link for link in book_links if link['tipo'] == 'fragmento'), {})
        if fragment:
            book['fragmento_url'] = fragment['url']
        for cat in row.get('categorias[]', '').split('|'):
            if cat.strip():
                data['libro_categorias'].append({'libro_id': book['id'], 'categoria_id': cat.strip()})
        data['libros'].append(book)
        report.append({'id': source_id, 'estado': book['estado'], 'url': builder.url(book), 'needs_review': book['estado'] == 'borrador'})
    # Sheets owns its reviewed entries; the editorial pipeline owns ISBN entries.
    # Importing a sheet must never erase independently validated public books.
    state_path = root / 'data/reading-intake-state.json'
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'items': {}}
    retained = set()
    for book in existing['libros']:
        if not book['id'].startswith('isbn-'):
            continue
        evidence = state['items'].get('isbn13:' + book.get('isbn13', ''), {})
        if evidence.get('estado_ingesta') != 'publicado' or evidence.get('libro_id') != book['id']:
            raise ValueError('Libro automático sin registro de ingesta: ' + book['id'])
        if any(b['id'] == book['id'] for b in data['libros']):
            raise ValueError('La hoja intenta reemplazar un libro editorial: ' + book['id'])
        data['libros'].append(book)
        retained.add(book['id'])
    data['libro_categorias'] += [r for r in existing['libro_categorias'] if r['libro_id'] in retained]
    # Las categorías añadidas después en la web (palabras clave editoriales) se conservan.
    manual = {b['id'] for b in data['libros']} - retained
    have = {(r['libro_id'], r['categoria_id']) for r in data['libro_categorias']}
    data['libro_categorias'] += [r for r in existing['libro_categorias'] if r['libro_id'] in manual and (r['libro_id'], r['categoria_id']) not in have]
    # Orden estable: las relaciones ya publicadas conservan su posición (diffs mínimos).
    position = {(r['libro_id'], r['categoria_id']): i for i, r in enumerate(existing['libro_categorias'])}
    data['libro_categorias'].sort(key=lambda r: position.get((r['libro_id'], r['categoria_id']), len(position)))
    builder.validate(data, root)
    return data, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', type=Path, default=ROOT / 'data/reading-sheet-snapshot.json')
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    review = json.loads((ROOT / 'data/reading-import-review.json').read_text(encoding='utf-8'))
    snapshot = json.loads(args.snapshot.read_text(encoding='utf-8'))
    if args.live:
        token = os.environ.get('GOOGLE_SHEETS_ACCESS_TOKEN')
        if not token:
            parser.error('Falta GOOGLE_SHEETS_ACCESS_TOKEN: configurar acceso de solo lectura a la hoja')
        snapshot['sheets'] = read_live(review['spreadsheet_id'], token)
        from datetime import datetime
        from zoneinfo import ZoneInfo
        snapshot['retrieved_at'] = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    target = ROOT / 'data/reading-catalogue.json'
    data, report = convert(snapshot, review, json.loads(target.read_text(encoding='utf-8')), ROOT)
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if json.loads(target.read_text(encoding='utf-8')) != data:
            raise SystemExit('Importación desactualizada')
    else:
        target.write_text(text, encoding='utf-8')
        if args.live:
            args.snapshot.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Importación OK: {len(report)} libros; {sum(r["needs_review"] for r in report)} pendientes de revisión.')


if __name__ == '__main__':
    main()
