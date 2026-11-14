#!/usr/bin/env python3
"""¿Está en la web todo lo que sale hoy, mañana y pasado?

Fuente independiente de la carga: los listados por fecha de todostuslibros (CEGAL, libros en castellano), los
mismos que siembran la cola. De cada libro con fecha en [hoy, hoy+dias] dice si está en el catálogo y, si no,
dónde está y por qué (estado de la rama `catalogo-estado`): en la cola de semillas esperando a Amazon,
pendiente de algún dato, aplazado por el cupo de altas, descartado («Amazon no lo tiene»…), o sin explicar.

    python scripts/cobertura_cercana.py [--dia AAAA-MM-DD] [--dias 2] [--salida .ci/reading-intake/cobertura-cercana.json]

Solo lee: ni toca el catálogo ni la cola. Los listados no traen la fecha de cada tarjeta: se lee la de la última
de cada página (si cae dentro, la página entera cae dentro) y solo en la página frontera se abre ficha a ficha.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from catalogo_amazon import TTL_CARD_LINK, TTL_CATEGORIES, isbn10, isbn13, ttl_listing_url  # noqa: E402
from reading_ttl_source import ttl_publication_date  # noqa: E402

LINK_ISBN = re.compile(r'_([\d-]{13,17})$')
MAX_PAGINAS = 15  # por listado; hoy+2 cabe de sobra en las primeras páginas


def get(url, pausa):
    if pausa:
        time.sleep(pausa)  # una petición por segundo, como la carga
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; catalogo-lecturas/1.0)'})
    with urlopen(request, timeout=30) as response:
        return response.read().decode('utf-8', errors='replace')


def tarjetas(document):
    """[(isbn13, enlace)] de una página de listado, en su orden."""
    salida = []
    for link in dict.fromkeys(TTL_CARD_LINK.findall(document or '')):
        match = LINK_ISBN.search(link)
        isbn = isbn13(match.group(1).replace('-', '')) if match else None
        if isbn:
            salida.append((isbn, link))
    return salida


def leer_listado(fetch, categoria, modo, orden, desde, hasta):
    """{isbn: fecha} de un listado ordenado por fecha, solo lo que cae en [desde, hasta]."""
    dentro, anterior = {}, None
    for pagina in range(1, MAX_PAGINAS + 1):
        cartas = tarjetas(fetch(ttl_listing_url(categoria, modo, orden, pagina)))
        if not cartas or cartas == anterior:
            break
        anterior = cartas
        ultima = ttl_publication_date(fetch(cartas[-1][1]) or '')
        if ultima and desde <= ultima <= hasta:
            dentro.update((isbn, None) for isbn, _ in cartas[:-1])
            dentro[cartas[-1][0]] = ultima
            continue
        # Página frontera (o sin fecha legible en la última): ficha a ficha.
        for isbn, link in cartas:
            fecha = ttl_publication_date(fetch(link) or '')
            if fecha and desde <= fecha <= hasta:
                dentro[isbn] = fecha
        break
    return dentro


def estado_rama(ref):
    """Cola, pendientes y descartados de la rama de estado; vacío si no se puede leer."""
    def show(path):
        out = subprocess.run(['git', 'show', f'{ref}:{path}'], cwd=ROOT, capture_output=True)
        return out.stdout.decode('utf-8', errors='replace') if out.returncode == 0 else ''
    semillas = json.loads(show('semillas.json') or '{}').get('cola', {})
    pendientes = json.loads(show('pendientes.json') or '{}')
    descartados = {}
    for line in show('descartados.jsonl').splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        descartados[row.get('isbn13') or row.get('asin')] = row.get('motivo', '')
    return semillas, pendientes, descartados


def clasificar(isbn, publicados, semillas, pendientes, descartados, dia):
    if isbn in publicados:
        return 'en_la_web', ''
    asin = isbn10(isbn) if isbn.startswith('978') else None
    if isbn in descartados or (asin and asin in descartados):
        return 'descartado', descartados.get(isbn) or descartados.get(asin)
    if asin and asin in pendientes:
        motivo = pendientes[asin].get('motivo', '')
        return ('aplazado_por_cupo' if 'cupo' in motivo else 'pendiente_de_datos'), motivo
    if isbn in semillas:
        row = semillas[isbn]
        cuando = row.get('siguiente', dia)
        return 'en_cola', f"intentos {row.get('intentos', 0)}, siguiente {cuando}"
    return 'sin_explicar', ''


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    p.add_argument('--dia', default=datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat())
    p.add_argument('--dias', type=int, default=2)
    p.add_argument('--estado', default='origin/catalogo-estado')
    p.add_argument('--pausa', type=float, default=1.0)
    p.add_argument('--salida', default='.ci/reading-intake/cobertura-cercana.json')
    args = p.parse_args(argv)
    hoy = date.fromisoformat(args.dia)
    desde, hasta = hoy.isoformat(), (hoy + timedelta(days=args.dias)).isoformat()
    peticiones, errores = 0, []

    def fetch(url):
        nonlocal peticiones
        peticiones += 1
        try:
            return get(url, args.pausa if peticiones > 1 else 0)
        except (OSError, ValueError) as exc:
            errores.append(f'{url[-90:]}: {str(exc)[:80]}')
            return ''

    libros = {}
    for categoria in TTL_CATEGORIES:
        # «novedades» descendente empieza en hoy; «próximas» ascendente, en mañana.
        for modo, orden in (('novedades', 'desc'), ('proximas_apariciones', 'asc')):
            for isbn, fecha in leer_listado(fetch, categoria, modo, orden, desde, hasta).items():
                libros.setdefault(isbn, {'fecha': fecha, 'categoria': categoria})
                if fecha and not libros[isbn]['fecha']:
                    libros[isbn]['fecha'] = fecha
    catalogo = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    publicados = {b.get('isbn13') for b in catalogo.get('libros', [])}
    semillas, pendientes, descartados = estado_rama(args.estado)
    detalle = []
    for isbn, info in sorted(libros.items()):
        situacion, motivo = clasificar(isbn, publicados, semillas, pendientes, descartados, args.dia)
        detalle.append({'isbn13': isbn, **info, 'situacion': situacion, 'motivo': motivo})
    cuenta = Counter(d['situacion'] for d in detalle)
    informe = {'dia': args.dia, 'ventana': [desde, hasta], 'libros': len(detalle), 'situacion': dict(cuenta),
               'cobertura': round(cuenta['en_la_web'] / len(detalle), 3) if detalle else None,
               'motivos_fuera': dict(Counter(d['motivo'] for d in detalle if d['situacion'] != 'en_la_web').most_common(10)),
               'peticiones': peticiones, 'errores': errores[-5:],
               'fuera': [d for d in detalle if d['situacion'] != 'en_la_web']}
    salida = ROOT / args.salida
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    resumen = {k: v for k, v in informe.items() if k != 'fuera'}
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
