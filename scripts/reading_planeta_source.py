"""Segunda fuente editorial: fichas públicas de Planeta de Libros (España).

Misma salida que `penguin_edition` para reutilizar validación, portadas, sellos y publicación.
La ficha de Planeta no lleva el ISBN en la URL (`/libro-<slug>/<id>`): se lee de la «Ficha técnica»
y se valida su dígito de control. Las clases CSS llevan un sufijo con hash que cambia en cada
despliegue, así que se localizan por el nombre estable del módulo (`FichaLibro`, `fichaTecnica`...).
Sin modelos ni claves.
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from decimal import Decimal, InvalidOperation

from reading_intake_core import clean_title
from urllib.parse import urljoin, urlsplit

from reading_editorial_sources import SourceError, allowed_url, editorial_excerpt
from reading_intake_core import isbn13, normalize_text
from reading_taxonomy import keyword_list

HOST = 'www.planetadelibros.com'
COVER_HOSTS = ('proassetspdlcom.cdnstatics2.com',)
PRODUCT_PATH = re.compile(r'^/libro-[a-z0-9-]+/(\d{1,9})/?$')
AUTHOR_PATH = re.compile(r'^/autor/[a-z0-9-]+/\d+/?$')
MONTHS = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
          'septiembre': 9, 'setiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}
SPANISH = {'el', 'la', 'los', 'las', 'una', 'del', 'que', 'con', 'por', 'para', 'sus', 'pero', 'como', 'más', 'su', 'se', 'en', 'y'}
CATALAN = {'els', 'les', 'amb', 'dels', 'però', 'una', 'del', 'que', 'per', 'aquest', 'aquesta', 'també', 'com', 'més', 'seva', 'seus', 'i', 'és'}


class _CanonicalLinks(HTMLParser):
    """Read canonical link attributes without relying on HTML attribute order."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls: list[str | None] = []

    def handle_starttag(self, tag, attrs):
        if tag != 'link':
            return
        values = dict(attrs)
        if 'canonical' in (values.get('rel') or '').casefold().split():
            self.urls.append(values.get('href'))


def canonical_urls(document: str) -> list[str | None]:
    parser = _CanonicalLinks()
    parser.feed(document)
    return parser.urls


def _text(fragment: str) -> str:
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', fragment)).split())


def planeta_links(document: str, source: str) -> list[str]:
    """Fichas de libro enlazadas desde un índice de novedades (misma ficha una sola vez)."""
    links: list[str] = []
    for href in re.findall(r'href="([^"]+)"', document):
        url = urljoin(source, html.unescape(href))
        parts = urlsplit(url)
        if parts.hostname == HOST and not parts.query and PRODUCT_PATH.fullmatch(parts.path):
            normal = 'https://' + HOST + parts.path.rstrip('/')
            if normal not in links:
                links.append(normal)
    return links


def _ficha(document: str) -> dict[str, str]:
    start = document.find('fichaTecnicaTablesWrapper')
    if start < 0:
        return {}
    table = document[start:start + 20000]
    end = table.find('</section>')
    table = table if end < 0 else table[:end]
    return {normalize_text(_text(k)): _text(v) for k, v in re.findall(r'<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>', table, re.S)}


def _date(value: str):
    match = re.fullmatch(r'(\d{1,2})\s+(?:de\s+)?([a-záéíóú]+)\s+(?:de\s+)?(20\d{2})', value.strip(), re.I)
    if not match or normalize_text(match.group(2)) not in MONTHS:
        return None
    from datetime import date
    try:
        return date(int(match.group(3)), MONTHS[normalize_text(match.group(2))], int(match.group(1))).isoformat()
    except ValueError:
        return None


def _price(value: str):
    match = re.search(r'(\d+(?:[.,]\d{1,2})?)\s*€', html.unescape(value))
    if not match:
        return None
    try:
        return int((Decimal(match.group(1).replace(',', '.')) * 100).to_integral_value())
    except InvalidOperation:
        return None


def _looks_spanish(text: str) -> bool:
    words = re.findall(r'[a-záéíóúüñàèòç·]+', text.casefold())
    return len(words) >= 12 and sum(w in SPANISH for w in words) > sum(w in CATALAN - SPANISH for w in words) * 2


