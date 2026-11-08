#!/usr/bin/env python3
"""Salud del catálogo publicado: qué está mal y qué se puede mejorar, cada noche. Solo informa.

    python scripts/catalogue-health-report.py                 # informe con los datos del repo
    python scripts/catalogue-health-report.py --amazon 40     # y pregunta a la Creators API por 40 portadas

No bloquea nada (David, 08/11: «no hace falta que bloqueen publicaciones pero sí que tengamos controlado lo que
pasa en nuestra web»): sale con 0 aunque encuentre problemas. Escribe `.ci/salud-catalogo/informe.json` (con la
comparación con el anterior, si lo hay) y un resumen en Markdown que la carga nocturna añade a su resumen.

Cada sección es un fallo que David ya señaló y no debe volver:
- portadas: libros con la portada tipográfica propia; con --amazon, cuáles tiene Amazon (oportunidad: el barrido
  nocturno la cambiará) y cuáles no (error real: falta en Amazon también).
- precios: formatos publicados sin precio («Tapa blanda · Ver precio») y libros sin ningún formato de compra.
- textos: libros sin sinopsis de la editorial ni texto propio (sin contenido para buscadores y asistentes).
- ficheros: portadas locales que faltan en disco.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
OUT = ROOT / '.ci/salud-catalogo'
SAMPLE = 25


def entry(book, **extra):
    return {'id': book['id'], 'titulo': book.get('titulo', ''), 'isbn13': book.get('isbn13', ''),
            'editorial': book.get('editorial', ''), 'fecha_publicacion': book.get('fecha_publicacion', ''), **extra}


def by_month(books):
    """Reparto por mes de publicación: lo que sale ahora y lo que viene pesa más que el fondo (punto 2)."""
    return dict(sorted(Counter((b.get('fecha_publicacion') or '????')[:7] for b in books).items(), reverse=True)[:12])


def has_text(book, root):
    return bool(book.get('sinopsis_breve')) or (root / 'data/reading-texts' / f"isbn-{book.get('isbn13')}.json").exists()


def check(catalogue, root):
    from reading_amazon_market import generated_cover
    books = [b for b in catalogue['libros'] if b.get('estado') == 'publicado']
    typographic = [b for b in books if generated_cover(b)]
    no_price = [(b, f) for b in books for f in b.get('formatos_compra') or [] if not f.get('precio_centimos')]
    no_formats = [b for b in books if not b.get('formatos_compra')]
    no_text = [b for b in books if not has_text(b, root)]
    # portada_local es una ruta del sitio («/assets/...»): sin quitar la barra, Path la trata como absoluta.
    missing_files = [b for b in books if b.get('portada_local') and not (root / b['portada_local'].lstrip('/')).exists()]
    today = datetime.now(timezone.utc).date().isoformat()
    upcoming = lambda group: [b for b in group if (b.get('fecha_publicacion') or '') >= today]
    sections = {
        'portadas_tipograficas': {'total': len(typographic), 'proximos': len(upcoming(typographic)),
                                  'por_mes': by_month(typographic),
                                  'muestra': [entry(b, fuente=b.get('portada_fuente_url', '')) for b in typographic[:SAMPLE]]},
        'formatos_sin_precio': {'total': len(no_price), 'libros': len({b['id'] for b, _ in no_price}),
                                'por_formato': dict(Counter(f.get('formato') for _, f in no_price).most_common()),
                                'muestra': [entry(b, formato=f.get('formato'), url=f.get('url')) for b, f in no_price[:SAMPLE]]},
        'sin_formatos_de_compra': {'total': len(no_formats), 'muestra': [entry(b) for b in no_formats[:SAMPLE]]},
        'sin_texto': {'total': len(no_text), 'proximos': len(upcoming(no_text)), 'por_mes': by_month(no_text),
                      'muestra': [entry(b) for b in no_text[:SAMPLE]]},
        'portada_sin_fichero': {'total': len(missing_files), 'muestra': [entry(b, portada=b['portada_local']) for b in missing_files[:SAMPLE]]},
    }
    return books, typographic, sections


def ask_amazon(typographic, client, budget, today):
    """Para las tipográficas más cercanas a hoy: ¿tiene Amazon la cubierta? Solo lectura, no cambia nada."""
    from reading_amazon_market import item_cover_url
    order = sorted(typographic, key=lambda b: abs((datetime.fromisoformat((b.get('fecha_publicacion') or '1900-01-01')[:10]).date() - today).days))
    found, missing, errors = [], [], Counter()
    for book in order[:budget]:
        try:
            url = item_cover_url(book, client(book))
        except Exception as exc:  # noqa: BLE001 - el informe sigue con lo que haya
            errors[type(exc).__name__ + ': ' + str(exc)[:60]] += 1
            if 'eligibility' in str(exc):
                break
            continue
        (found if url else missing).append(entry(book, portada_amazon=url) if url else entry(book))
    return {'consultados': len(found) + len(missing), 'amazon_la_tiene': len(found), 'amazon_no_la_tiene': len(missing),
            'errores': dict(errors), 'oportunidades': found[:SAMPLE], 'sin_portada_en_amazon': missing[:SAMPLE]}


def compare(sections, previous):
    """Diferencia con el informe anterior: lo que empeora es lo primero que hay que mirar."""
    old = (previous or {}).get('secciones') or {}
    return {k: v['total'] - old[k]['total'] for k, v in sections.items() if k in old and isinstance(old[k], dict) and 'total' in old[k]}


LABELS = {'portadas_tipograficas': 'Portadas tipográficas (sin la oficial)', 'formatos_sin_precio': 'Formatos sin precio',
          'sin_formatos_de_compra': 'Libros sin formato de compra', 'sin_texto': 'Libros sin sinopsis ni texto propio',
          'portada_sin_fichero': 'Portadas que faltan en disco'}


def markdown(report):
    lines = [f"### Salud del catálogo · {report['generado'][:16].replace('T', ' ')} UTC",
             f"{report['publicados']} libros publicados. Solo informa: no bloquea la publicación.", '',
             '| Comprobación | Total | Próximos | Cambio |', '|---|---:|---:|---:|']
    for key, label in LABELS.items():
        s = report['secciones'][key]
        delta = report['cambio'].get(key)
        lines.append(f"| {label} | {s['total']} | {s.get('proximos', '')} | {'' if delta is None else f'{delta:+d}'} |")
    amazon = report.get('amazon')
    if amazon:
        lines += ['', f"**Portadas en Amazon:** {amazon['consultados']} consultadas; Amazon tiene {amazon['amazon_la_tiene']} "
                      f"(el barrido las cambiará) y no tiene {amazon['amazon_no_la_tiene']}."]
        if amazon['errores']:
            lines.append('Errores: ' + ', '.join(f'{k} ×{v}' for k, v in amazon['errores'].items()))
    fmt = report['secciones']['formatos_sin_precio']['por_formato']
    if fmt:
        lines += ['', 'Sin precio por formato: ' + ', '.join(f'{k} {v}' for k, v in fmt.items())]
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--amazon', type=int, default=0, help='portadas tipográficas por las que preguntar a la Creators API')
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args(argv)
    root = args.root
    catalogue = json.loads((root / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    books, typographic, sections = check(catalogue, root)
    out = root / '.ci/salud-catalogo'
    # La copia en .local/catalogo viaja de una noche a otra en la rama catalogo-estado (catalogo_estado.FILES);
    # .ci/ no sobrevive entre ejecuciones de Actions.
    kept = root / '.local/catalogo/salud.json'
    previous_path = next((p for p in (kept, out / 'informe.json') if p.exists()), None)
    try:
        previous = json.loads(previous_path.read_text(encoding='utf-8')) if previous_path else None
    except ValueError:
        previous = None
    report = {'generado': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'publicados': len(books),
              'secciones': sections, 'cambio': compare(sections, previous)}
    if args.amazon and typographic:
        client_id = os.getenv('AMAZON_CREATORS_CLIENT_ID', '').strip()
        secret = os.getenv('AMAZON_CREATORS_CLIENT_SECRET', '').strip()
        if client_id and secret:
            from reading_amazon_market import CreatorsPrices
            tag = json.loads((root / 'data/reading-intake-config.json').read_text(encoding='utf-8'))['amazon_partner_tag']
            report['amazon'] = ask_amazon(typographic, CreatorsPrices(client_id, secret, tag), args.amazon, datetime.now(timezone.utc).date())
        else:
            report['amazon'] = {'consultados': 0, 'amazon_la_tiene': 0, 'amazon_no_la_tiene': 0,
                                'errores': {'sin credenciales de la Creators API': 1}, 'oportunidades': [], 'sin_portada_en_amazon': []}
    data = json.dumps(report, ensure_ascii=False, indent=1) + '\n'
    for path in (out / 'informe.json', kept):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding='utf-8')
    text = markdown(report)
    (out / 'resumen.md').write_text(text, encoding='utf-8')
    summary = os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as handle:
            handle.write(text)
    print(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
