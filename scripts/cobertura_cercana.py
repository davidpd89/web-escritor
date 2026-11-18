#!/usr/bin/env python3
"""¿Está en la web todo lo que sale hoy, mañana y pasado?

Fuente independiente de la carga: los listados por fecha de todostuslibros (CEGAL, libros en castellano), los
mismos que siembran la cola. De cada libro con fecha en [hoy, hoy+dias] dice si está en el catálogo y, si no,
dónde está y por qué (estado de la rama `catalogo-estado`): en la cola de semillas esperando a Amazon,
pendiente de algún dato, aplazado por el cupo de altas, descartado («Amazon no lo tiene»…), o sin explicar.

    python scripts/cobertura_cercana.py [--dia AAAA-MM-DD] [--dias 2] [--salida .ci/reading-intake/cobertura-cercana.json]

Solo lee: ni toca el catálogo ni la cola. Los listados no traen la fecha de cada tarjeta: se lee la de la última
de cada página (si cae dentro, la página entera cae dentro) y en la página frontera se busca el corte por
bisección (unas 10 fichas en vez de 30); solo si alguna fecha no se lee se abre ficha a ficha.

Tiene presupuesto (peticiones, minutos y errores seguidos de la fuente) y va por rondas: la página 1 de todos los
listados antes que la 2 de ninguno. Si el presupuesto se agota escribe igualmente el informe, con
`completo: false` y los listados que quedaron a medias; solo falla si no llegó a dar la primera ronda entera.
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

from catalogo_amazon import MOTIVO_CUPO, TTL_CARD_LINK, TTL_CATEGORIES, isbn10, isbn13, ttl_listing_url  # noqa: E402
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


class SinPresupuesto(Exception):
    """Se acabó lo que este recorrido puede gastar; el mensaje dice qué."""


class Presupuesto:
    """Reparte las peticiones: tope de peticiones, de tiempo y de errores seguidos (fuente caída o que bloquea)."""

    def __init__(self, get, max_peticiones, segundos, max_errores_seguidos=8, reloj=time.monotonic):
        self.get, self.max_peticiones, self.segundos = get, max_peticiones, segundos
        self.max_errores_seguidos, self.reloj, self.inicio = max_errores_seguidos, reloj, reloj()
        self.peticiones, self.seguidos, self.errores = 0, 0, []

    def fetch(self, url):
        if self.seguidos >= self.max_errores_seguidos:
            raise SinPresupuesto(f'la fuente falló {self.seguidos} veces seguidas')
        if self.peticiones >= self.max_peticiones:
            raise SinPresupuesto(f'tope de {self.max_peticiones} peticiones')
        if self.reloj() - self.inicio >= self.segundos:
            raise SinPresupuesto(f'tope de {round(self.segundos / 60)} minutos')
        self.peticiones += 1
        try:
            documento = self.get(url)
        except (OSError, ValueError) as exc:
            self.seguidos += 1
            self.errores.append(f'{url[-90:]}: {str(exc)[:80]}')
            return ''
        self.seguidos = 0
        return documento


def tramo_dentro(n, fecha_de, desde, hasta):
    """(a, b) tal que las posiciones [a, b) de una lista de n fechas ascendentes caen en [desde, hasta], por
    bisección. None si alguna fecha consultada no se lee: sin ella no se puede partir."""
    def primera(cumple):
        lo, hi = 0, n
        while lo < hi:
            medio = (lo + hi) // 2
            fecha = fecha_de(medio)
            if not fecha:
                raise LookupError(medio)
            lo, hi = (lo, medio) if cumple(fecha) else (medio + 1, hi)
        return lo
    try:
        return primera(lambda f: f >= desde), primera(lambda f: f > hasta)
    except LookupError:
        return None


def recorrer(fetch, categoria, modo, orden, desde, hasta, dentro):
    """Va llenando `dentro` ({isbn: fecha} de lo que cae en [desde, hasta]) y cede el turno tras cada página."""
    anterior = None
    for pagina in range(1, MAX_PAGINAS + 1):
        cartas = tarjetas(fetch(ttl_listing_url(categoria, modo, orden, pagina)))
        if not cartas or cartas == anterior:
            break
        anterior = cartas
        # La página entera cae dentro solo si sus dos extremos caen dentro (el listado está ordenado por fecha).
        ultima = ttl_publication_date(fetch(cartas[-1][1]) or '')
        primera = ultima if len(cartas) == 1 else ttl_publication_date(fetch(cartas[0][1]) or '')
        if ultima and primera and all(desde <= f <= hasta for f in (primera, ultima)):
            dentro.update((isbn, None) for isbn, _ in cartas[:-1])
            dentro[cartas[-1][0]] = ultima
            yield pagina
            continue
        # Página frontera: el corte se busca por bisección sobre la página puesta en orden ascendente.
        asc = cartas if orden == 'asc' else cartas[::-1]
        fechas = {0 if orden == 'asc' else len(asc) - 1: primera, len(asc) - 1 if orden == 'asc' else 0: ultima}

        def fecha_de(i):
            if i not in fechas:
                fechas[i] = ttl_publication_date(fetch(asc[i][1]) or '')
            return fechas[i]
        tramo = tramo_dentro(len(asc), fecha_de, desde, hasta)
        if tramo:
            dentro.update((asc[i][0], fechas.get(i)) for i in range(*tramo))
        else:  # alguna fecha ilegible: ficha a ficha, aprovechando las ya leídas
            dentro.update((asc[i][0], fecha_de(i)) for i in range(len(asc)) if desde <= (fecha_de(i) or '') <= hasta)
        break


def leer_listado(fetch, categoria, modo, orden, desde, hasta):
    """{isbn: fecha} de un listado ordenado por fecha, solo lo que cae en [desde, hasta]."""
    dentro = {}
    for _ in recorrer(fetch, categoria, modo, orden, desde, hasta, dentro):
        pass
    return dentro


def recoger(fetch, listados, desde, hasta, aviso=lambda _texto: None):
    """Recorre los listados [(categoria, modo, orden)] por rondas. Devuelve (libros, a_medias, rondas, motivo):
    `a_medias` son los listados sin terminar y `motivo` por qué se paró («» si terminó todo)."""
    hallado = {(c, m): {} for c, m, _ in listados}
    vivos = {(c, m): recorrer(fetch, c, m, o, desde, hasta, hallado[c, m]) for c, m, o in listados}
    rondas, motivo = 0, ''
    try:
        while vivos:
            for clave in list(vivos):
                if next(vivos[clave], None) is None:
                    del vivos[clave]
            rondas += 1
            aviso(f'ronda {rondas}: quedan {len(vivos)} listados, {sum(map(len, hallado.values()))} libros')
    except SinPresupuesto as exc:
        motivo = str(exc)
    libros = {}
    for (categoria, _modo), dentro in hallado.items():
        for isbn, fecha in dentro.items():
            libros.setdefault(isbn, {'fecha': fecha, 'categoria': categoria})
            if fecha and not libros[isbn]['fecha']:
                libros[isbn]['fecha'] = fecha
    return libros, [f'{c}/{m}' for c, m in vivos], rondas, motivo


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


def pendientes_por_isbn(pendientes):
    """La cola por ASIN, también por ISBN-13 cuando la fila lo lleva (un 979 no se deduce de su ASIN B0…)."""
    return {**pendientes, **{row['isbn13']: row for row in pendientes.values() if row.get('isbn13')}}


def clasificar(isbn, publicados, semillas, pendientes, descartados, dia, cuarentena=None):
    if isbn in publicados:
        return 'en_la_web', ''
    if cuarentena and isbn in cuarentena:
        return 'en_cuarentena', cuarentena[isbn]
    asin = isbn10(isbn) if isbn.startswith('978') else None
    # Lo activo antes que lo histórico: un descartado que volvió a la cola cuenta como pendiente.
    clave = isbn if isbn in pendientes else asin
    if clave and clave in pendientes:
        motivo = pendientes[clave].get('motivo', '')
        return ('aplazado_por_cupo' if motivo == MOTIVO_CUPO else 'pendiente_de_datos'), motivo
    if isbn in descartados or (asin and asin in descartados):
        return 'descartado', descartados.get(isbn) or descartados.get(asin)
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
    p.add_argument('--max-peticiones', type=int, default=1500)
    p.add_argument('--minutos', type=float, default=35, help='tope de tiempo del recorrido; el informe sale igual')
    p.add_argument('--salida', default='.ci/reading-intake/cobertura-cercana.json')
    args = p.parse_args(argv)
    hoy = date.fromisoformat(args.dia)
    desde, hasta = hoy.isoformat(), (hoy + timedelta(days=args.dias)).isoformat()
    presupuesto = Presupuesto(lambda url: get(url, args.pausa if presupuesto.peticiones > 1 else 0),
                              args.max_peticiones, args.minutos * 60)
    # «novedades» descendente empieza en hoy; «próximas» ascendente, en mañana.
    listados = [(categoria, modo, orden) for categoria in TTL_CATEGORIES
                for modo, orden in (('novedades', 'desc'), ('proximas_apariciones', 'asc'))]
    libros, a_medias, rondas, motivo = recoger(presupuesto.fetch, listados, desde, hasta,
                                               lambda texto: print(texto, file=sys.stderr, flush=True))
    catalogo = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    publicados = {b.get('isbn13') for b in catalogo.get('libros', [])}
    semillas, pendientes, descartados = estado_rama(args.estado)
    pendientes = pendientes_por_isbn(pendientes)
    cuarentena = {h.get('isbn'): h.get('causa') or h.get('motivo', '') for h in json.loads(
        (ROOT / 'data/reading-quarantine.json').read_text(encoding='utf-8')).get('libros', []) if h.get('isbn')}
    detalle = []
    for isbn, info in sorted(libros.items()):
        situacion, causa = clasificar(isbn, publicados, semillas, pendientes, descartados, args.dia, cuarentena)
        detalle.append({'isbn13': isbn, **info, 'situacion': situacion, 'motivo': causa})
    cuenta = Counter(d['situacion'] for d in detalle)
    informe = {'dia': args.dia, 'ventana': [desde, hasta], 'libros': len(detalle), 'situacion': dict(cuenta),
               'cobertura': round(cuenta['en_la_web'] / len(detalle), 3) if detalle else None,
               'motivos_fuera': dict(Counter(d['motivo'] for d in detalle if d['situacion'] != 'en_la_web').most_common(10)),
               'completo': not a_medias, 'parado_por': motivo, 'rondas': rondas, 'listados_a_medias': a_medias,
               'peticiones': presupuesto.peticiones, 'errores': presupuesto.errores[-5:],
               'fuera': [d for d in detalle if d['situacion'] != 'en_la_web']}
    salida = ROOT / args.salida
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    resumen = {k: v for k, v in informe.items() if k != 'fuera'}
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    if a_medias and not rondas:
        print(f'::error::Cobertura sin primera ronda completa ({motivo}): el informe no sirve.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
