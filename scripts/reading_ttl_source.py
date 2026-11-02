"""Ficha bibliográfica por ISBN en todostuslibros.com (CEGAL, librerías de España).

El radar de Amazon dice qué novedades y próximos lanzamientos faltan en el catálogo, pero de Amazon
solo se usa el ISBN y el mismo día (su licencia no permite guardar más). Los datos de la ficha salen
de aquí: título, autoría, sello, fecha, encuadernación, páginas, PVP, categorías y la descripción de
la editorial. La imagen de esta web lleva marca de agua y no se usa: la cubierta es tipográfica y
propia (`typographic_cover`), hasta que un conector editorial aporte la cubierta oficial.

Misma salida que `penguin_edition`, `planeta_edition` y `generic_edition`. Sin red propia.
"""
from __future__ import annotations

import hashlib
import html
import io
import json
import re
import textwrap
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageDraw, ImageFont

from reading_editorial_sources import SourceError, editorial_excerpt, editorial_synopsis
from reading_generic_source import _euros, _format, _text
from reading_intake_core import clean_title, edition_date, isbn13, normalize_text

HOST = 'www.todostuslibros.com'
PRODUCT_PATH = re.compile(r'/libros/[a-z0-9-]+_(97[89][0-9-]{10,14})')
JSONLD = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)
MAKER = re.compile(r'class="block-dato security"[^>]*>\s*<strong>([^<]+)<br', re.S)
LEGAL = re.compile(r',?\s+(?:S\.?\s?A\.?\s?U\.?|S\.?\s?L\.?\s?U?\.?|S\.?\s?A\.?)$', re.I)
# Categorías de la librería (Thema en castellano) -> materia que entiende `classify`. Gana el orden:
# los géneros concretos van antes que la narrativa general; se guardan como mucho dos.
CATEGORY_RULES = (
    (r'ciencia ficcion', 'ciencia ficcion'),
    (r'fantasia', 'fantasia'),
    (r'romantic|amor', 'novela romantica'),
    (r'policiac|thriller|novela negra|crimen|misterio|suspense', 'misterio'),
    (r'(?:novela|ficcion|aventura) historica', 'novela historica'),
    (r'terror|miedo|fantasmas', 'terror'),
    (r'poesia', 'poesia'),
    (r'comic|novela grafica|manga', 'comic'),
    (r'infantil', 'infantil'),
    (r'juvenil|adolescen', 'literatura juvenil'),
    (r'biografi|memorias', 'biografias y memorias'),
    (r'cuentos|relatos', 'relatos'),
    (r'ficcion|novela|narrativa', 'narrativa'),
    (r'filosof', 'filosofia'),
    (r'psicolog', 'psicologia'),
    (r'historia', 'historia'),
    (r'cocina|gastronom', 'cocina'),
    (r'autoayuda|desarrollo personal|superacion', 'autoayuda'),
    (r'economia|empresa|negocio|finanzas', 'economia'),
    (r'salud|dieta|nutricion', 'salud'),
    (r'crianza|padres', 'para padres'),
    (r'ciencia|divulgacion', 'ciencia'),
    (r'ensayo', 'ensayo'),
)
FONTS = Path(__file__).resolve().parents[1] / 'assets' / 'fonts'
# Las fuentes de la web (con tildes y eñes), como las tarjetas sociales.
SERIF, SANS = FONTS / 'cg-normal-latin.woff2', FONTS / 'inter-normal-latin.woff2'
PALETTE = ((33, 47, 61), (88, 24, 31), (24, 66, 56), (52, 40, 82), (102, 64, 22), (20, 54, 92), (70, 70, 70))


def ttl_url(isbn: str) -> str:
    """Dirección directa de la ficha por ISBN: la web redirige a la ficha canónica."""
    valid = isbn13(isbn)
    if not valid:
        raise SourceError('ISBN no válido')
    return f'https://{HOST}/libros/x_{valid}'


def url_isbn(url: str) -> str | None:
    return isbn13(url.rsplit('_', 1)[-1].replace('-', '')) if urlsplit(url).hostname == HOST else None


def _dd(document: str, label: str) -> str:
    match = re.search(r'<dt>\s*' + label + r'\s*:?\s*</dt>\s*<dd>(.*?)</dd>', document, re.S | re.I)
    return _text(match.group(1)) if match else ''


def _book(document: str) -> dict:
    for raw in JSONLD.findall(document):
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        for node in data if isinstance(data, list) else [data]:
            if isinstance(node, dict) and node.get('@type') == 'Book':
                return node
    return {}


def _authors(book: dict, document: str) -> list[str]:
    value = book.get('author')
    names = [a.get('name', '') if isinstance(a, dict) else str(a) for a in (value if isinstance(value, list) else [value]) if a]
    if not names:
        names = [n.strip() for n in _dd(document, 'Autoría').split(';')]
    # «Apellido, Nombre» -> «Nombre Apellido».
    names = [' '.join(reversed([p.strip() for p in n.split(',', 1)])) if ',' in n else n for n in names]
    return list(dict.fromkeys(' '.join(html.unescape(n).split()) for n in names if n.strip()))


def subjects(categories: str) -> list[str]:
    found = []
    for category in categories.split('|'):
        folded = normalize_text(category)
        for pattern, subject in CATEGORY_RULES:
            if re.search(pattern, folded) and subject not in found:
                found.append(subject)
                break
    return found[:2]


