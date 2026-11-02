"""Fuente editorial genérica: fichas públicas de editoriales con marcado schema.org o ficha técnica.

Misma salida que `penguin_edition` y `planeta_edition`, de modo que validación, portadas, sellos y
publicación se reutilizan sin tocar. Cada editorial es una entrada de `data/reading-intake-config.json`
con `"provider": "generic"` y su perfil declarativo (hosts, ruta de ficha, hosts de portada, expresiones
para lo que la ficha no marca...), así que sumar una editorial es configuración y no código. El perfil se
limita a los hosts de `REVIEWED`: un host no revisado aquí detiene la ingesta, igual que con Penguin y
Planeta.

Cada dato se busca en este orden: JSON-LD (`Book`, o `Product` con ISBN), ficha técnica de la página
(etiqueta/valor), y por último una expresión del perfil (`regex`). Nunca se infiere un día a partir de un
mes, no se aceptan ediciones que no estén en castellano ni formatos que no sean físicos, y el ISBN debe
tener dígito de control y pertenecer al registro español. Sin red propia: recibe el HTML ya descargado.
"""
from __future__ import annotations

import html
import json
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin, urlsplit

from reading_editorial_sources import SourceError, editorial_excerpt, editorial_synopsis
from reading_intake_core import clean_title, edition_date, isbn13, normalize_text
from reading_planeta_source import _looks_spanish
from reading_taxonomy import keyword_list

# source id -> (hosts de fichas, hosts de portada). Cualquier otro valor en la configuración se rechaza.
REVIEWED: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    'anagrama-es': (('www.anagrama-ed.es',), ('cms.anagrama-ed.es',)),
    'nordica-es': (('nordicalibros.com',), ('nordicalibros.com',)),
    'duomo-es': (('www.duomoediciones.com',), ('www.duomoediciones.com',)),
    'periferica-es': (('www.editorialperiferica.com',), ('www.editorialperiferica.com',)),
}

FORMATS = (
    (('hardcover', 'tapa dura', 'cartone', 'tapa-dura'), 'tapa-dura'),
    (('paperback', 'rustica', 'tapa blanda', 'bolsillo', 'tapa-blanda'), 'tapa-blanda'),
)
SYNOPSIS_HEADINGS = {'sinopsis', 'resumen', 'descripcion', 'argumento', 'de que trata', 'sobre el libro'}
LABELS = {
    'isbn': {'isbn', 'isbn 13', 'ean', 'isbn ean'},
    'paginas': {'paginas', 'n de paginas', 'no de paginas', 'num de paginas', 'numero de paginas', 'extension'},
    'fecha': {'fecha de publicacion', 'publicacion', 'fecha de edicion', 'fecha de aparicion', 'fecha de lanzamiento', 'fecha'},
    'formato': {'formato', 'encuadernacion', 'presentacion', 'tipo de encuadernacion', 'tapa'},
    'coleccion': {'coleccion', 'serie'},
    'pvp': {'pvp', 'pvp con iva', 'precio', 'precio con iva'},
    'thema': {'thema', 'codigo thema', 'materia thema'},
}
# Prefijos de la clasificación Thema que declara la propia editorial; más fiables que deducir de la sinopsis.
THEMA_SUBJECTS = (('DC', 'Poesía'), ('DN', 'Biografías y memorias'), ('F', 'Narrativa'), ('Q', 'Ensayo'), ('J', 'Ensayo'))
LABEL_OF = {text: field for field, texts in LABELS.items() for text in texts}
MONTHS = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
          'septiembre': 9, 'setiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}
# Materia deducida del texto de la propia ficha cuando la editorial no la marca (primera regla que case).
SUBJECT_RULES = (
    (r'\b(poemas?|poesia|poetico|poemario)\b', 'Poesía'),
    (r'\b(cuentos|relatos)\b', 'Narrativa'),
    (r'\b(novela|narrativa|trilogia|saga|thriller|detectives?)\b', 'Narrativa'),
    # «diarios secretos» o «sus memorias» salen en tramas de ficción: solo cuenta el género nombrado.
    (r'\b(autobiograf\w+|biografia|libro de memorias)\b', 'Biografías y memorias'),
    # «historia», «estudio» o «análisis» salen en casi cualquier sinopsis de novela: no deciden la materia.
    (r'\b(ensayo|ensayos|filosofia|psicoanalisis)\b', 'Ensayo'),
)
JSONLD = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)
BLOCK = re.compile(r'</?(?:p|div|li|ul|ol|dt|dd|dl|th|td|tr|table|section|article|h[1-6]|span|strong|b|em|i|a|label|small|br)\b[^>]*>', re.I)


