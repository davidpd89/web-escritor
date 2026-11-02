"""Radar de novedades de Amazon: qué libros recientes faltan en el catálogo y de qué editorial son.

Amazon no da sinopsis ni portadas reutilizables y su licencia solo permite guardar el ASIN, así que
el radar no crea fichas: las fichas salen de la web de cada editorial. El radar mide la cobertura
(próximamente y novedades de Amazon frente al catálogo) y dice qué editoriales conviene conectar.
El informe va al artefacto de la CI con cifras agregadas; ni títulos ni datos de producto.
"""
import re
from collections import Counter
from datetime import date

from reading_amazon_market import amazon_dict, amazon_list
from reading_ratings_refresh import isbn13, key

BOOKS_NODE = '599364031'  # «Libros» en amazon.es
RESOURCES = ['itemInfo.byLineInfo', 'itemInfo.contentInfo', 'itemInfo.externalIds']


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
        rows.append({'isbn13': isbn, 'editorial': publisher.strip() if isinstance(publisher, str) else '',
                     'fecha': published[:10] if isinstance(published, str) and re.match(r'\d{4}-\d{2}-\d{2}', published) else ''})
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


def run(provider, catalogue, aliases, tag, today=None, pages=10, node=BOOKS_NODE):
    """`provider` es un CreatorsPrices: una petición por página, al ritmo de 1 por segundo."""
    rows, requests = [], 0
    for page in range(1, pages + 1):
        payload = provider.post('https://creatorsapi.amazon/catalog/v1/searchItems', radar_request(tag, page, node), provider.headers())
        requests += 1
        rows += radar_rows(payload)
        if len(amazon_list(amazon_dict(payload.get('searchResult')).get('items'))) < 10:
            break
    report = coverage(rows, catalogue, connected_publishers(catalogue, aliases), today or date.today())
    return {**report, 'peticiones': requests}