def ttl_edition(document: str, url: str) -> dict:
    """Edición de una ficha de todostuslibros; lanza SourceError si falta algo comprobable."""
    book = _book(document)
    canonical = re.search(r'<link rel="canonical" href="([^"]+)"', document)
    page = html.unescape(canonical.group(1)) if canonical else str(book.get('url', ''))
    parts = urlsplit(page)
    if parts.scheme != 'https' or parts.hostname != HOST or not PRODUCT_PATH.fullmatch(parts.path):
        raise SourceError('Ficha de todostuslibros no reconocida')
    edition = next((w for w in book.get('workExample') or [] if isinstance(w, dict)), {})
    isbn = isbn13(str(edition.get('isbn', '')).replace('-', '')) or isbn13(_dd(document, 'EAN'))
    if not isbn or isbn != url_isbn(page) or (url_isbn(url) and url_isbn(url) != isbn):
        raise SourceError('El ISBN de la ficha no coincide con el pedido')
    if not isbn.startswith(('97884', '97913')):
        raise SourceError('ISBN fuera del registro español')
    if str(edition.get('inLanguage', '')).lower() not in ('spa', 'es'):
        raise SourceError('Edición no identificada como castellano')
    title = clean_title(html.unescape(str(book.get('name', ''))))
    authors = _authors(book, document)
    publisher = LEGAL.sub('', _dd(document, 'Editorial')).strip()
    # «Datos del fabricante» (seguridad de producto): la empresa responsable de la edición.
    maker = MAKER.search(document)
    group = LEGAL.sub('', re.sub(r'\s*\(.*?\)', '', html.unescape(maker.group(1)))).strip(' ,') if maker else ''
    if not (title and authors and publisher):
        raise SourceError('Faltan título, autoría o sello')
    day = re.fullmatch(r'(\d{2})-(\d{2})-(20\d{2})', _dd(document, 'Fecha publicación'))
    stamp = str(edition.get('datePublished', ''))[:10]
    published, precision = edition_date(f'{day.group(3)}-{day.group(2)}-{day.group(1)}' if day else stamp)
    if not published:
        raise SourceError('Fecha editorial ausente o inválida')
    format_id = _format(str(edition.get('bookFormat', ''))) or _format(_dd(document, 'Encuadernación'))
    if not format_id:
        raise SourceError('Encuadernación desconocida o no física')
    block = re.search(r'id="collapseSynopsis"[^>]*>(.*?)</div>', document, re.S)
    synopsis_html = block.group(1) if block else '<p>' + html.escape(str(book.get('description', ''))) + '</p>'
    offers = edition.get('offers') or []
    price = next((_euros(o.get('Price') or o.get('price')) for o in offers if isinstance(o, dict)
                  and str(o.get('priceCurrency', 'EUR')).upper() == 'EUR' and (o.get('Price') or o.get('price'))), None)
    count = re.sub(r'\D', '', str(edition.get('numberOfPages') or _dd(document, 'Nº páginas')))
    return {'isbn13': isbn, 'titulo': title, 'autores': authors, 'editorial': publisher,
            'grupo_editorial': group if 2 <= len(group) <= 80 else publisher,
            'fecha_publicacion_edicion': published, 'precision_fecha': precision,
            'idioma': 'es', 'formato_edicion': format_id,
            'encuadernacion': 'Tapa dura' if format_id == 'tapa-dura' else 'Tapa blanda',
            'numero_paginas': int(count) if count else None,
            'materias': subjects(_dd(document, 'Categorías')), 'edad_recomendada': '',
            # Sin imagen de la librería: la «fuente» de la cubierta tipográfica es la propia ficha.
            'portada_fuente_url': page, 'fuente_bibliografica_url': page,
            'fuentes_autores': {}, 'coleccion': _dd(document, 'Colección'),
            'sinopsis_breve': editorial_excerpt(synopsis_html),
            'sinopsis_completa': editorial_synopsis(synopsis_html),
            'palabras_clave': [], 'pvp_centimos': price if price and 100 <= price <= 20000 else None}


def _font(size: int, path: Path = SANS):
    return ImageFont.truetype(str(path), size)


def _lines(draw, text: str, font, width: int, limit: int) -> list[str]:
    for chars in range(28, 8, -1):
        lines = textwrap.wrap(text, chars)
        if all(draw.textlength(line, font=font) <= width for line in lines):
            return lines[:limit]
    return textwrap.wrap(text, 9)[:limit]


def typographic_cover(record: dict) -> tuple[bytes, bytes, tuple[int, int]]:
    """Cubierta propia (título, autoría y sello sobre un color fijo por ISBN): sin imagen de terceros."""
    width, height = 800, 1200
    seed = hashlib.sha256(record['isbn13'].encode()).digest()
    background = PALETTE[seed[0] % len(PALETTE)]
    image = Image.new('RGB', (width, height), background)
    draw = ImageDraw.Draw(image)
    accent = tuple(min(255, c + 120) for c in background)
    draw.rectangle((48, 48, width - 48, height - 48), outline=accent, width=4)
    y = 220
    title = _font(84, SERIF)
    for line in _lines(draw, record['titulo'], title, width - 180, 6):
        draw.text((width // 2, y), line, font=title, fill=(250, 246, 238), anchor='ma')
        y += 96
    draw.line((width // 2 - 80, y + 30, width // 2 + 80, y + 30), fill=accent, width=4)
    y += 80
    author = _font(40)
    for line in _lines(draw, ', '.join(record['autores']), author, width - 180, 3):
        draw.text((width // 2, y), line, font=author, fill=(235, 228, 214), anchor='ma')
        y += 54
    draw.text((width // 2, height - 130), record['editorial'], font=_font(32), fill=accent, anchor='ma')
    out = io.BytesIO()
    image.save(out, 'WEBP', quality=85, method=6)
    small = image.copy()
    small.thumbnail((320, 600))
    preview = io.BytesIO()
    small.save(preview, 'WEBP', quality=80, method=6)
    return out.getvalue(), preview.getvalue(), (width, height)