def reviewed_hosts(source: dict) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Hosts revisados de una fuente genérica; lanza si la configuración se aparta de ellos."""
    known = REVIEWED.get(source.get('id', ''))
    if not known or tuple(source.get('hosts', ())) != known[0] or tuple(source.get('cover_hosts', ())) != known[1]:
        raise SourceError('Conector editorial genérico no revisado')
    return known


def _text(fragment: str) -> str:
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', fragment)).split())


def generic_links(source: dict, document: str, index: str) -> list[str]:
    """Fichas de libro enlazadas desde un índice de novedades (cada ficha una sola vez)."""
    hosts, _ = reviewed_hosts(source)
    path_rule = re.compile(source['product_path'])
    links: list[str] = []
    for href in re.findall(r'href=["\']([^"\']+)["\']', document):
        parts = urlsplit(urljoin(index, html.unescape(href)))
        if (parts.scheme == 'https' and parts.hostname in hosts and not parts.query
                and not parts.username and not parts.password and path_rule.fullmatch(parts.path)):
            url = 'https://' + parts.hostname + parts.path
            if url not in links:
                links.append(url)
    return links


def _nodes(document: str) -> list[dict]:
    found: list[dict] = []
    for raw in JSONLD.findall(document):
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        stack = list(data) if isinstance(data, list) else [data]
        while stack:
            node = stack.pop(0)
            if isinstance(node, dict):
                found.append(node)
                stack.extend(v for v in (node.get('@graph') or []) if isinstance(v, dict))
    return found


def _is_type(node: dict, name: str) -> bool:
    kind = node.get('@type')
    return name in (kind if isinstance(kind, list) else [kind])


def _names(value) -> list[str]:
    out = []
    for item in value if isinstance(value, list) else [value]:
        name = item.get('name') if isinstance(item, dict) else item
        if isinstance(name, str) and name.strip():
            out.append(' '.join(html.unescape(name).split()))
    return list(dict.fromkeys(out))


def _meta(document: str, prop: str) -> str:
    for tag in re.findall(r'<meta\b[^>]*>', document):
        if re.search(r'(?:property|name)=["\']' + re.escape(prop) + r'["\']', tag):
            content = re.search(r'content=["\']([^"\']*)["\']', tag)
            if content:
                return html.unescape(content.group(1)).strip()
    return ''


def _canonical(document: str) -> list[str]:
    out = []
    for tag in re.findall(r'<link\b[^>]*>', document):
        if re.search(r'rel=["\']canonical["\']', tag):
            href = re.search(r'href=["\']([^"\']*)["\']', tag)
            out.append(html.unescape(href.group(1)) if href else '')
    return out


def _format(text: str):
    folded = normalize_text(str(text).rsplit('/', 1)[-1])
    for words, ident in FORMATS:
        if any(normalize_text(w) in folded for w in words):
            return ident
    return None


def _date(value: str):
    value = str(value or '').strip()
    match = re.fullmatch(r'(\d{1,2})[/.-](\d{1,2})[/.-](20\d{2})', value)
    if match:
        value = f'{match.group(3)}-{int(match.group(2)):02d}-{int(match.group(1)):02d}'
    elif match := re.fullmatch(r'(\d{1,2})[/.-](20\d{2})', value):
        value = f'{match.group(2)}-{int(match.group(1)):02d}'
    elif re.match(r'20\d{2}-\d{2}-\d{2}', value):
        value = value[:10]
    iso, precision = edition_date(value)
    return (iso, precision) if iso else (None, 'desconocida')


def _spanish_date(value: str):
    match = re.search(r'(\d{1,2})\s+(?:de\s+)?([a-záéíóú]+)[\s,]+(?:de\s+)?(20\d{2})', value, re.I)
    if match and normalize_text(match.group(2)) in MONTHS:
        return _date(f'{match.group(3)}-{MONTHS[normalize_text(match.group(2))]:02d}-{int(match.group(1)):02d}')
    match = re.search(r'([a-záéíóú]+)[\s,]+(?:de\s+)?(20\d{2})', value, re.I)
    if match and normalize_text(match.group(1)) in MONTHS:
        return _date(f'{match.group(2)}-{MONTHS[normalize_text(match.group(1))]:02d}')
    return _date(value)


def _euros(value: str):
    match = re.search(r'(\d+(?:[.,]\d{1,2})?)', str(value))
    if not match:
        return None
    try:
        return int((Decimal(match.group(1).replace(',', '.')) * 100).to_integral_value())
    except InvalidOperation:
        return None


def _lines(document: str) -> list[str]:
    body = re.sub(r'<(script|style|noscript|svg)\b.*?</\1>', ' ', document, flags=re.S | re.I)
    body = html.unescape(re.sub(r'<[^>]+>', ' ', BLOCK.sub('\n', body)))
    return [' '.join(line.split()) for line in body.split('\n') if line.strip()]


def ficha_fields(document: str) -> dict[str, str]:
    """Pares etiqueta → valor de la ficha técnica de la página; gana la primera aparición de cada campo."""
    lines = _lines(document)
    found: dict[str, str] = {}
    for index, line in enumerate(lines):
        head, sep, tail = line.partition(':')
        key = LABEL_OF.get(normalize_text(head if sep else line))
        if not key or key in found:
            continue
        value = tail.strip() if sep and tail.strip() else (lines[index + 1] if index + 1 < len(lines) else '')
        if value and len(value) <= 120 and not (value.endswith(':') or LABEL_OF.get(normalize_text(value.rstrip(':')))):
            found[key] = value
    return found


def _regex(source: dict, name: str, document: str) -> str:
    pattern = (source.get('regex') or {}).get(name)
    match = re.search(pattern, document, re.S) if pattern else None
    return _text(match.group(1)) if match else ''


def _synopsis_html(source: dict, document: str, fallback: str) -> str:
    """Párrafos de la sinopsis: expresión del perfil, encabezado «Sinopsis», o la descripción declarada."""
    pattern = (source.get('regex') or {}).get('sinopsis')
    if pattern and (match := re.search(pattern, document, re.S)) and len(_text(match.group(1)).split()) >= 10:
        return match.group(1)
    for match in re.finditer(r'<h[1-6][^>]*>(.*?)</h[1-6]>', document, re.S):
        if normalize_text(_text(match.group(1))) in SYNOPSIS_HEADINGS:
            tail = document[match.end():match.end() + 12000]
            stop = re.search(r'<h[1-6]\b', tail)
            block = tail[:stop.start()] if stop else tail
            if len(_text(block).split()) >= 10:
                return block
    return '<p>' + html.escape(fallback) + '</p>' if fallback else ''


def _infer_subject(*texts: str) -> list[str]:
    # Gana la materia con más apariciones: un «poema» suelto en la sinopsis no convierte una novela en poesía.
    folded = normalize_text(' '.join(texts))
    scores = {}
    for pattern, subject in SUBJECT_RULES:
        scores[subject] = scores.get(subject, 0) + len(re.findall(pattern, folded))
    best = max(scores.values(), default=0)
    return [next(subject for subject, score in scores.items() if score == best)] if best else []


def _authors(source: dict, document: str, book: dict, title_end: int) -> list[str]:
    names = _names(book.get('author'))
    pattern = source.get('author_link')
    if not names and pattern:
        area = document[title_end:title_end + 6000]
        found = [_text(m.group(1)) for m in re.finditer(r'<a\b[^>]*href=["\'](?:https://[^/"\']+)?' + pattern + r'[^"\']*["\'][^>]*>(.*?)</a>', area, re.S)]
        names = list(dict.fromkeys(n for n in found if n))
    if source.get('author_order') == 'last_first':
        # «Apellido, Nombre» -> «Nombre Apellido»; un nombre sin coma (p. ej. una entidad) se deja como está.
        names = [' '.join(reversed([part.strip() for part in name.split(',', 1)])) if ',' in name else name for name in names]
    return names


def generic_edition(source: dict, document: str, url: str) -> dict:
    """Edición de una ficha editorial; lanza SourceError si falta algo comprobable."""
    hosts, cover_hosts = reviewed_hosts(source)
    parts = urlsplit(url)
    if parts.hostname not in hosts or not re.fullmatch(source['product_path'], parts.path):
        raise SourceError('Ficha editorial no reconocida')
    canonicals = _canonical(document)
    if len(canonicals) > 1 or (canonicals and canonicals[0].rstrip('/') != url.rstrip('/')):
        raise SourceError('La ficha no conserva la edición canónica esperada')
    nodes = _nodes(document)
    book = next((n for n in nodes if (_is_type(n, 'Book') or _is_type(n, 'Product'))
                 and (n.get('isbn') or n.get('gtin13') or n.get('sku'))), None) or {}
    ficha = ficha_fields(document)
    h1 = re.search(r'<h1\b[^>]*>(.*?)</h1>', document, re.S)
    title = clean_title(str(book.get('name') or (_text(h1.group(1)) if h1 else '')))
    authors = _authors(source, document, book, h1.end() if h1 else 0)
    publisher = (_names(book.get('publisher')) or [source.get('default_publisher', '')])[0]
    isbn = next((valid for valid in (isbn13(str(c or '')) for c in (book.get('isbn'), book.get('gtin13'), book.get('sku'), ficha.get('isbn'))) if valid), None)
    if not (isbn and title and authors and publisher):
        raise SourceError('Faltan título, autoría, sello o ISBN comprobable')
    if not isbn.startswith(('97884', '97913')):
        raise SourceError('ISBN fuera del registro español')
    published, precision = _date(book.get('datePublished', ''))
    if not published and ficha.get('fecha'):
        published, precision = _spanish_date(ficha['fecha'])
    if not published and (extra := _regex(source, 'fecha', document)):
        published, precision = _spanish_date(extra)
    if not published:
        raise SourceError('Fecha editorial ausente o inválida')
    format_id = (_format(str(book.get('bookFormat', ''))) or _format(ficha.get('formato', ''))
                 or _format(_regex(source, 'formato', document)) or _format(source.get('default_format', '')))
    if not format_id:
        raise SourceError('Encuadernación desconocida o no física')
    binding = 'Tapa dura' if format_id == 'tapa-dura' else 'Tapa blanda'
    sources = {'jsonld': book.get('image') if isinstance(book.get('image'), str) else (book.get('image') or {}).get('url', '') if isinstance(book.get('image'), dict) else '',
               'og': _meta(document, 'og:image'), 'regex': _regex(source, 'portada', document)}
    image = next((urljoin(url, sources[k]) for k in source.get('cover_order', ('regex', 'og', 'jsonld')) if sources.get(k)), '')
    image_parts = urlsplit(image)
    if image_parts.scheme != 'https' or image_parts.hostname not in cover_hosts:
        raise SourceError('Portada editorial ausente')
    synopsis_html = _synopsis_html(source, document, str(book.get('description') or _meta(document, 'og:description')))
    synopsis = _text(synopsis_html)
    if not _looks_spanish(synopsis or title):
        raise SourceError('Edición no identificada como castellano')
    count = re.sub(r'\D', '', str(book.get('numberOfPages') or ficha.get('paginas') or _regex(source, 'paginas', document)))
    segments = [s for s in parts.path.split('/') if s]
    group = source.get('collection_from_path')
    collection_key = segments[group] if isinstance(group, int) and len(segments) > group else ''
    collection = (source.get('collection_names', {}).get(collection_key) or ficha.get('coleccion')
                  or collection_key.replace('-', ' ').capitalize())
    subject = source.get('subject_by_collection', {}).get(collection_key)
    genre = book.get('genre')
    thema = (ficha.get('thema') or '').strip().upper()
    subject = subject or next((name for prefix, name in THEMA_SUBJECTS if thema.startswith(prefix)), None)
    subjects = [s for s in ([subject] if subject else _names(genre) if genre else []) if s] or _infer_subject(title, synopsis)
    keywords = book.get('keywords')
    keywords = ', '.join(keywords) if isinstance(keywords, list) else str(keywords or '')
    offers = book.get('offers')
    price = next((_euros(o['price']) for o in (offers if isinstance(offers, list) else [offers])
                  if isinstance(o, dict) and str(o.get('priceCurrency', 'EUR')).upper() == 'EUR' and o.get('price') not in (None, '')), None)
    if price is None:
        price = _euros(ficha['pvp']) if ficha.get('pvp') and '€' in ficha['pvp'] else None
    return {'isbn13': isbn, 'titulo': title, 'autores': authors, 'editorial': publisher,
            'fecha_publicacion_edicion': published, 'precision_fecha': precision,
            'idioma': 'es', 'formato_edicion': format_id, 'encuadernacion': binding,
            'numero_paginas': int(count) if count else None,
            'materias': subjects[:1], 'edad_recomendada': '',
            'portada_fuente_url': image, 'fuente_bibliografica_url': url,
            'fuentes_autores': {},
            'coleccion': collection,
            'sinopsis_breve': editorial_excerpt(synopsis_html),
            'sinopsis_completa': editorial_synopsis(synopsis_html),
            'palabras_clave': keyword_list(keywords),
            'pvp_centimos': price}