def planeta_edition(document: str, source: str) -> dict:
    """Edición seleccionada de una ficha de Planeta; lanza SourceError si falta algo comprobable."""
    parts = urlsplit(source)
    path = PRODUCT_PATH.fullmatch(parts.path) if parts.hostname == HOST else None
    if not path:
        raise SourceError('Ficha de Planeta no reconocida')
    canonicals = canonical_urls(document)
    if len(canonicals) > 1 or (canonicals and (not canonicals[0] or canonicals[0].rstrip('/') != source.rstrip('/'))):
        raise SourceError('La ficha no conserva la edición canónica esperada')
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', document, re.S)
    title = _text(h1.group(1)) if h1 else ''
    block = document[h1.end():h1.end() + 4000] if h1 else ''
    authors = list(dict.fromkeys(
        _text(m.group(2)) for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block[:block.find('</ul>') if '</ul>' in block else len(block)], re.S)
        if (urlsplit(urljoin(source, html.unescape(m.group(1)))).hostname == HOST
            and AUTHOR_PATH.fullmatch(urlsplit(urljoin(source, html.unescape(m.group(1)))).path))))
    fields = _ficha(document)
    expected = isbn13(fields.get('isbn', ''))
    publisher = fields.get('editorial', '')
    if not title or not authors or not publisher or not expected:
        raise SourceError('Faltan título, autoría, sello o ISBN comprobable')
    if not expected.startswith(('97884', '97913')):
        raise SourceError('ISBN fuera del registro español')
    published = _date(fields.get('publicacion', ''))
    if not published:
        raise SourceError('Fecha editorial ausente o inválida')
    binding = fields.get('presentacion', '')
    physical = normalize_text(binding)
    format_id = ('tapa-dura' if any(x in physical for x in ('tapa dura', 'cartone')) else
                 'tapa-blanda' if any(x in physical for x in ('rustica', 'tapa blanda', 'bolsillo')) else None)
    if not format_id:
        raise SourceError('Encuadernación desconocida o no física')
    cover = re.search(r'<link[^>]*rel="preload"[^>]*href="(https://[^"]+/usuaris/libros/thumbs/[^"]+\.(?:webp|jpg|png))"', document)
    image = cover.group(1) if cover else ''
    if not image or urlsplit(image).hostname not in COVER_HOSTS:
        raise SourceError('Portada editorial ausente')
    synopsis_match = re.search(r'sinopsis__text[^>]*>(.*?)</article>', document, re.S)
    synopsis_html = synopsis_match.group(1) if synopsis_match else ''
    synopsis = _text(synopsis_html)
    if not _looks_spanish(synopsis or title):
        raise SourceError('Edición no identificada como castellano')
    price = None
    for href, label in re.findall(r'<a[^>]*href="([^"]*soporte=' + path.group(1) + r'[^"]*)"[^>]*>(.*?)</a>', document, re.S):
        price = _price(_text(label))
        break
    count = fields.get('paginas', '')
    topics = re.search(r'<th[^>]*>\s*Tem[aá]ticas?\s*</th>\s*<td[^>]*>(.*?)</td>', document, re.S)
    topic_names = [_text(x) for x in re.findall(r'<a[^>]*>(.*?)</a>', topics.group(1), re.S)] if topics else []
    author_sources = {}
    for m in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', block, re.S):
        url = urljoin(source, html.unescape(m.group(1)))
        if urlsplit(url).hostname == HOST and AUTHOR_PATH.fullmatch(urlsplit(url).path) and _text(m.group(2)) in authors:
            allowed_url(url, (HOST,))
            author_sources.setdefault(_text(m.group(2)), url)
    if any(author not in author_sources for author in authors):
        raise SourceError('Falta perfil oficial de Planeta para la autoría')
    return {'isbn13': expected, 'titulo': clean_title(title), 'autores': authors, 'editorial': publisher,
            'fecha_publicacion_edicion': published, 'precision_fecha': 'dia',
            'idioma': 'es', 'formato_edicion': format_id, 'encuadernacion': binding,
            'numero_paginas': int(count) if count.isdigit() else None,
            'materias': topic_names[:1],
            'edad_recomendada': '',
            'portada_fuente_url': image, 'fuente_bibliografica_url': source,
            'fuentes_autores': {a: author_sources[a] for a in authors},
            'coleccion': fields.get('coleccion', ''),
            'sinopsis_breve': editorial_excerpt(synopsis_html),
            'palabras_clave': keyword_list(', '.join(topic_names)),
            'pvp_centimos': price}
