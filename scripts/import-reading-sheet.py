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


AMAZON_FIELDS = ('formatos_compra', 'precios_amazon_revision', 'formatos_amazon_buscados', 'formatos_pagina_buscados', 'portadas_amazon_buscadas', 'portada_sustituida')
# Lo que el barrido de Amazon anota y la hoja no produce: se conserva si la fila no lo fija. Sin esto cada libro de
# la hoja con `publico_amazon` (26/11, lib-0001) rompía el contrato de importación y caía en cuarentena cada noche.
# tests/test_reading_sheet_import_smoke.py obliga a clasificar aquí toda clave nueva que escriba reading_amazon_market.
MARKET_FIELDS = ('publico_amazon', 'no_lectura', 'formato_edicion', 'edicion', 'encuadernacion')
SHEET_FIELDS_TOUCHED_BY_MARKET = ('descripcion_breve', 'portada_local')
# Portada sustituida por el mercado (replace_cover): la ficha de la hoja apunta a la editorial y la reimportación
# devolvía la vieja (fuente, base de uso, medidas) junto a portada_sustituida=True: contrato roto y cuarentena,
# como lib-0001 con publico_amazon. Con la marca, la portada entera se conserva de la ficha anterior.
COVER_REPLACEMENT_FIELDS = ('portada_local', 'portada_fuente_url', 'portada_ancho', 'portada_alto', 'portada_fecha_revision',
                            'autorizacion_o_base_uso')


def has_intake_record(book, state):
    """Un libro automático (isbn-*) solo se conserva con su registro «publicado» en el estado de ingesta.
    La usa también el contrato previo a la PR de la carga (test_reading_sheet_import_smoke)."""
    evidence = state.get('items', {}).get('isbn13:' + book.get('isbn13', ''), {})
    return evidence.get('estado_ingesta') == 'publicado' and evidence.get('libro_id') == book['id']


def cover_dimensions(book, previous, root):
    """Ancho y alto de la portada: del fichero si está en el checkout; si no (portada servida desde el almacén externo,
    #1588), los que ya publicó ese libro con la misma portada. El constructor valida la huella del almacén."""
    cover = book.get('portada_local')
    if not cover:
        return
    path = root / cover.lstrip('/')
    if path.is_file():
        with Image.open(path) as image:
            book['portada_ancho'], book['portada_alto'] = image.size
    elif previous.get('portada_local') == cover and previous.get('portada_ancho') and previous.get('portada_alto'):
        book['portada_ancho'], book['portada_alto'] = previous['portada_ancho'], previous['portada_alto']


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
        cover_dimensions(book, next((b for b in existing['libros'] if b['id'] == book['id']), {}), root)
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
        book.update({k: previous[k] for k in MARKET_FIELDS if k in previous and k not in book})
        if previous.get('portada_sustituida'):
            book.update({k: previous[k] for k in COVER_REPLACEMENT_FIELDS if k in previous})
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
        if not has_intake_record(book, state):
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
    # Lo que la clasificación ya retiró no vuelve por la hoja: sin temporadas y sin géneros de adultos en lo infantil.
    sys.path.insert(0, str(ROOT / 'scripts'))
    import reading_taxonomy as taxonomy
    by_book = {}
    for rel in data['libro_categorias']:
        by_book.setdefault(rel['libro_id'], set()).add(rel['categoria_id'])
    taxonomy.drop_seasons(data, by_book)
    taxonomy.repair_children_genres(data, by_book)
    # Los veredictos de clasificación son la capa final también para los libros de la hoja (si no, --check
    # nunca reproduce el catálogo). Se reordena después para conservar la posición de lo ya publicado.
    published = {b['id']: b for b in existing['libros']}
    for book_id in taxonomy.apply_verdicts(data, by_book):
        book = next(b for b in data['libros'] if b['id'] == book_id)
        old = (published.get(book_id) or {}).get('fecha_actualizacion')
        if old and old > (book.get('fecha_actualizacion') or ''):
            book['fecha_actualizacion'] = old  # la fecha que puso la reclasificación, no la de la hoja
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
