"""Radar de novedades de Amazon: qué libros recientes y próximos faltan en el catálogo.

SearchItems devuelve como mucho 10 páginas de 10 por consulta, así que una sola consulta sobre
«Libros» ve 100 títulos de los miles que salen cada semana. El radar recorre el árbol de nodos
(GetBrowseNodes): cada nodo que llena sus 10 páginas se parte en sus hijos, hasta `max_depth`
o hasta agotar `max_requests`. El informe dice cuántos nodos siguen llenos (cobertura incompleta).
"""
import re
from collections import Counter
from datetime import date

from reading_amazon_market import amazon_dict, amazon_list
from reading_ratings_refresh import isbn13, key

BOOKS_NODE = '599364031'  # «Libros» en amazon.es
RESOURCES = ['itemInfo.byLineInfo', 'itemInfo.contentInfo', 'itemInfo.externalIds']


SPANISH = ('español', 'espanol', 'spanish', 'castellano')


def radar_request(tag, page, node=BOOKS_NODE):
    if not re.fullmatch(r'[A-Za-z0-9-]+', tag) or not 1 <= page <= 10 or not re.fullmatch(r'\d+', node):
        raise ValueError('Tag, página o nodo inválidos')
    return {'marketplace': 'www.amazon.es', 'partnerTag': tag, 'searchIndex': 'Books', 'browseNodeId': node,
            'sortBy': 'NewestArrivals', 'itemCount': 10, 'itemPage': page, 'resources': RESOURCES}


def radar_rows(payload):
    """ISBN-13, editorial y fecha de cada resultado; lo demás de Amazon no sale de aquí."""
    rows = []
    for item in amazon_list(amazon_dict(amazon_dict(payload).get('searchResult')).get('items')):
        info = amazon_dict(amazon_dict(item).get('itemInfo'))
        isbns = [isbn13(v) for v in amazon_list(amazon_dict(amazon_dict(info.get('externalIds')).get('eans')).get('displayValues'))
                 if isinstance(v, str)]
        isbn = next((i for i in isbns if i and i.startswith(('978', '979'))), None)
        if not isbn:
            continue
        publisher = amazon_dict(amazon_dict(info.get('byLineInfo')).get('manufacturer')).get('displayValue')
        published = amazon_dict(amazon_dict(info.get('contentInfo')).get('publicationDate')).get('displayValue')
        languages = amazon_list(amazon_dict(amazon_dict(info.get('contentInfo')).get('languages')).get('displayValues'))
        spanish = any(isinstance(amazon_dict(l).get('displayValue'), str) and amazon_dict(l)['displayValue'].strip().lower() in SPANISH
                      for l in languages)
        rows.append({'isbn13': isbn, 'editorial': publisher.strip() if isinstance(publisher, str) else '',
                     'fecha': published[:10] if isinstance(published, str) and re.match(r'\d{4}-\d{2}-\d{2}', published) else '',
                     'castellano': spanish})
    return rows


def connected_publishers(catalogue, aliases):
    """Sellos que ya entran por un conector editorial: los del catálogo y sus alias."""
    names = {key(b.get('editorial', '')) for b in catalogue.get('libros', [])}
    slugs = {b.get('editorial_slug') for b in catalogue.get('libros', [])}
    for alias in aliases:
        if alias.get('slug') in slugs:
            names.update(key(a) for a in alias.get('aliases', []))
    return names - {''}


def coverage(rows, catalogue, connected, today):
    known = {b.get('isbn13') for b in catalogue.get('libros', [])}
    unique = list({r['isbn13']: r for r in rows}.values())
    missing = [r for r in unique if r['isbn13'] not in known]
    uncovered = Counter(r['editorial'] or 'sin editorial' for r in missing if key(r['editorial']) not in connected)
    return {'resultados': len(unique), 'en_catalogo': len(unique) - len(missing), 'faltan': len(missing),
            'faltan_proximamente': sum(1 for r in missing if r['fecha'] > today.isoformat()),
            'faltan_con_conector': sum(1 for r in missing if key(r['editorial']) in connected),
            'editoriales_sin_conector': dict(uncovered.most_common(20))}


def missing_isbns(rows, catalogue):
    """ISBN que faltan y son españoles (978-84, 979-13) o están en castellano según Amazon, de la
    fecha más reciente a la más antigua."""
    known = {b.get('isbn13') for b in catalogue.get('libros', [])}
    unique = {r['isbn13']: r for r in rows if (r['isbn13'].startswith(('97884', '97913')) or r.get('castellano'))
              and r['isbn13'] not in known}
    return [r['isbn13'] for r in sorted(unique.values(), key=lambda r: r['fecha'], reverse=True)]


def children(provider, tag, nodes):
    """Hijos de cada nodo (GetBrowseNodes admite 10 por petición): {nodo: [hijos]}."""
    payload = provider.post('https://creatorsapi.amazon/catalog/v1/getBrowseNodes',
                            {'marketplace': 'www.amazon.es', 'partnerTag': tag, 'browseNodeIds': list(nodes)[:10],
                             'resources': ['browseNodes.children']}, provider.headers())
    result = amazon_dict(payload.get('browseNodesResult') or payload.get('browseNodeResult'))
    found = {}
    for node in amazon_list(result.get('browseNodes')):
        node = amazon_dict(node)
        ids = [str(amazon_dict(c).get('id')) for c in amazon_list(node.get('children'))]
        found[str(node.get('id'))] = [i for i in ids if re.fullmatch(r'\d+', i)]
    return found


def run(provider, catalogue, aliases, tag, today=None, pages=10, node=BOOKS_NODE, collect=None,
        max_requests=10, max_depth=0):
    """`provider` es un CreatorsPrices: una petición por página, al ritmo de 1 por segundo.

    Cada nodo se lee por NewestArrivals; si llena las `pages` páginas, Amazon está cortando la
    lista y el nodo se parte en sus hijos (hasta `max_depth` niveles bajo `node`). Si se pasa
    `collect` (una lista), recibe los ISBN que faltan para la ingesta de esta misma ejecución.
    """
    rows, requests, scanned, full = [], 0, 0, 0
    pending, seen = [(node, 0)], {node}
    while pending and requests < max_requests:
        current, depth = pending.pop(0)
        filled = True
        for page in range(1, pages + 1):
            if requests >= max_requests:
                break
            payload = provider.post('https://creatorsapi.amazon/catalog/v1/searchItems', radar_request(tag, page, current), provider.headers())
            requests += 1
            rows += radar_rows(payload)
            if len(amazon_list(amazon_dict(payload.get('searchResult')).get('items'))) < 10:
                filled = False
                break
        scanned += 1
        if not filled:
            continue
        if depth >= max_depth or requests >= max_requests:
            full += 1
            continue
        requests += 1
        try:
            kids = children(provider, tag, [current]).get(current, [])
        except RuntimeError:
            kids = []
        kids = [k for k in kids if k not in seen]
        if not kids:
            full += 1
        seen.update(kids)
        pending += [(k, depth + 1) for k in kids]
    full += len(pending)
    if collect is not None:
        collect.extend(missing_isbns(rows, catalogue))
    report = coverage(rows, catalogue, connected_publishers(catalogue, aliases), today or date.today())
    return {**report, 'peticiones': requests, 'nodos_leidos': scanned, 'nodos_sin_cubrir': full}
