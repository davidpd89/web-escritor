#!/usr/bin/env python3
"""Catálogo desde Amazon, en local: descargar → transformar → aplicar (cuarentena) → informe.

    python scripts/catalogo_amazon.py descargar [--peticiones 1500] [--profundidad 3]
    python scripts/catalogo_amazon.py transformar
    python scripts/catalogo_amazon.py aplicar
    python scripts/catalogo_amazon.py revisar       # foto de la BD y comparación con la anterior
    python scripts/catalogo_amazon.py todo          # las cuatro, una detrás de otra

Credenciales: AMAZON_CREATORS_CLIENT_ID / AMAZON_CREATORS_CLIENT_SECRET del entorno o de
`.env.local` (ignorado por git; se busca en este checkout y en el principal).

Nada se rechaza a ciegas: cada libro que no entra queda en `.local/catalogo/fallos.json` con su
motivo, agrupado, para corregir el MÉTODO (no el libro). La subida (commit/PR) es la última
comprobación, no la primera.

Los huecos que Amazon rellena más tarde (editorial, fecha, autoría…) no tiran el libro: van a
`.local/catalogo/pendientes.json` y la descarga de los días siguientes los vuelve a pedir con getItems.
Si tras el último reintento siguen sin llegar, pasan a `descartados.jsonl`.

Los sellos grandes (Planeta, Random House…) llenan los 100 resultados de una búsqueda con preventas de
dentro de un año y nunca llegan a las novedades del mes. Por eso las altas también se descubren por ISBN:
el sitemap de todostuslibros (CEGAL) trae miles de fichas recientes al día y Amazon acepta hasta 10 ISBN
por búsqueda separados por «|» (`semillas_ttl` → `por_isbn`, cola en `.local/catalogo/semillas.json`).

`revisar` guarda una foto de los campos de cada libro publicado y la compara con la anterior: los
campos vaciados o los libros desaparecidos son regresión (código de salida 1).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from reading_amazon_market import (BINDINGS, CreatorsPrices, NotFound, amazon_dict, amazon_list,  # noqa: E402
                                   select_offers, store_prices)
from reading_amazon_radar import BOOKS_NODE, SPANISH  # noqa: E402
from reading_ratings_refresh import isbn13, key  # noqa: E402

WORK = ROOT / '.local/catalogo'
SEARCH = 'https://creatorsapi.amazon/catalog/v1/searchItems'
NODES = 'https://creatorsapi.amazon/catalog/v1/getBrowseNodes'
ITEMS = 'https://creatorsapi.amazon/catalog/v1/getItems'
# Los hijos directos de Libros (599364031) son nodos técnicos («Shops», «Búsqueda avanzada»…); las materias
# de verdad cuelgan de «Categorías». Comprobado con la API real el 2026-11-06 (31 categorías).
CATEGORIES_NODE = '599365031'
# Categorías que no son lectura para el catálogo: se ahorran sus peticiones.
SKIP_NODES = {'calendarios y agendas', 'libros de texto', 'guias de estudio y repaso',
              'libros universitarios y de estudios superiores'}
RESOURCES = ['itemInfo.title', 'itemInfo.byLineInfo', 'itemInfo.contentInfo', 'itemInfo.classifications',
             'itemInfo.externalIds', 'browseNodeInfo.browseNodes',
             # Ancestros: «Paranormal» o «Militar» solos son ambiguos; con su rama (Juvenil > Novelas románticas)
             # no. Ranking de ventas para ordenar el fondo; productInfo trae releaseDate cuando falta publicationDate.
             'browseNodeInfo.browseNodes.ancestor', 'browseNodeInfo.websiteSalesRank', 'itemInfo.productInfo',
             'offersV2.listings.price', 'offersV2.listings.condition', 'offersV2.listings.availability',
             'offersV2.listings.dealDetails', 'offersV2.listings.type']
# Nodos que no dicen nada del libro: no son materia.
GENERIC_NODES = {'libros', 'categorias', 'books', 'tienda kindle', 'ebooks kindle', 'literatura y ficcion',
                 'libros en espanol', 'libros en idiomas extranjeros', 'novedades', 'mas vendidos',
                 # Raíces internas de Amazon: salían en los 113 libros sin materia de la tanda de semillas del 2026-11-06.
                 'special features stores', 'self service', 'arborist merchandising root', 'featured categories',
                 # Literaturas por región: dicen de dónde es el autor, no qué se lee; deciden los nodos hermanos.
                 'literatura britanica e irlandesa', 'literatura europea', 'literatura mundial',
                 'britanica e irlandesa', 'europea'}
# Nodos de escaparate de Amazon (idioma, formato, tienda de un sello…): ocupaban las tres plazas de materia
# y acababan como «temas» del catálogo («Libros en castellano» en 2258 de 4551 candidatos).
STORE_NODES = re.compile(r'^(?:libros en (?:castellano|espanol|ingles|catalan|gallego|euskera|valenciano|frances|'
                         r'aleman|italiano|portugues|otros idiomas|idiomas extranjeros)$|'
                         r'libros (?:excepto|fisicos|estructurados)\b|tienda\b|ficcion por genero$|'
                         r'(?:no )?ficcion$|consulta$|dia de las librerias$|promocion\b|botiga\b|'
                         r'(?:espanol|ingles|catalan|frances|aleman|italiano|portugues)$|regular stores$|'
                         r'[0-9a-f]{8} [0-9a-f]{4} [0-9a-f]{4} )')  # nodos internos con nombre de UUID
# Nodos que solo se entienden con su padre.
NODE_ALIASES = {'literaria': 'Ficción literaria'}
# Taxonomía cerrada: un nodo de Amazon solo da materia si está aquí. El valor es una materia que el catálogo ya
# clasifica (GENRES del pipeline) o un tema fijo («Religión y espiritualidad» → tema-religion-y-espiritualidad).
# El resto de nodos van a palabras clave: las reglas de reading_taxonomy pueden añadir sus categorías cerradas,
# pero ningún nodo nuevo crea una página «tema-» (431 temas finos por 1000 libros, medido el 2026-11-06).
AMAZON_SUBJECTS = {
    'Narrativa contemporánea': ['ficcion contemporanea', 'ficcion literaria', 'novelas y ficcion literaria',
                                'mujer contemporanea', 'ficcion femenina', 'saga familiar', 'multigeneracional',
                                'biografico y autoficcion'],
    'Aventuras': ['accion y aventura', 'accion y aventuras'],
    'Fantasía': ['fantasia', 'fantasia oscura', 'fantasia epica', 'dragones y criaturas miticas', 'magos y brujas',
                 'dragones, unicornios y criaturas mitologicas'],
    'Cómic y novela gráfica': ['comics y novelas graficas', 'comics, manga y novelas graficas', 'manga', 'shonen',
                               'shojo', 'seinen', 'superheroes', 'como crear comics y manga'],
    'Biografías y memorias': ['hechos reales', 'biografias y autobiografias', 'biografias, diarios y hechos reales', 'diarios y cartas',
                              'actores y artistas'],
    'Poesía': ['poesia'],
    'Filosofía': ['filosofia', 'etica'],
    'Historia': ['arqueologia', 'historia', 'historia del siglo xx y xxi', 'edad moderna hasta el siglo xx', 'historia social y cultural',
                 'antigua y clasica', 'antiguedad', 'historia militar'],
    'Psicología': ['psicologia', 'neurociencia'],
    'Novela histórica': ['novela historica', 'ficcion historica', 'historico'],
    'Ensayo': ['sociedad y ciencias sociales', 'sociedad y cultura', 'ensayos', 'ensayos y correspondencia', 'historia, teoria literaria y critica', 'historia y critica',
               'periodismo', 'sociologia', 'estudios de genero', 'estudios de medios',
               'lengua, linguistica y redaccion', 'linguistica', 'gramatica', 'retorica y oratoria',
               'enciclopedias y obras de consulta'],
    'Clásicos': ['ficcion clasica', 'clasicos'],
    'Misterio': ['novela negra', 'misterio', 'thrillers policiacos', 'thriller y suspense', 'thrillers psicologicos', 'suspense',
                 'misterio, thriller y suspense', 'misterios y detectives', 'detectives amateurs', 'investigadores privados'],
    'Terror': ['terror', 'fantasmas', 'monstruos'],
    'Romance': ['romance', 'romantica', 'romantico', 'novelas romanticas', 'novelas de amor contemporaneas', 'comedia romantica',
                'romance oscuro'],
    'Ciencia ficción': ['ciencia ficcion'],
    'Relatos': ['colecciones de cuentos cortos', 'relatos breves', 'historias cortas', 'antologias'],
    'Cocina': ['cocina, bebida y hospitalidad', 'cocina'],
    'Autoayuda': ['desarrollo personal y autoayuda', 'autoestima y amor propio', 'emociones y sentimientos'],
    'Familia y crianza': ['familia y relaciones', 'vida familiar', 'para padres'],
    'Salud': ['bienestar y vida sana', 'medicina preventiva', 'salud publica', 'medicina alternativa',
              'salud, familia y desarrollo personal'],
    'Economía': ['empresa, estrategia y gestion', 'economia', 'industria y sectores economicos'],
    'Ciencia': ['ciencias de la tierra', 'biologia', 'ciencias, tecnologia y medicina', 'ciencias informaticas'],
    'Tiempo libre': ['deportes y aire libre', 'baloncesto', 'hogar, manualidades y estilos de vida', 'artesania, artes decorativas y manualidades',
                     'juegos y adivinanzas', 'libros para colorear', 'libros para colorear para adultos', 'futbol'],
    'Religión y espiritualidad': ['cristianismo', 'religion', 'teologia y filosofia de la religion'],
    'Derecho': ['derecho internacional', 'derecho', 'jurisprudencia', 'derecho publico', 'derecho privado', 'procesos y practica legal'],
    'Poder y política': ['politica', 'estructuras y procesos politicos', 'ideologias politicas', 'teoria politica',
                         'relaciones internacionales y globalizacion', 'libertad y seguridad'],
    'Viajes': ['guias turisticas', 'literatura de viaje'],
    'Arte y diseño': ['arte y fotografia', 'fotografia y video', 'pintura', 'arquitectura', 'dibujo', 'grafitis y arte callejero', 'diseno y moda', 'ilustracion', 'musica', 'artes escenicas', 'teatro'],
    'Infantil': ['infantil'],
    'Novela juvenil': ['juvenil'],
}
SUBJECT_OF_NODE = {key(node): subject for subject, nodes in AMAZON_SUBJECTS.items() for node in nodes}
# Encuadernaciones de papel que el mapa común no conoce: el libro de cartón infantil (79 en la descarga del
# 2026-11-06), el de tela, el de espiral y el grapado se compran igual que una tapa dura o blanda. «Libro» a secas
# no dice el formato y sigue fuera; los libros de texto también (no son lectura del portal).
PRINT_BINDINGS = {'libro de carton': 'tapa-dura', 'libro de tela': 'tapa-dura',
                  'encuadernacion en espiral': 'tapa-blanda', 'grapado': 'tapa-blanda'}
AUTHOR_ROLES = {'autor', 'author', 'autora'}
COVER_BASIS = 'Portada tipográfica propia generada con los datos bibliográficos; no reproduce la cubierta editorial'
EDITION_PREFERENCE = ['tapa-blanda', 'tapa-dura', 'ebook', 'audiolibro']
# Huecos que Amazon suele rellenar días después del alta (sobre todo en «próximamente»): el libro no se
# descarta, se vuelve a pedir con getItems a 1, 2, 4, 8, 16 y 30 días hasta que llega el campo.
RETRYABLE = ('sin materia', 'sin título', 'sin autoría', 'sin editorial', 'sin fecha de publicación', 'encuadernación: vacía',
             'sin idioma y con ISBN extranjero')
RETRY_DAYS = (1, 2, 4, 8, 16, 30)


# ---------------------------------------------------------------- entorno

def load_env():
    """Lee .env.local (este checkout o el principal) sin pisar lo que ya trae el entorno."""
    candidates = [ROOT / '.env.local']
    try:
        common = subprocess.run(['git', 'rev-parse', '--git-common-dir'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        candidates.append((ROOT / common).resolve().parent / '.env.local')
    except (OSError, subprocess.CalledProcessError):
        pass
    for path in candidates:
        if not path.is_file():
            continue
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            match = re.match(r'\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=\s*(.*)$', line)
            if match and match.group(1) not in os.environ:
                os.environ[match.group(1)] = match.group(2).strip().strip('"').strip("'")


def provider(tag):
    load_env()
    client, secret = (os.getenv(k, '').strip() for k in ('AMAZON_CREATORS_CLIENT_ID', 'AMAZON_CREATORS_CLIENT_SECRET'))
    if not client or not secret:
        raise SystemExit('Faltan AMAZON_CREATORS_CLIENT_ID / AMAZON_CREATORS_CLIENT_SECRET en el entorno o en .env.local')
    return CreatorsPrices(client, secret, tag)


def read_json(path, default=None):
    return json.loads(Path(path).read_text(encoding='utf-8')) if Path(path).exists() else default


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def config():
    cfg = read_json(ROOT / 'data/reading-intake-config.json')
    return cfg['amazon_partner_tag'], cfg.get('amazon_catalogo', {})


# ---------------------------------------------------------------- 1. descargar

def search(prov, tag, node, page):
    return prov.post(SEARCH, {'marketplace': 'www.amazon.es', 'partnerTag': tag, 'searchIndex': 'Books',
                              'browseNodeId': node, 'sortBy': 'NewestArrivals', 'itemCount': 10, 'itemPage': page,
                              'availability': 'IncludeOutOfStock', 'condition': 'New', 'currencyOfPreference': 'EUR', 'resources': RESOURCES}, prov.headers())


def node_children(prov, tag, node):
    payload = prov.post(NODES, {'marketplace': 'www.amazon.es', 'partnerTag': tag, 'browseNodeIds': [node],
                                'resources': ['browseNodes.children']}, prov.headers())
    result = amazon_dict(payload.get('browseNodesResult') or payload.get('browseNodeResult'))
    out = []
    for item in amazon_list(result.get('browseNodes')):
        for child in amazon_list(amazon_dict(item).get('children')):
            child = amazon_dict(child)
            ident = str(child.get('id', ''))
            if re.fullmatch(r'\d+', ident):
                out.append((ident, child.get('displayName') or child.get('contextFreeName') or ''))
    return out


def isbn10(isbn):
    """ISBN-13 978 → ISBN-10, que en Amazon es el ASIN del libro en papel. Los 979 no tienen."""
    if not (isbn and len(isbn) == 13 and isbn.startswith('978') and isbn.isdigit()):
        return None
    body = isbn[3:12]
    check = (11 - sum((10 - i) * int(d) for i, d in enumerate(body)) % 11) % 11
    return body + ('X' if check == 10 else str(check))


# ---------------------------------------------------------------- semillas por ISBN

def seeds_path():
    return WORK / 'semillas.json'


SPLIT_AFTER, DROP_AFTER = 2, 4  # errores seguidos de un lote: se pregunta suelto / se descarta


def semillas_ttl(get, day, known, files=2):
    """Altas nuevas del sitemap de todostuslibros → cola de semillas. Se recuerdan los ISBN de cada fichero
    leído (no una posición): si el sitemap se reordena o se reescribe, entra solo lo que no se había visto.
    Tampoco vuelve lo ya descartado."""
    from reading_ttl_source import LOC, SITEMAP_INDEX, sitemap_children, url_isbn
    state = read_json(seeds_path(), {})
    queue = state.setdefault('cola', {})
    state.pop('leidos', None)  # formato anterior (posición por fichero)
    seen = {i for isbns in state.get('vistos', {}).values() for i in isbns} | discarded_isbns()
    current, added = {}, 0
    for url in reversed(sitemap_children(get(SITEMAP_INDEX), files)):  # del más antiguo al más nuevo
        isbns = [i for i in (url_isbn(u) for u in LOC.findall(get(url))) if i]
        for isbn in isbns:
            if isbn not in known and isbn not in queue and isbn not in seen:
                queue[isbn] = {'primera': day, 'intentos': 0, 'siguiente': day, 'fuente': 'todostuslibros'}
                added += 1
        current[url] = sorted(set(isbns))
    state['vistos'] = current  # solo los ficheros vigentes: el estado no crece sin límite
    write_json(seeds_path(), state)
    return added


def discarded_isbns():
    if not discarded_path().exists():
        return set()
    out = set()
    for line in discarded_path().read_text(encoding='utf-8').splitlines():
        try:
            out.add(json.loads(line).get('isbn13'))
        except (ValueError, AttributeError):
            continue
    return out - {None}


def item_isbns(item):
    info = amazon_dict(amazon_dict(item).get('itemInfo'))
    values = amazon_list(amazon_dict(amazon_dict(info.get('externalIds')).get('eans')).get('displayValues'))
    return {isbn13(v) for v in values if isinstance(v, str)} - {None}


def seed_batches(due, queue):
    """Lotes de 10; lo que ya ha fallado varias veces va suelto para que un ISBN raro no arrastre a otros."""
    group = []
    for isbn in due:
        if queue[isbn].get('errores', 0) >= SPLIT_AFTER:
            yield [isbn]
            continue
        group.append(isbn)
        if len(group) == 10:
            yield group
            group = []
    if group:
        yield group


def discard_seed(queue, isbn, day, motivo):
    row = queue.pop(isbn)
    discarded_path().parent.mkdir(parents=True, exist_ok=True)
    with discarded_path().open('a', encoding='utf-8') as log:
        log.write(json.dumps({'isbn13': isbn, 'dia': day, 'motivo': motivo, 'primera': row['primera'],
                              'intentos': row['intentos'], 'errores': row.get('errores', 0)}, ensure_ascii=False) + '\n')


def por_isbn(prov, tag, day, out, budget):
    """Semillas que tocan hoy, de 10 en 10 («isbn|isbn|…» en una sola búsqueda). Solo cuentan (y pasan al raw)
    los resultados cuyo ISBN se pidió: otra edición no da por encontrada la semilla. Las que Amazon aún no
    tiene vuelven con el calendario de reintentos; agotado, se descartan con su motivo."""
    state = read_json(seeds_path(), {})
    queue = state.get('cola', {})
    due = sorted((row['primera'], isbn) for isbn, row in queue.items() if row.get('siguiente', '') <= day)
    due = [isbn for _, isbn in reversed(due)]  # las altas más recientes primero
    tomorrow = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
    used, found, foreign, failed = 0, set(), 0, 0
    for batch in seed_batches(due, queue):
        if used >= budget:
            break
        used += 1
        try:
            payload = prov.post(SEARCH, {'marketplace': 'www.amazon.es', 'partnerTag': tag, 'searchIndex': 'Books',
                                         'keywords': '|'.join(batch), 'itemCount': 10, 'availability': 'IncludeOutOfStock',
                                         'condition': 'New', 'currencyOfPreference': 'EUR', 'resources': RESOURCES}, prov.headers())
        except NotFound:
            payload = {}
        except RuntimeError as exc:
            if 'eligibility' in str(exc) or 'HTTP 401' in str(exc):
                raise
            failed += 1
            for isbn in batch:  # sin respuesta: no gasta reintentos, pero tras varios fallos va suelto y luego fuera
                queue[isbn]['errores'] = queue[isbn].get('errores', 0) + 1
                if queue[isbn]['errores'] >= DROP_AFTER:
                    discard_seed(queue, isbn, day, f'error de Amazon: {str(exc)[:80]}')
                else:
                    queue[isbn]['siguiente'] = tomorrow
            continue
        wanted, hits = set(batch), set()
        for item in amazon_list(amazon_dict(payload.get('searchResult')).get('items')):
            match = item_isbns(item) & wanted
            if not match:
                foreign += 1  # otra edición u otro libro: no entra por esta vía
                continue
            hits |= match
            out.write(json.dumps({'nodo': 'isbn', 'ruta': [], 'item': item}, ensure_ascii=False) + '\n')
        found |= hits
        for isbn in batch:
            if isbn in hits:
                queue.pop(isbn, None)  # desde aquí lo sigue el flujo normal (por ASIN)
                continue
            row = queue[isbn]
            row['intentos'] += 1
            row.pop('errores', None)
            if row['intentos'] > len(RETRY_DAYS):
                row['intentos'] -= 1
                discard_seed(queue, isbn, day, 'Amazon no lo tiene')
            else:
                row['siguiente'] = (date.fromisoformat(day) + timedelta(days=RETRY_DAYS[row['intentos'] - 1])).isoformat()
    write_json(seeds_path(), state)
    return {'peticiones': used, 'debidas': len(due), 'encontradas': len(found), 'ajenos': foreign,
            'lotes_fallidos': failed, 'en_cola': len(queue)}


def enlaces_path(day):
    return WORK / f'enlaces-{day}.json'


def pending_path():
    return WORK / 'pendientes.json'


def discarded_path():
    return WORK / 'descartados.jsonl'


def schedule(pending, asin, day, motivo):
    """Un intento más a 1/2/4/8/16/30 días; agotados, el libro sale de la cola y queda anotado."""
    row = pending.get(asin) or {'primera': day, 'intentos': 0}
    if row.get('ultima') == day:
        return
    row['intentos'] += 1
    if row['intentos'] > len(RETRY_DAYS):
        pending.pop(asin, None)
        discarded_path().parent.mkdir(parents=True, exist_ok=True)
        with discarded_path().open('a', encoding='utf-8') as out:
            out.write(json.dumps({'asin': asin, 'dia': day, 'motivo': motivo, 'primera': row['primera'],
                                  'intentos': row['intentos'] - 1}, ensure_ascii=False) + '\n')
        return
    row |= {'motivo': motivo, 'ultima': day,
            'siguiente': (date.fromisoformat(day) + timedelta(days=RETRY_DAYS[row['intentos'] - 1])).isoformat()}
    pending[asin] = row


def update_pending(day, failures, resolved):
    """Apunta los libros con huecos reintentables y quita los que ya llegaron completos."""
    pending = read_json(pending_path(), {})
    for asin in resolved:
        pending.pop(asin, None)
    for f in failures:
        if f['motivo'].startswith(RETRYABLE) and f.get('asin'):
            schedule(pending, f['asin'], day, f['motivo'])
    write_json(pending_path(), pending)
    return pending


def reintentar(prov, tag, day, out, budget):
    """getItems de los pendientes que tocan hoy, de 10 en 10, al mismo raw que el recorrido."""
    due = sorted(a for a, row in read_json(pending_path(), {}).items() if row.get('siguiente', '') <= day)
    used, asked, got = 0, set(), set()
    for start in range(0, len(due), 10):
        if used >= budget:
            break
        used += 1
        try:
            payload = prov.post(ITEMS, {'marketplace': 'www.amazon.es', 'partnerTag': tag, 'condition': 'New',
                                        'currencyOfPreference': 'EUR', 'resources': RESOURCES,
                                        'itemIds': due[start:start + 10], 'itemIdType': 'ASIN'}, prov.headers())
        except NotFound:
            payload = {}
        except RuntimeError:
            continue
        result = amazon_dict(payload.get('itemsResult') or payload.get('itemResults'))
        for item in amazon_list(result.get('items')):
            got.add(amazon_dict(item).get('asin'))
            out.write(json.dumps({'nodo': 'pendiente', 'ruta': [], 'item': item}, ensure_ascii=False) + '\n')
        asked.update(due[start:start + 10])
    # Lo que Amazon ya no devuelve (retirado, ASIN inválido) no se pide cada día: avanza su calendario.
    if asked - got:
        pending = read_json(pending_path(), {})
        for asin in sorted(asked - got):
            schedule(pending, asin, day, 'getItems sin respuesta')
        write_json(pending_path(), pending)
    return used, len(due)


def descargar(prov, tag, day, max_requests=1500, max_depth=3, pages=10, root_node=BOOKS_NODE):
    """Recorre el árbol de Libros por NewestArrivals; un nodo que llena sus 10 páginas se parte en
    hijos. Todo lo leído va a raw/<día>.jsonl al momento: un corte no pierde nada y se reanuda."""
    raw = WORK / 'raw' / f'{day}.jsonl'
    checkpoint = WORK / 'raw' / f'{day}.estado.json'
    state = read_json(checkpoint) or {'pendientes': [[root_node, 0, ['Libros']]], 'vistos': [root_node],
                                      'peticiones': 0, 'nodos_leidos': 0, 'nodos_llenos': 0, 'errores': []}
    seen = set(state['vistos'])
    raw.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with raw.open('a', encoding='utf-8') as out:
        if 'reintentos' not in state:  # una vez por día, antes del recorrido
            used, due = reintentar(prov, tag, day, out, max_requests // 5)
            state['peticiones'] += used
            state['reintentos'] = due
            write_json(checkpoint, state)
        while state['pendientes'] and state['peticiones'] < max_requests:
            node, depth, path = state['pendientes'][0]
            filled = True
            for page in range(1, pages + 1):
                if state['peticiones'] >= max_requests:
                    filled = None
                    break
                try:
                    payload = search(prov, tag, node, page)
                except NotFound:
                    payload = {}  # 404 = página sin resultados: el nodo se acaba aquí
                except RuntimeError as exc:
                    state['errores'].append({'nodo': node, 'pagina': page, 'error': str(exc)})
                    if 'eligibility' in str(exc) or 'HTTP 401' in str(exc):
                        raise
                    filled = False
                    break
                finally:
                    state['peticiones'] += 1
                items = amazon_list(amazon_dict(payload.get('searchResult')).get('items'))
                for item in items:
                    out.write(json.dumps({'nodo': node, 'ruta': path, 'item': item}, ensure_ascii=False) + '\n')
                if len(items) < 10:
                    filled = False
                    break
            if filled is None:
                break  # Sin presupuesto a mitad de nodo: se repite entero en la próxima ejecución.
            state['pendientes'].pop(0)
            state['nodos_leidos'] += 1
            if filled:
                kids = []
                if depth < max_depth and state['peticiones'] < max_requests:
                    state['peticiones'] += 1
                    try:
                        parent = CATEGORIES_NODE if node == root_node == BOOKS_NODE else node
                        kids = [(k, n) for k, n in node_children(prov, tag, parent)
                                if k not in seen and key(n) not in SKIP_NODES]
                    except RuntimeError as exc:
                        state['errores'].append({'nodo': node, 'hijos': str(exc)})
                if kids:
                    seen.update(k for k, _ in kids)
                    state['pendientes'] += [[k, depth + 1, path + [n]] for k, n in kids]
                else:
                    state['nodos_llenos'] += 1
            state['vistos'] = sorted(seen)
            out.flush()
            write_json(checkpoint, state)
    state['segundos'] = round(time.monotonic() - started)
    write_json(checkpoint, state)
    return {k: state.get(k, 0) for k in ('peticiones', 'nodos_leidos', 'nodos_llenos', 'reintentos')} | {
        'nodos_pendientes': len(state['pendientes']), 'errores': len(state['errores']), 'raw': str(raw)}


def seller_names():
    """Sellos que se recorren: los del directorio, los del catálogo y los aprendidos en descargas anteriores."""
    names = [p.get('name', '') for p in read_json(ROOT / 'data/editoriales.json', {}).get('publishers', [])]
    names += [p.get('nombre', '') for p in read_json(ROOT / 'data/reading-publishers.json', {}).get('editoriales', [])]
    names += list(read_json(WORK / 'sellos.json', {}).values())
    # «Grupo Almuzara — Almuzara/Berenice» o «Pie de Mosca / MilMadres» no casan como brand: cada sello por separado.
    parts = [part.strip() for name in names for part in re.split(r'\s+[—–·-]\s+|\s*/\s*', name or '') if part.strip()]
    first = {}
    for part in parts:
        first.setdefault(key(part), part)  # una búsqueda por sello, con la primera grafía
    return list(first.values())


def short_name(name):
    return re.sub(r'^(?:Editorial|Ediciones|Edicions|Ed\.)\s+(?=\S{3})', '', (name or '').strip(), flags=re.I)


def spanish_language(lang):
    """«español», «español latino», «castellano»… (ya normalizado con key)."""
    spanish = {key(s) for s in SPANISH}
    return lang in spanish or (lang.split() or [''])[0] in spanish


def is_spanish(info):
    isbn = item_isbn(info) or ''
    return isbn.startswith(('97884', '97913')) or any(spanish_language(l) for l in languages(info))


def spelling_variants(name):
    """Otras escrituras con las que Amazon indexa el papel de un sello: «Plaza & Janés» solo trae Kindle y
    «Plaza & Janes» trae 10 de 10 en papel; «Planeta» trae Lonely Planet y «Editorial Planeta», Planeta
    (medido el 2026-11-06)."""
    fold = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    core = re.sub(r'^editorial\s+', '', name, flags=re.I)
    other = core if core != name else f'Editorial {name}'  # nunca «Editorial Editorial X»
    return [v for v in dict.fromkeys((fold, other)) if v != name]


REPOSO = 21  # días sin preguntar a un sello estéril; luego se revalida solo


def rendimiento_path():
    return WORK / 'rendimiento-sellos.json'


def por_sellos(prov, tag, day, max_requests=1500, pages=10, horizon_days=60, names=None):
    """Novedades por sello (brand + NewestArrivals): casi todo sale en español, al revés que por categorías,
    donde ~3 de cada 4 novedades son importaciones en inglés (medido el 2026-11-06). Un sello se deja de paginar
    al llegar a libros de hace más de `horizon_days`. Los sellos nuevos que aparecen en libros en español se
    aprenden (sellos.json) y entran en la cola del mismo recorrido."""
    raw = WORK / 'raw' / f'{day}.jsonl'
    checkpoint = WORK / 'raw' / f'{day}.sellos.json'
    oldest = (date.fromisoformat(day) - timedelta(days=horizon_days)).isoformat()
    learned = read_json(WORK / 'sellos.json', {})
    # Memoria de rendimiento: un sello que no dio ni un libro en español no se pregunta en REPOSO días
    # (Plaza & Janés, Harlequin… por nombre no traen nada; Minotauro trae Minotaur Books en inglés).
    memory = read_json(rendimiento_path(), {})
    state = read_json(checkpoint)
    if not state:
        queue, keys = [], []
        for name in names if names is not None else seller_names():
            short = short_name(name)
            k = key(short)
            if len(k) >= 3 and k not in keys:
                keys.append(k)
                queue.append(short)
        state = {'cola': queue, 'claves': keys, 'peticiones': 0, 'sellos_leidos': 0, 'sellos_nuevos': 0,
                 'libros_es': 0, 'errores': []}
    keys = state['claves']
    raw.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with raw.open('a', encoding='utf-8') as out:
        if 'reintentos' not in state:
            used, due = reintentar(prov, tag, day, out, max_requests // 5)
            state['peticiones'] += used
            state['reintentos'] = due
            write_json(checkpoint, state)
        origins = state.setdefault('origen', {})
        while state['cola'] and state['peticiones'] < max_requests:
            name = state['cola'][0]
            origin = origins.get(name, name)  # una variante de escritura cuenta para el sello original
            remembered = memory.get(key(origin), {})
            query = remembered.get('consulta', name) if name == origin else name
            if name == origin and remembered.get('saltar_hasta', '') > day:
                state['cola'].pop(0)
                state['sellos_saltados'] = state.get('sellos_saltados', 0) + 1
                continue
            done, found = True, 0
            for page in range(1, pages + 1):
                if state['peticiones'] >= max_requests:
                    done = False
                    break
                try:
                    payload = prov.post(SEARCH, {'marketplace': 'www.amazon.es', 'partnerTag': tag, 'searchIndex': 'Books',
                                                 'brand': query, 'sortBy': 'NewestArrivals', 'itemCount': 10,
                                                 'itemPage': page, 'availability': 'IncludeOutOfStock', 'condition': 'New', 'currencyOfPreference': 'EUR',
                                                 'resources': RESOURCES}, prov.headers())
                except NotFound:
                    payload = {}
                except RuntimeError as exc:
                    state['errores'].append({'sello': name, 'pagina': page, 'error': str(exc)})
                    if 'eligibility' in str(exc) or 'HTTP 401' in str(exc):
                        raise
                    if name not in state.setdefault('reencolados', []):
                        state['reencolados'].append(name)
                        state['cola'].append(name)
                    break
                finally:
                    state['peticiones'] += 1
                items = [amazon_dict(i) for i in amazon_list(amazon_dict(payload.get('searchResult')).get('items'))]
                dates, spanish = [], 0
                for item in items:
                    out.write(json.dumps({'nodo': 'sello:' + name, 'ruta': [], 'item': item}, ensure_ascii=False) + '\n')
                    info = amazon_dict(item.get('itemInfo'))
                    published = amazon_dict(amazon_dict(info.get('contentInfo')).get('publicationDate')).get('displayValue')
                    if isinstance(published, str):
                        dates.append(published[:10])
                    if not is_spanish(info):
                        continue
                    spanish += 1
                    found += bool(item_isbn(info))  # un sello que solo trae Kindle/Audible tampoco aporta
                    state['libros_es'] += 1
                    maker = short_name(publisher_name(amazon_dict(info.get('byLineInfo')).get('manufacturer')))
                    k = key(maker)
                    # «Salamandra Infantil y Juvenil» ya sale buscando «Salamandra»: solo se aprende lo que no cubre ninguno.
                    if len(k) >= 3 and not any(k == c or k.startswith(c + ' ') for c in keys):
                        keys.append(k)
                        state['cola'].append(maker)
                        learned[k] = maker
                        state['sellos_nuevos'] += 1
                # Se deja de paginar: página incompleta, página sin un solo libro en español (brand es coincidencia
                # parcial: «Minotauro» trae Minotaur Books en inglés) o página entera más antigua que el horizonte.
                if len(items) < 10 or not spanish or (dates and max(dates) < oldest):
                    break
                if page == pages:
                    state['sellos_llenos'] = state.get('sellos_llenos', 0) + 1  # 100 resultados: habría que partirlo
            if not done:
                break  # sin presupuesto a mitad de sello: se repite entero la próxima vez
            state['cola'].pop(0)
            state['sellos_leidos'] += 1
            if not any(e['sello'] == name for e in state['errores']):
                tried = state.setdefault('variantes_probadas', [])
                untried = [v for v in spelling_variants(origin) if f'{key(origin)}|{key(v)}' not in tried and v != query]
                if not found and untried:
                    # Estéril con esta escritura: el papel suele estar indexado con otra (sin tilde, con
                    # «Editorial»). Se prueba la siguiente antes de dejar el sello en reposo.
                    tried.append(f'{key(origin)}|{key(untried[0])}')
                    origins[untried[0]] = origin
                    state['cola'].append(untried[0])
                else:
                    memory[key(origin)] = {'nombre': origin, 'libros_es': found, 'ultima': day} | (
                        {'consulta': query} if found and query != origin else {}) | (
                        {'saltar_hasta': (date.fromisoformat(day) + timedelta(days=REPOSO)).isoformat()} if not found else {})
                    write_json(rendimiento_path(), memory)
            out.flush()
            write_json(checkpoint, state)
            write_json(WORK / 'sellos.json', learned)
    state['segundos'] = round(time.monotonic() - started)
    write_json(checkpoint, state)
    return {k: state.get(k, 0) for k in ('peticiones', 'sellos_leidos', 'sellos_saltados', 'sellos_nuevos', 'sellos_llenos', 'libros_es', 'reintentos', 'segundos')} | {
        'sellos_pendientes': len(state['cola']), 'errores': len(state['errores']), 'raw': str(raw)}


# ---------------------------------------------------------------- 2. transformar

def text(value):
    value = amazon_dict(value).get('displayValue')
    return ' '.join(value.split()) if isinstance(value, str) else ''


def publisher_name(value):
    """Nombre de sello o ''. Los autoeditados traen como fabricante su ISBN («978-628-01-9180-5»): sin una
    letra no es un sello, ni para la ficha ni para aprenderlo en el radar."""
    name = text(value)
    return name if re.search(r'[^\W\d_]', name) else ''


def person(name):
    """«García Márquez, Gabriel» → «Gabriel García Márquez»; «ELI CYMET» → «Eli Cymet»."""
    from reading_intake_core import clean_author
    name = ' '.join(str(name).split())
    parts = [p.strip() for p in name.split(',')]
    if (len(parts) == 2 and all(parts) and not re.search(r'\b(?:y|and|et)\b', name)
            and not re.fullmatch(r'(?:jr|sr|hijo|ii|iii|iv)\.?', key(parts[1]))):  # «Juan Pérez, Jr.» ya está bien
        name = parts[1] + ' ' + parts[0]
    folded = re.sub(r'[\W_]', '', key(name))
    if folded in {'aavv', 'vvaa', 'varios', 'variosautores'}:
        return 'Varios autores'
    if folded in {'anonimo', 'anonima', 'anonymous'}:
        return 'Anónimo'
    return clean_author(name)


ARTICLE_AT_END = re.compile(r'^(.+?),\s*(el|la|los|las|lo|un|una|unos|unas)$', re.I)
ROMAN = re.compile(r'^(?=[ivxlc]+$)c{0,3}(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3})$', re.I)
SHORT_WORDS = set('de la el en un mi tu su se no lo le al es me te si ya yo ni os ha he oh ay ti da ve va'.split())
SENTENCE_START = re.compile(r'(^|[.:!?¡¿«"(]\s*)(\w)')


def proper_words(catalogue):
    """Palabras que el catálogo escribe con mayúscula en mitad de un título o en un nombre: «Lorca», «Dios»."""
    # Solo cuenta una palabra que el catálogo nunca escribe en minúscula: así «Al», «De» o «The» de los títulos
    # en estilo inglés (Mayúscula En Cada Palabra) no se cuelan como nombres propios.
    upper, lower = {}, set()
    for book in catalogue['libros']:
        title = book.get('titulo', '')
        if title.upper() == title:
            continue
        for word in re.findall(r'(?<=[\w,;] )\w+', title):
            if word[:1].isupper() and (not word.isupper() or 3 <= len(word) <= 6):
                upper.setdefault(key(word), word)  # nombre propio, o sigla escrita así fuera de mayúsculas: ONU
            elif word.islower():
                lower.add(key(word))
    for book in catalogue['libros']:
        for name in book.get('autores', []):
            if name.upper() != name:
                for word in name.split():
                    if word[:1].isupper() and word.isalpha() and len(word) > 2:
                        upper.setdefault(key(word), word)
    return {k: v for k, v in upper.items() if k not in lower and len(k) > 2}


def tidy_title(title, proper=None):
    """Título entero en mayúsculas → mayúscula inicial (norma del español), con los nombres propios que el
    catálogo ya conoce y los numerales romanos; el artículo pospuesto de catálogo («MUNDO, EL») vuelve delante."""
    proper = proper or {}
    letters = [c for c in title if c.isalpha()]
    if len(letters) >= 4 and all(c.isupper() for c in letters):
        words = []
        for word in title.split(' '):
            core = re.sub(r'^\W+|\W+$', '', word)
            if core and ROMAN.match(core) and len(core) <= 4 and core.lower() not in {'mi', 'di', 'li', 'ci'}:
                words.append(word)
            elif len(core) == 2 and core.isalpha() and core.lower() not in SHORT_WORDS:
                words.append(word)  # sigla: IA, UE, TV
            elif core and key(core) in proper:
                words.append(word.replace(core, proper[key(core)]))
            else:
                words.append(word.lower())
        title = SENTENCE_START.sub(lambda m: m.group(1) + m.group(2).upper(), ' '.join(words))
    moved = ARTICLE_AT_END.match(title)
    if moved:
        rest = moved.group(1)
        if key(rest.split(' ')[0]) not in proper:
            rest = rest[:1].lower() + rest[1:]
        title = moved.group(2).capitalize() + ' ' + rest
    return title


def item_isbn(info):
    eans = [isbn13(v) for v in amazon_list(amazon_dict(amazon_dict(info.get('externalIds')).get('eans')).get('displayValues'))
            if isinstance(v, str)]
    found = [i for i in eans if i and i.startswith(('978', '979'))]
    return next((i for i in found if i.startswith(('97884', '97913'))), found[0] if found else None)


def languages(info):
    """Idiomas en que está la edición. Amazon añade el «Idioma original» de la obra: con él, 306 ediciones en
    catalán, gallego, euskera o inglés de obras escritas en español pasaban por castellanas (descarga del
    2026-11-06). Si hay idioma «Publicado» manda ese; si no, vale cualquiera menos el original."""
    values = [amazon_dict(v) for v in amazon_list(amazon_dict(amazon_dict(info.get('contentInfo')).get('languages'))
                                                  .get('displayValues'))]
    values = [v for v in values if isinstance(v.get('displayValue'), str)]
    published = [v for v in values if key(v.get('type') or '') == 'publicado']
    chosen = published or [v for v in values if key(v.get('type') or '') != 'idioma original']
    return [key(v['displayValue']) for v in chosen]


def subjects(item, path):
    """Materias del libro: sus nodos de Amazon (de más concreto a más general) y la ruta del recorrido."""
    names = []
    for node in amazon_list(amazon_dict(item.get('browseNodeInfo')).get('browseNodes')):
        current = amazon_dict(node)
        while current:
            names.append(current.get('displayName') or current.get('contextFreeName') or '')
            current = amazon_dict(current.get('ancestor'))
    names += list(reversed(path or []))
    out, seen = [], set()
    for name in names:
        name = ' '.join(str(name).split())
        name = NODE_ALIASES.get(key(name), name)
        if name and key(name) not in GENERIC_NODES and not STORE_NODES.match(key(name)) and key(name) not in seen:
            seen.add(key(name))  # «Novela histórica» y «Novela Historica» son la misma plaza
            out.append(name)
    return out


def node_subjects(item):
    """Materias del mapa cerrado por rama de nodos, de lo concreto a lo general. En cada nivel cuenta antes el
    nombre sin contexto («Novelas románticas y paranormales para jóvenes»), que no es ambiguo, que el visible
    («Paranormal»)."""
    found = []
    for node in amazon_list(amazon_dict(item.get('browseNodeInfo')).get('browseNodes')):
        current, level = amazon_dict(node), 0
        while current:
            for name in (current.get('contextFreeName'), current.get('displayName')):
                name = ' '.join(str(name or '').split())
                subject = SUBJECT_OF_NODE.get(key(NODE_ALIASES.get(key(name), name)))
                if subject:
                    found.append((level, subject))
                    break
            current, level = amazon_dict(current.get('ancestor')), level + 1
    # Amazon no garantiza el orden de las ramas: el resultado (y el corte a tres) no debe depender de él.
    return list(dict.fromkeys(subject for _, subject in sorted(found)))


def node_names(item):
    """Nombres de los nodos para el diagnóstico de lo no mapeado: el contextual, que es el que se añade al mapa."""
    names = []
    for node in amazon_list(amazon_dict(item.get('browseNodeInfo')).get('browseNodes')):
        current = amazon_dict(node)
        while current:
            name = ' '.join(str(current.get('contextFreeName') or current.get('displayName') or '').split())
            if name and key(name) not in GENERIC_NODES and not STORE_NODES.match(key(name)):
                names.append(name)
            current = amazon_dict(current.get('ancestor'))
    return list(dict.fromkeys(names))


def sales_rank(record):
    rank = amazon_dict(amazon_dict(amazon_dict(record.get('item')).get('browseNodeInfo')).get('websiteSalesRank')).get('salesRank')
    if isinstance(rank, str) and rank.strip().isdigit():
        rank = int(rank)
    return rank if isinstance(rank, int) and not isinstance(rank, bool) and rank > 0 else float('inf')


class Rejected(Exception):
    pass


def to_record(entry, day, proper=None):
    """Un resultado de Amazon → registro con la forma que espera make_book. Lanza Rejected(motivo)."""
    item = amazon_dict(entry.get('item'))
    info = amazon_dict(item.get('itemInfo'))
    asin = item.get('asin', '')
    isbn = item_isbn(info)
    if not isbn:
        raise Rejected('sin ISBN-13')
    langs = languages(info)
    spanish = any(spanish_language(l) for l in langs)
    if langs and not spanish:
        raise Rejected('idioma: ' + ', '.join(sorted(set(langs)))[:60])
    if not langs and not isbn.startswith(('97884', '97913')):
        raise Rejected('sin idioma y con ISBN extranjero')
    title = tidy_title(text(info.get('title')), proper)
    if not title:
        raise Rejected('sin título')
    byline = amazon_dict(info.get('byLineInfo'))
    contributors = [amazon_dict(c) for c in amazon_list(byline.get('contributors'))]
    authors = [person(c['name']) for c in contributors if isinstance(c.get('name'), str)
               and key(c.get('role', '') or c.get('roleType', '')) in AUTHOR_ROLES]
    if not authors:
        authors = [person(c['name']) for c in contributors if isinstance(c.get('name'), str)][:3]
    authors = list(dict.fromkeys(a for a in authors if a))
    if not authors:
        raise Rejected('sin autoría')
    publisher = publisher_name(byline.get('manufacturer')) or publisher_name(byline.get('brand'))
    if not publisher:
        raise Rejected('sin editorial')
    binding_text = text(amazon_dict(info.get('classifications')).get('binding'))
    # «Tapa blanda (Bunko)» (manga) es tapa blanda: la variante entre paréntesis no cambia el formato.
    fmt = PRINT_BINDINGS.get(key(binding_text)) or BINDINGS.get(key(binding_text)) or BINDINGS.get(key(re.sub(r'\s*\([^)]*\)\s*$', '', binding_text or '')))
    if not fmt or fmt == 'audiolibro':  # el catálogo es de libros para leer: un audiolibro no es su edición
        raise Rejected('encuadernación: ' + (binding_text or 'vacía'))
    content = amazon_dict(info.get('contentInfo'))
    published = text(content.get('publicationDate')) or text(amazon_dict(info.get('productInfo')).get('releaseDate'))
    if not re.match(r'\d{4}-\d{2}-\d{2}', published):
        raise Rejected('sin fecha de publicación')
    pages = amazon_dict(content.get('pagesCount')).get('displayValue')
    nodes = subjects(item, entry.get('ruta'))
    materias = list(dict.fromkeys(node_subjects(item) + [SUBJECT_OF_NODE[key(n)] for n in nodes if key(n) in SUBJECT_OF_NODE]))
    record = {
        'isbn13': isbn, 'asin': asin, 'titulo': title, 'autores': authors, 'editorial': publisher,
        'encuadernacion': binding_text[:1].upper() + binding_text[1:], 'formato_edicion': fmt,
        'materias': materias[:3], 'palabras_clave': nodes[:12],
        'fecha_publicacion_edicion': published[:10], 'precision_fecha': 'dia',
        'numero_paginas': pages if isinstance(pages, int) and 0 < pages < 10000 else None,
        'portada_fuente_url': f'https://www.amazon.es/dp/{asin}', 'cover_use_basis': COVER_BASIS,
        'fuente_bibliografica_url': f'https://www.amazon.es/dp/{asin}',
        'item': item,
    }
    return record


def transformar(day, catalogue):
    """raw → candidatos.json (uno por obra) y fallos de esta fase."""
    from reading_intake_pipeline import classify, work_key  # import tardío: carga el builder
    from reading_editorial_sources import SourceError
    raw = WORK / 'raw' / f'{day}.jsonl'
    if not raw.exists():
        raise SystemExit(f'No hay descarga para {day}: {raw}')
    known_isbn = {b.get('isbn13') for b in catalogue['libros']}
    # Libros del catálogo sin enlace directo: si Amazon devuelve su ISBN, el item no se tira, se guarda para
    # que «aplicar» les ponga formatos y precio (microcorrección, no alta).
    linkless = {b.get('isbn13') for b in catalogue['libros'] if b.get('estado') == 'publicado' and not b.get('formatos_compra')}
    links = defaultdict(list)
    known_work = {work_key(b['titulo'], b['autores']) for b in catalogue['libros']}
    proper = proper_words(catalogue)
    by_work, failures, seen, complete = defaultdict(list), [], set(), set()
    total, best = 0, {}
    for line in raw.read_text(encoding='utf-8').splitlines():
        entry = json.loads(line)
        asin = amazon_dict(entry.get('item')).get('asin')
        # El mismo libro sale por varias búsquedas; se queda la aparición con la clasificación más completa.
        if asin not in best or len(node_names(entry['item'])) > len(node_names(best[asin]['item'])):
            best[asin] = entry
    for asin, entry in best.items():
        if asin in seen:
            continue
        seen.add(asin)
        total += 1
        found = item_isbn(amazon_dict(amazon_dict(entry.get('item')).get('itemInfo')))
        if found in linkless:
            links[found].append(entry['item'])
            complete.add(asin)
            failures.append({'asin': asin, 'isbn13': found, 'fase': 'transformar', 'motivo': 'enlace para un libro del catálogo'})
            continue
        try:
            record = to_record(entry, day, proper)
        except Rejected as exc:
            failures.append({'asin': asin, 'fase': 'transformar', 'motivo': str(exc)})
            continue
        try:
            # Solo nodos de escaparate: sin materia no hay dónde mostrarlo. Amazon suele asignarla días
            # después, así que se vuelve a pedir (pendientes) en vez de publicarlo sin clasificar.
            classify(dict(record), {**catalogue, 'categorias': list(catalogue.get('categorias', []))})
        except SourceError:
            # Con nodos que no están en el mapa, reintentar no cambia nada: va a revisión con los nodos,
            # que son la lista de lo que falta por mapear (AMAZON_SUBJECTS).
            nodes = node_names(entry['item']) or record.get('palabras_clave') or []
            failures.append({'asin': asin, 'isbn13': record['isbn13'], 'fase': 'transformar',
                             'motivo': 'materia sin mapear' if nodes else 'sin materia'} | ({'nodos': nodes} if nodes else {}))
            continue
        complete.add(asin)
        if record['isbn13'] in known_isbn:
            failures.append({'asin': asin, 'isbn13': record['isbn13'], 'fase': 'transformar', 'motivo': 'ya en el catálogo'})
            continue
        work = work_key(record['titulo'], record['autores'])
        if work in known_work:
            failures.append({'asin': asin, 'isbn13': record['isbn13'], 'fase': 'transformar', 'motivo': 'otra edición de una obra del catálogo'})
            continue
        by_work[work].append(record)
    candidates = []
    for records in by_work.values():
        # Una ficha por obra: la edición en papel española; las demás aportan sus formatos y precios.
        records.sort(key=lambda r: (EDITION_PREFERENCE.index(r['formato_edicion']), not r['isbn13'].startswith(('97884', '97913'))))
        main, others = records[0], records[1:]
        main['otras_ediciones'] = [o['item'] for o in others]
        candidates.append(main)
    write_json(WORK / f'candidatos-{day}.json', candidates)
    write_json(enlaces_path(day), links)
    pending = update_pending(day, failures, complete)
    return {'leidos': total, 'candidatos': len(candidates), 'pendientes': len(pending), 'enlaces': len(links),
            'fallos': failures}


# ---------------------------------------------------------------- 3. aplicar

LEGAL_FORM = re.compile(r'[\s,]+(?:S\.?\s?A\.?\s?S\.?|S\.?\s?A\.?\s?U\.?|S\.?\s?L\.?\s?U\.?|S\.?\s?L\.?|S\.?\s?A\.?|S\.?\s?C\.?\s?P\.?)\s*$', re.I)
PREFIX = re.compile(r'^(?:Editorial|Ediciones)\s+(?=\S{4})', re.I)
# Clave de sello: lo que queda al quitar forma jurídica, paréntesis y palabras de oficio. En la tanda del
# 2026-11-06 salían como «pendientes» sellos que ya tenían ficha: «Grijalbo Comercial, S.a.», «Molino,editorial»,
# «Errata Naturae Editores S.l», «Hoaki Books», «Altamarea Edición de Libros SL». «Libros» y «Press» no son de
# oficio: «Ediciones la Cúpula» no es «Libros Cúpula» ni «Peninsula Press» es Península.
# Con puntos vale cualquier caja («S.a.», «S.l», «C.b.»); sin puntos solo en mayúsculas («SL», «SA», «CB»), para
# no comerse un nombre que acabe en «As», «Sa» o «Cb».
KEY_LEGAL_FORM = re.compile(r'[\s,]+(?:(?i:s\.\s?[alc]\.?(?:\s?[asup]\.?)?|s\s?[alc]\.(?:\s?[asup]\.?)?|c\.\s?b\.?'
                            r'|ltd\.?|inc\.?|llc|gmbh)|S[ALC][ASUP]?|CB)\s*$')
KEY_TRADE_WORDS = {'editorial', 'editoriales', 'ediciones', 'edicions', 'edicion', 'editores', 'editora', 'edition',
                   'comercial', 'publicaciones', 'publishing', 'publishers', 'books', 'de', 'del', 'la', 'el', 'y'}


def publisher_key(name):
    """«Grijalbo Comercial, S.a.» y «Grijalbo» → «grijalbo»; vacía si no queda nada propio."""
    from reading_intake_core import normalize_text
    text = re.sub(r'\([^)]*\)', ' ', name or '')
    for _ in range(2):
        text = KEY_LEGAL_FORM.sub('', text).strip(' ,')
    text = normalize_text(re.sub(r'[,\-/&]', ' ', text))
    words = re.sub(r"(?:^| )edicion(?:es)? de libros(?= |$)", " ", text).split()  # «Altamarea Edición de Libros SL»
    return ' '.join(w for w in words if w not in KEY_TRADE_WORDS)


def publisher_key_index(directory, catalogue):
    """Clave → sello, solo cuando la clave señala uno. Si choca un sello del directorio con uno del catálogo
    («Maeva» y «Maeva Ediciones»), gana el del directorio, que es el que se enlaza primero."""
    found = {}
    for kind, entries in (('directorio', directory), ('catalogo', catalogue)):
        for entry in entries:
            for name in [entry['nombre'], *entry.get('alias', [])]:
                if k := publisher_key(name):
                    found.setdefault(k, {}).setdefault(kind, set()).add(entry['slug'])
    index = {}
    for k, kinds in found.items():
        slugs = kinds.get('directorio') or kinds.get('catalogo')
        if len(slugs) == 1:
            index[k] = (next(iter(slugs)), 'directorio' if 'directorio' in kinds else 'catalogo')
    return index


def pending_creation_path():
    """Autores y sellos que aparecen en libros publicados sin ficha propia: se crean aparte, por lotes."""
    return WORK / 'pendientes-creacion.json'


def priorizar(candidates, day, limit):
    """Altas de esta pasada: primero novedades y preventas (de 60 días atrás a 6 meses vista), de la más reciente a la
    más antigua; después el fondo, del más vendido en Amazon al menos (sin ranking, al final y por fecha). El resto
    se aplaza: vuelve a salir en la próxima descarga y entra entonces."""
    today = date.fromisoformat(day)
    window = ((today - timedelta(days=60)).isoformat(), (today + timedelta(days=183)).isoformat())

    def rank(record):
        published = record.get('fecha_publicacion_edicion') or ''
        fresh = window[0] <= published <= window[1]
        return (not fresh, 0 if fresh else sales_rank(record), [-ord(c) for c in published])
    ordered = sorted(candidates, key=rank)
    return ordered[:limit], len(ordered[limit:])


def aplicar(day, tag, candidates, transform_failures, root=ROOT):
    from reading_catalogue_publishers import display_name
    from reading_intake_core import normalize_text, publisher_slug
    from reading_intake_pipeline import builder, classify, make_book, texts
    from reading_intake_publishers import resolve_publishers
    from reading_taxonomy import apply_derived
    from reading_ttl_source import typographic_cover

    catalogue = read_json(root / 'data/reading-catalogue.json')
    base_categories = {c['id'] for c in catalogue['categorias']}
    store = read_json(root / 'data/reading-publishers.json', {'schema_version': 1, 'editoriales': []})
    registry = read_json(root / 'data/editoriales.json')
    intake = read_json(root / 'data/reading-intake-config.json')
    allowed = resolve_publishers(registry, intake.get('publisher_aliases', []))
    by_slug = {p['slug']: p for p in allowed}
    catalogue_names = {normalize_text(p['nombre']): p for p in store['editoriales']}
    catalogue_slugs = {p['slug']: p for p in store['editoriales']}
    key_index = publisher_key_index([{'nombre': p['name'], 'slug': p['slug'], 'alias': p.get('aliases', [])}
                                     for p in allowed], store['editoriales'])
    known_authors = {a['nombre'] for a in
                     read_json(root / 'data/reading-authors.json', {'autores': []}).get('autores', [])}
    waiting = read_json(pending_creation_path(), {'editoriales': {}, 'autores': {}})
    pending_keys = {}
    for pending in waiting['editoriales']:
        pending_keys.setdefault(publisher_key(pending) or pending, pending)
    now = datetime.now(timezone.utc)
    failures = list(transform_failures)
    added = {}

    def publisher_for(name):
        # Amazon escribe el sello con forma jurídica o prefijo («Norma Editorial, S.a.», «Editorial Almuzara»):
        # se prueban esas variantes contra el directorio y el catálogo antes de darlo por desconocido.
        bare = LEGAL_FORM.sub('', name).strip(' ,')
        core = PREFIX.sub('', bare)
        tail = re.sub(r'\s+Editorial$', '', core, flags=re.I)
        for variant in dict.fromkeys((name, bare, core, tail, f'{tail} Editorial')):
            slug = publisher_slug(variant, allowed)
            if slug:
                return {'name': by_slug[slug]['name'], 'slug': slug}
            found = catalogue_names.get(normalize_text(variant))
            if found:
                return {'name': found['nombre'], 'slug': found['slug'], 'catalogo': True}
        slug, kind = key_index.get(publisher_key(name), (None, None))
        if kind == 'directorio':
            return {'name': by_slug[slug]['name'], 'slug': slug}
        if kind == 'catalogo':
            return {'name': catalogue_slugs[slug]['nombre'], 'slug': slug, 'catalogo': True}
        # Sello desconocido: el libro sale con el nombre en texto, sin enlace. Crear su ficha es trabajo aparte
        # (lista de pendientes de creación), no de la ingesta diaria.
        return {'name': display_name(name) or name, 'slug': None}

    def note(kind, name, isbn):
        if kind == 'editoriales':  # «GTM Ediciones» y «GTM Ediciones C.b.» son un solo sello por crear
            name = pending_keys.setdefault(publisher_key(name) or name, name)
        entry = waiting[kind].setdefault(name, {'libros': 0, 'primera': day, 'ejemplos': []})
        entry['libros'] += 1
        if len(entry['ejemplos']) < 3 and isbn not in entry['ejemplos']:
            entry['ejemplos'].append(isbn)

    for record in candidates:
        try:
            publisher = publisher_for(record['editorial'])
            record['editorial'] = publisher['name']
            image, small, dimensions = typographic_cover(record)
            path = '/assets/reading-covers/isbn-' + record['isbn13'] + '.webp'
            book = make_book(record, publisher, tag, day, path, dimensions)
            if not publisher['slug']:
                book.pop('editorial_slug', None)
            offers = []
            for item in [record['item'], *record.get('otras_ediciones', [])]:
                offers += select_offers(book, {'searchResult': {'items': [item]}}, tag, now)
            if offers:
                store_prices(book, offers, day)
            categories = classify(record, catalogue)
            catalogue['libros'].append(book)
            catalogue['libro_categorias'] += [{'libro_id': book['id'], 'categoria_id': c} for c in dict.fromkeys(categories)]
            added[book['id']] = (path, image, small, record)
        except Exception as exc:  # noqa: BLE001 - el lote sigue; el motivo queda registrado
            failures.append({'asin': record.get('asin'), 'isbn13': record.get('isbn13'), 'fase': 'aplicar',
                             'motivo': f'{type(exc).__name__}: {exc}'[:200]})
    # Microcorrección: formatos y precio para libros ya publicados que no tenían enlace directo. Cada uno se
    # valida solo; si no pasa, vuelve a como estaba (nunca tumba el lote).
    linked, links = 0, read_json(enlaces_path(day), {})
    for book in catalogue['libros']:
        items = links.get(book.get('isbn13')) if links and not book.get('formatos_compra') else None
        if not items:
            continue
        before = json.loads(json.dumps(book))
        try:
            offers = select_offers(book, {'searchResult': {'items': items}}, tag, now)
            if not offers:
                continue
            store_prices(book, offers, day)
            builder.validate({'schema_version': 1, 'categorias': catalogue['categorias'], 'libros': [book],
                              'libro_categorias': [r for r in catalogue['libro_categorias'] if r['libro_id'] == book['id']]}, root)
            linked += 1
        except Exception as exc:  # noqa: BLE001
            book.clear()
            book.update(before)
            failures.append({'isbn13': book.get('isbn13'), 'fase': 'enlazar', 'motivo': f'{type(exc).__name__}: {exc}'[:200]})
    apply_derived(catalogue)
    for book_id, (path, image, small, _) in added.items():
        for relative, content in ((path, image), (path.replace('.webp', '-320.webp'), small)):
            target = root / relative.lstrip('/')
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(content)

    def drop(book_id, reason):
        catalogue['libros'] = [b for b in catalogue['libros'] if b['id'] != book_id]
        catalogue['libro_categorias'] = [r for r in catalogue['libro_categorias'] if r['libro_id'] != book_id]
        path, _, _, record = added.pop(book_id)
        for relative in (path, path.replace('.webp', '-320.webp')):
            (root / relative.lstrip('/')).unlink(missing_ok=True)
        failures.append({'asin': record.get('asin'), 'isbn13': record['isbn13'], 'fase': 'validar', 'motivo': reason[:200]})

    # Índice libro → categorías: sin él, cada libro nuevo recorre todas las relaciones por cada libro afín (O(n²)).
    index = {}
    for r in catalogue['libro_categorias']:
        index.setdefault(r['libro_id'], set()).add(r['categoria_id'])
    for module in (texts.catalogue, builder):
        module.CATEGORY_INDEX = (catalogue, index)
    # Contenido mínimo para orientar (lo exige la puerta de textos): se mide, no se adivina.
    for book in [b for b in catalogue['libros'] if b['id'] in added]:
        modules = {m['modulo'] for m in texts.payload(catalogue, book)['modulos_permitidos']}
        if len(modules) < texts.MIN_BLOCKS or 'para_quien' not in modules:
            drop(book['id'], 'datos insuficientes para orientar: ' + (', '.join(sorted(modules)) or 'ningún bloque'))
    # Cuarentena en dos pasos. 1) Cada libro nuevo solo (milisegundos): sus campos, enlaces y portada.
    # La validación entera tarda ~10 s; hacerla por libro con 1000 altas serían horas.
    for book in [b for b in catalogue['libros'] if b['id'] in added]:
        alone = {'schema_version': 1, 'categorias': catalogue['categorias'], 'libros': [book],
                 'libro_categorias': [r for r in catalogue['libro_categorias'] if r['libro_id'] == book['id']]}
        try:
            builder.validate(alone, root)
        except builder.ValidationError as exc:
            if book['id'] in str(exc):
                drop(book['id'], str(exc))
    # 2) El catálogo entero (duplicados entre libros): el libro nuevo que lo rompe sale y se repite.
    while True:
        try:
            builder.validate(catalogue, root)
            break
        except builder.ValidationError as exc:
            found = re.search(r'isbn-\d{13}', str(exc))
            if not found or found.group() not in added:
                write_json(WORK / f'fallos-{day}.json', summarize(failures))
                raise SystemExit(f'Validación global sin libro nuevo al que atribuirla: {exc}')
            drop(found.group(), str(exc))
    # Las categorías que solo creó un libro apartado no se quedan vacías.
    used = {r['categoria_id'] for r in catalogue['libro_categorias']}
    catalogue['categorias'] = [c for c in catalogue['categorias'] if c['id'] in used or c['id'] in base_categories]
    builder.validate(catalogue, root)
    write_json(root / 'data/reading-catalogue.json', catalogue)
    # Solo los libros que han quedado publicados apuntan autores y sellos pendientes de ficha.
    for book in [b for b in catalogue['libros'] if b['id'] in added]:
        if not book.get('editorial_slug') and not book.get('editorial_catalogo_slug'):
            note('editoriales', book['editorial'], book['isbn13'])
        for author in book['autores']:
            if author not in known_authors:  # el builder enlaza por nombre exacto
                note('autores', author, book['isbn13'])
    write_json(pending_creation_path(), waiting)
    report = summarize(failures)
    write_json(WORK / f'fallos-{day}.json', report)
    return {'publicados': len(added), 'enlazados': linked, 'fallos': len(failures), 'motivos': report['motivos']}


def summarize(failures):
    reasons = Counter(re.sub(r'isbn-\d{13}|\d{3,}', '#', f['motivo']) for f in failures)
    by_reason = defaultdict(list)
    for f in failures:
        by_reason[re.sub(r'isbn-\d{13}|\d{3,}', '#', f['motivo'])].append(f)
    unmapped = Counter(n for f in failures for n in f.get('nodos', []))
    return {'total': len(failures), 'motivos': dict(reasons.most_common()),
            'ejemplos': {r: items[:5] for r, items in by_reason.items()},
            'nodos_sin_mapear': dict(unmapped.most_common(100))}  # lo siguiente que añadir a AMAZON_SUBJECTS


# ---------------------------------------------------------------- CLI

# ---------------------------------------------------------------- 4. revisar

# Campos que mira la revisión diaria. Los estables no deberían cambiar nunca en un libro publicado: si cambian,
# es un dato pisado (o una corrección legítima que conviene ver). Los demás solo se vigilan para que no se vacíen.
WATCH = ('titulo', 'autores', 'editorial', 'isbn13', 'idioma', 'formato_edicion', 'fecha_publicacion',
         'numero_paginas', 'sinopsis_breve', 'descripcion_breve', 'formatos_compra', 'portada_local', 'pvp_centimos')
STABLE = ('titulo', 'autores', 'editorial', 'isbn13', 'idioma')


def fingerprint(value):
    """Huella corta de un campo; None si está vacío."""
    if value in (None, '', [], {}):
        return None
    if isinstance(value, (str, int, float)):
        return str(value)[:120]
    return hashlib.sha1(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]


def revisar(day, catalogue):
    """Foto de los libros publicados y comparación con la última anterior: campos vacíos, vaciados, cambiados y
    libros desaparecidos. Lo vaciado o desaparecido es una regresión (sale con código 1); lo vacío es la lista de
    microcorrecciones pendientes."""
    folder = WORK / 'revision'
    folder.mkdir(parents=True, exist_ok=True)
    books = {b['id']: b for b in catalogue['libros'] if b.get('estado') == 'publicado'}
    snap = {i: {f: fingerprint(b.get(f)) for f in WATCH} for i, b in books.items()}
    earlier = sorted(p for p in folder.glob('foto-*.json') if p.stem[5:] < day)
    prev = read_json(earlier[-1], {}) if earlier else {}
    write_json(folder / f'foto-{day}.json', snap)
    empty = Counter(f for s in snap.values() for f, v in s.items() if v is None)
    emptied = [{'id': i, 'campo': f} for i, s in snap.items() if i in prev
               for f in WATCH if prev[i].get(f) is not None and s[f] is None]
    changed = [{'id': i, 'campo': f} for i, s in snap.items() if i in prev
               for f in STABLE if None not in (prev[i].get(f), s[f]) and prev[i].get(f) != s[f]]
    report = {'dia': day, 'publicados': len(books), 'comparado_con': earlier[-1].stem[5:] if earlier else None,
              'vacios': dict(empty.most_common()),
              'sin_enlace': sorted(i for i, b in books.items() if not b.get('formatos_compra'))[:50],
              'vaciados': emptied, 'cambiados': changed, 'desaparecidos': sorted(set(prev) - set(books))}
    report['regresion'] = bool(emptied or report['desaparecidos'])
    # Los sin enlace con ISBN 978 se piden por su ISBN-10 (ASIN del papel) en la próxima descarga.
    pending = read_json(pending_path(), {})
    queued = 0
    for b in books.values():
        asin = isbn10(b.get('isbn13')) if not b.get('formatos_compra') else None
        if asin and asin not in pending:
            pending[asin] = {'primera': day, 'intentos': 0, 'motivo': 'sin enlace directo', 'siguiente': day}
            queued += 1
    write_json(pending_path(), pending)
    report['enlaces_pedidos'] = queued
    write_json(folder / f'informe-{day}.json', report)
    return report


def http_get(url):
    from urllib.request import Request, urlopen
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; catalogo-lecturas/1.0)'})
    with urlopen(request, timeout=60) as response:
        return response.read().decode('utf-8', errors='replace')


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')  # consola Windows (cp1252): «→», «ñ» en ayuda e informe
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('fase', choices=['descargar', 'transformar', 'aplicar', 'revisar', 'todo'])
    parser.add_argument('--dia', default=date.today().isoformat())
    parser.add_argument('--peticiones', type=int, default=None)
    parser.add_argument('--profundidad', type=int, default=None)
    parser.add_argument('--altas', type=int, default=None, help='máximo de libros nuevos por pasada (1000)')
    parser.add_argument('--modo', choices=['sellos', 'nodos'], default='sellos',
                        help='sellos: novedades por editorial (por defecto, casi todo en español); nodos: por categorías')
    args = parser.parse_args(argv)
    tag, cfg = config()
    report = {'dia': args.dia, 'inicio': datetime.now().isoformat(timespec='seconds')}
    started = time.monotonic()
    if args.fase in ('descargar', 'todo'):
        budget = args.peticiones or cfg.get('max_requests', 1500)
        if cfg.get('semillas_sitemaps', 2):
            catalogue = read_json(ROOT / 'data/reading-catalogue.json')
            try:
                added = semillas_ttl(http_get, args.dia, {b.get('isbn13') for b in catalogue['libros']},
                                     cfg.get('semillas_sitemaps', 2))
            except (OSError, ValueError) as exc:  # sin sitemap hoy: la cola de días anteriores sigue valiendo
                added = f'error: {str(exc)[:120]}'
            raw = WORK / 'raw' / f'{args.dia}.jsonl'
            raw.parent.mkdir(parents=True, exist_ok=True)
            with raw.open('a', encoding='utf-8') as out:
                # Las semillas rinden ~98 %: van primero y a los sellos se les guarda solo una reserva.
                reserve = cfg.get('reserva_sellos', budget // 4)
                report['semillas'] = {'nuevas': added} | por_isbn(provider(tag), tag, args.dia, out, max(budget - reserve, 0))
            budget -= report['semillas']['peticiones']
        if args.modo == 'sellos':
            report['descargar'] = por_sellos(provider(tag), tag, args.dia, max_requests=budget,
                                             horizon_days=cfg.get('horizonte_dias', 60))
        else:
            report['descargar'] = descargar(provider(tag), tag, args.dia, max_requests=budget,
                                            max_depth=args.profundidad if args.profundidad is not None else cfg.get('max_depth', 3))
    if args.fase in ('transformar', 'aplicar', 'todo'):
        catalogue = read_json(ROOT / 'data/reading-catalogue.json')
        result = transformar(args.dia, catalogue)
        report['transformar'] = {k: v for k, v in result.items() if k != 'fallos'} | {'rechazos': len(result['fallos'])}
        if args.fase in ('aplicar', 'todo'):
            candidates, deferred = priorizar(read_json(WORK / f'candidatos-{args.dia}.json'), args.dia,
                                             args.altas or cfg.get('max_altas', 1000))
            report['aplicar'] = aplicar(args.dia, tag, candidates, result['fallos']) | {'aplazados': deferred}
        else:
            write_json(WORK / f'fallos-{args.dia}.json', summarize(result['fallos']))
    if args.fase in ('revisar', 'todo'):
        review = revisar(args.dia, read_json(ROOT / 'data/reading-catalogue.json'))
        report['revisar'] = {k: (len(v) if isinstance(v, list) else v) for k, v in review.items()}
    report['segundos'] = round(time.monotonic() - started)
    write_json(WORK / f'informe-{args.dia}.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report.get('revisar', {}).get('regresion') else 0


if __name__ == '__main__':
    sys.exit(main())
