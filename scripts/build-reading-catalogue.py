#!/usr/bin/env python3
"""Catálogo estático de lectura. Una obra, una URL; datos privados fuera del HTML.

python scripts/build-reading-catalogue.py [--check] [--root .] [--data ruta.json]
La carga desde Drive y Pinterest pertenecen a fases posteriores.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_shell import inject_shell_auto
from reading_intake_core import strip_shouting, decode_text_entities

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://davidportodiaz.com"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
TYPES = {"genero": "Género", "tematica": "Temática", "temporada": "Temporada", "edad": "Edad", "contenido": "Contenido", "epoca": "Época"}
PRICE_FIELDS = {'precio_centimos', 'precio_referencia_centimos'}
# Una oferta solo se muestra si Amazon la confirmó hace como mucho estos días; después desaparece sola.
OFFER_MAX_DAYS = 3
BOOK_FIELDS = set("id slug titulo autores descripcion_breve estado portada_local portada_fuente_url portada_edicion_verificada autorizacion_o_base_uso portada_fecha_revision portada_ancho portada_alto fuente_bibliografica_url fecha_verificacion descripcion_original_confirmada url_amazon_afiliada isbn13 edicion editorial fecha_publicacion anio_publicacion numero_paginas fuente_publicacion_url idioma edad_recomendada fuente_edad_url avisos_contenido lectura_personal_confirmada evidencia_lectura autoria_propia resenas fragmento_url fecha_actualizacion editorial_catalogo_slug pvp_centimos pvp_fecha_verificacion audio_descripcion audio_voz formatos_compra fragmento_texto fragmento_uso_autorizado fragmento_base_uso audio_fragmento".split())
FORMATS = {"tapa-blanda": "Tapa blanda", "tapa-dura": "Tapa dura", "ebook": "Kindle", "audiolibro": "Audiolibro"}
BOOK_FIELDS.update({'editorial_slug', 'formato_edicion', 'amazon_busqueda_isbn', 'fecha_publicacion_parcial', 'precios_amazon_revision', 'formatos_amazon_buscados', 'formatos_pagina_buscados', 'portadas_amazon_buscadas', 'portada_sustituida'})
BOOK_FIELDS.update({'sinopsis_breve', 'sinopsis_fuente_url', 'sinopsis_tipo', 'categorias_excluidas', 'sinopsis_completa'})


class ValidationError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise ValidationError(message)


def esc(value):
    return html.escape(str(value), quote=True)


def https(raw):
    if not isinstance(raw, str) or re.search(r"[\s<>\x00-\x1f]", raw):
        return False
    try:
        p = urlparse(raw)
        return p.scheme == "https" and bool(p.hostname) and not p.username and not p.password and p.port in (None, 443)
    except ValueError:
        return False


def day(raw, name):
    require(isinstance(raw, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw)), f"{name}: fecha ISO obligatoria")
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValidationError(f"{name}: fecha inválida") from exc


def valid_isbn(value):
    return isinstance(value, str) and bool(re.fullmatch(r"97[89][0-9]{10}", value)) and sum(int(n) * (1 if i % 2 == 0 else 3) for i, n in enumerate(value)) % 10 == 0


def validate(data, root):
    require(isinstance(data, dict) and data.get("schema_version") == 1, "schema_version debe ser 1")
    require(set(data) == {"schema_version", "categorias", "libros", "libro_categorias"}, "Campos raíz desconocidos o ausentes")
    cats, books, relations = data["categorias"], data["libros"], data["libro_categorias"]
    require(all(isinstance(items, list) for items in (cats, books, relations)), "Las entidades deben ser listas")
    ids, slugs = set(), set()
    for c in cats:
        require(isinstance(c, dict) and set(c) == {"id", "slug", "nombre", "tipo", "descripcion", "orden", "activa"}, "Categoría: columnas inválidas")
        require(all(isinstance(c[k], str) and c[k].strip() for k in ("id", "slug", "nombre", "tipo", "descripcion")), "Categoría incompleta")
        require(SLUG.fullmatch(c["id"]) and SLUG.fullmatch(c["slug"]) and c["id"] not in ids and c["slug"] not in slugs, "Categoría duplicada o clave inválida")
        require(c["tipo"] in TYPES and type(c["activa"]) is bool and type(c["orden"]) is int, "Categoría: tipo/orden/activa inválidos")
        ids.add(c["id"]); slugs.add(c["slug"])
    book_ids, book_slugs, isbns, covers, hashes, amazon_urls, works, descriptions = (set() for _ in range(8))
    for b in books:
        require(isinstance(b, dict) and not set(b) - BOOK_FIELDS, "Libro: campos desconocidos")
        for key in ("id", "slug", "titulo", "estado"):
            require(isinstance(b.get(key), str) and b[key].strip(), f"Libro sin {key}")
        name = b["id"]
        require(SLUG.fullmatch(name) and name not in book_ids and SLUG.fullmatch(b["slug"]) and b["slug"] not in book_slugs, f"{name}: id/slug inválido o duplicado")
        book_ids.add(name); book_slugs.add(b["slug"])
        require(b["estado"] in {"borrador", "listo", "publicado"}, f"{name}: estado inválido")
        require(isinstance(b.get("autores"), list) and b["autores"] and all(isinstance(a, str) and a.strip() for a in b["autores"]), f"{name}: autores debe ser una lista")
        work = (b['titulo'].strip().casefold(), tuple(sorted(a.strip().casefold() for a in b['autores'])))
        require(work not in works, f"{name}: obra duplicada; reunir las ediciones en una ficha")
        works.add(work)
        if b.get("isbn13"):
            require(valid_isbn(b["isbn13"]) and b["isbn13"] not in isbns, f"{name}: ISBN inválido o duplicado")
            isbns.add(b["isbn13"])
        if b.get('editorial_slug'):
            require(SLUG.fullmatch(b['editorial_slug']) and (root / 'editoriales' / b['editorial_slug'] / 'index.html').is_file(), f'{name}: editorial inexistente')
        if b.get('editorial_catalogo_slug'):
            require(not b.get('editorial_slug') and b.get('editorial'), f'{name}: la editorial del catálogo excluye la del directorio')
            require(b['editorial_catalogo_slug'] in {p['slug'] for p in publisher_records(root)}, f'{name}: sello del catálogo inexistente')
        if b.get('formato_edicion'):
            require(b['formato_edicion'] in FORMATS, f'{name}: formato de edición inválido')
        if b.get('fecha_publicacion_parcial'):
            partial = b['fecha_publicacion_parcial']
            require(isinstance(partial, str) and bool(re.fullmatch(r'\d{4}-\d{2}', partial)), f'{name}: mes inválido')
            day(partial + '-01', name + '.mes')
            require(not b.get('fecha_publicacion') and b.get('anio_publicacion') == int(partial[:4]), f'{name}: fechas incompatibles')
        if b.get('amazon_busqueda_isbn'):
            raw = b['amazon_busqueda_isbn']
            p = urlparse(raw); query = parse_qs(p.query)
            require(https(raw) and p.hostname in {'www.amazon.es', 'amazon.es'} and p.path == '/s' and not p.fragment and set(query) == {'k', 'tag'} and query['k'] == [b.get('isbn13')] and len(query['tag']) == 1 and bool(re.fullmatch(r'[A-Za-z0-9-]+', query['tag'][0])), f'{name}: búsqueda Amazon inválida')
        if b["estado"] == "borrador":
            continue
        for key in ("descripcion_breve", "portada_local", "portada_fuente_url", "autorizacion_o_base_uso", "fuente_bibliografica_url", "fecha_verificacion", "portada_fecha_revision", "fecha_actualizacion", "edicion"):
            require(isinstance(b.get(key), str) and b[key].strip(), f"{name}: falta {key}")
        require(b.get("portada_edicion_verificada") is True and b.get("descripcion_original_confirmada") is True, f"{name}: falta confirmación de edición/descripción original")
        require(type(b.get("lectura_personal_confirmada", False)) is bool and type(b.get("autoria_propia", False)) is bool, f"{name}: confirmaciones deben ser booleanas")
        require(40 <= len(b["descripcion_breve"]) <= 1200, f"{name}: descripción debe tener 40–1200 caracteres")
        require(b['descripcion_breve'].strip().casefold() not in descriptions, f"{name}: descripción duplicada")
        descriptions.add(b['descripcion_breve'].strip().casefold())
        if b.get('sinopsis_breve'):
            require(isinstance(b['sinopsis_breve'], str) and 30 <= len(b['sinopsis_breve']) <= 700, f'{name}: sinopsis inválida')
            require(b.get('sinopsis_tipo') in {'extracto_editorial', 'resumen_propio'} and https(b.get('sinopsis_fuente_url')), f'{name}: sinopsis sin procedencia')
        if 'sinopsis_completa' in b:
            require(isinstance(b['sinopsis_completa'], str) and 60 <= len(b['sinopsis_completa']) <= 4500 and https(b.get('sinopsis_fuente_url')), f'{name}: sinopsis completa inválida')
        if b.get('categorias_excluidas'):
            require(isinstance(b['categorias_excluidas'], list) and all(c in ids for c in b['categorias_excluidas']), f'{name}: exclusiones de categorías inválidas')
        for key in ("portada_fuente_url", "fuente_bibliografica_url", "fuente_publicacion_url", "fuente_edad_url", "fragmento_url"):
            if b.get(key):
                require(https(b[key]), f"{name}: {key} debe ser HTTPS")
        for key in ("fecha_verificacion", "portada_fecha_revision", "fecha_actualizacion"):
            day(b[key], name + "." + key)
        if b.get("fecha_publicacion"):
            day(b["fecha_publicacion"], name + ".fecha_publicacion")
            require(https(b.get("fuente_publicacion_url")), f"{name}: publicación sin fuente")
        if b.get("edad_recomendada"):
            require(isinstance(b["edad_recomendada"], str) and https(b.get("fuente_edad_url")), f"{name}: edad sin fuente")
        if b.get("lectura_personal_confirmada"):
            require(isinstance(b.get("evidencia_lectura"), str) and b["evidencia_lectura"].strip(), f"{name}: lectura personal sin evidencia")
        for key in ("editorial", "idioma", "avisos_contenido"):
            require(not b.get(key) or isinstance(b[key], str), f"{name}: {key} debe ser texto")
        for key in ('anio_publicacion', 'numero_paginas'):
            require(not b.get(key) or type(b[key]) is int and b[key] > 0, f'{name}: {key} debe ser entero positivo')
        for field in ('precios_amazon_revision', 'formatos_amazon_buscados', 'formatos_pagina_buscados', 'portadas_amazon_buscadas'):
            if b.get(field):
                day(b[field], name + '.' + field)
        if b.get('pvp_centimos') is not None:
            require(type(b['pvp_centimos']) is int and 100 <= b['pvp_centimos'] <= 20000, f'{name}: pvp_centimos fuera de rango')
            day(b.get('pvp_fecha_verificacion'), name + '.pvp_fecha_verificacion')
        if b.get('audio_descripcion'):
            require(bool(re.fullmatch(r'/assets/reading-audio/[a-z0-9-]+\.mp3', b['audio_descripcion'])) and (root / b['audio_descripcion'].lstrip('/')).is_file(), f'{name}: audio local inválido o ausente')
        cover = b["portada_local"]
        require(bool(re.fullmatch(r"/assets/reading-covers/[a-z0-9-]+\.(?:jpg|jpeg|png|webp)", cover)), f"{name}: portada fuera de assets/reading-covers")
        file = (root / cover.lstrip("/")).resolve()
        require(file.is_relative_to(root.resolve()) and file.is_file(), f"{name}: portada local inexistente")
        digest = hashlib.sha256(file.read_bytes()).hexdigest()
        require(cover not in covers and digest not in hashes, f"{name}: portada duplicada")
        covers.add(cover); hashes.add(digest)
        require(all(type(b.get(k)) is int and b[k] > 0 for k in ("portada_ancho", "portada_alto")), f"{name}: dimensiones de portada obligatorias")
        try:
            with Image.open(file) as img:
                require(img.size == (b['portada_ancho'], b['portada_alto']), f"{name}: dimensiones no coinciden con la portada")
                require(img.format in {'JPEG', 'PNG', 'WEBP'}, f"{name}: formato de portada inválido")
                img.verify()
        except OSError as exc:
            raise ValidationError(f"{name}: portada corrupta") from exc
        if b.get("url_amazon_afiliada"):
            url = b["url_amazon_afiliada"]
            require(https(url), f"{name}: URL Amazon inválida")
            parsed = urlparse(url)
            direct = parsed.hostname in {"amazon.es", "www.amazon.es"} and bool(re.fullmatch(r"/(?:[^/]+/)?(?:dp|gp/product)/[A-Z0-9]{10}/?", parsed.path)) and bool(re.fullmatch(r"[a-zA-Z0-9-]+", parse_qs(parsed.query).get("tag", [""])[0]))
            short = parsed.hostname == "amzn.to" and bool(re.fullmatch(r"/[A-Za-z0-9]+", parsed.path)) and not parsed.query
            require(direct or short, f"{name}: se requiere enlace de producto Amazon.es con tag o enlace corto verificado")
            product = (parsed.hostname, parsed.path) if short else re.search(r"(?:dp|gp/product)/([A-Z0-9]{10})", parsed.path).group(1)
            require(product not in amazon_urls, f"{name}: producto Amazon duplicado")
            amazon_urls.add(product)
        formats = b.get('formatos_compra', [])
        require(isinstance(formats, list), f'{name}: formatos_compra debe ser una lista')
        seen_formats = set()
        for option in formats:
            require(isinstance(option, dict) and set(option) - PRICE_FIELDS == {'formato', 'url', 'fuente_url', 'fecha_verificacion'}, f'{name}: formato de compra inválido')
            for key in PRICE_FIELDS:
                require(key not in option or (type(option[key]) is int and 100 <= option[key] <= 100000), f'{name}: precio de formato fuera de rango')
            require(option['formato'] in FORMATS and option['formato'] not in seen_formats, f'{name}: formato duplicado o desconocido')
            seen_formats.add(option['formato'])
            p = urlparse(option['url'])
            require(https(option['url']) and p.hostname in {'www.amazon.es', 'amazon.es'} and bool(re.fullmatch(r'/(?:[^/]+/)?(?:dp|gp/product)/[A-Z0-9]{10}/?', p.path)) and bool(re.fullmatch(r'[A-Za-z0-9-]+', parse_qs(p.query).get('tag', [''])[0])), f'{name}: enlace directo afiliado obligatorio por formato')
            require(https(option['fuente_url']), f'{name}: formato sin fuente')
            day(option['fecha_verificacion'], name + '.formato')
        if b.get('fragmento_texto') or b.get('audio_fragmento'):
            require(b.get('fragmento_uso_autorizado') is True and bool(b.get('fragmento_base_uso')) and https(b.get('fragmento_url')), f'{name}: fragmento sin autorización de publicación/narración')
        if b.get('audio_fragmento'):
            require(bool(b.get('fragmento_texto')) and bool(re.fullmatch(r'/assets/reading-audio/[a-z0-9-]+\.mp3', b['audio_fragmento'])) and (root / b['audio_fragmento'].lstrip('/')).is_file(), f'{name}: audio del fragmento inválido')
        reviews = b.get("resenas", [])
        require(isinstance(reviews, list), f"{name}: reseñas debe ser lista")
        seen_reviews = set()
        for review in reviews:
            require(isinstance(review, dict) and set(review) == {"titulo", "url", "fecha_verificacion"}, f"{name}: reseña mal formada")
            require(isinstance(review["titulo"], str) and review["titulo"].strip() and https(review["url"]) and review["url"] not in seen_reviews, f"{name}: reseña sin título/URL o duplicada")
            day(review["fecha_verificacion"], name + ".reseña")
            seen_reviews.add(review["url"])
    excluded_by_book = {}
    for b in books:
        excluded = b.get('categorias_excluidas', [])
        require(isinstance(excluded, list) and all(isinstance(c, str) and c in ids for c in excluded), f"{b['id']}: exclusiones de categorías inválidas")
        excluded_by_book[b['id']] = set(excluded)
    seen = set()
    for rel in relations:
        require(isinstance(rel, dict) and set(rel) == {"libro_id", "categoria_id"}, "Relación mal formada")
        pair = (rel["libro_id"], rel["categoria_id"])
        require(pair[0] in book_ids and pair[1] in ids and pair not in seen, "Relación duplicada o referencia inexistente")
        require(pair[1] not in excluded_by_book[pair[0]], f"{pair[0]}: categoría {pair[1]} asignada y excluida simultáneamente")
        seen.add(pair)
    for b in books:
        if b["estado"] != "borrador":
            require(any(r["libro_id"] == b["id"] and any(c["id"] == r["categoria_id"] and c["activa"] for c in cats) for r in relations), f"{b['id']}: sin categoría activa")
    return [b for b in books if b["estado"] == "publicado"]


def url(b):
    return f"/recomendaciones/libros/{b['slug']}/"


# Índice libro → categorías que main() activa solo mientras pinta: sin él, cada ficha recorre todas las relaciones
# por cada libro afín y el coste crece con el cubo del catálogo. Fuera de main() (tests) se calcula al vuelo.
CATEGORY_INDEX = None


def index_categories(data):
    """Activa el índice para `data` (main() y los tests que pintan el catálogo real). Mutar data después lo invalida."""
    global CATEGORY_INDEX
    index = {}
    for r in data['libro_categorias']:
        index.setdefault(r['libro_id'], set()).add(r['categoria_id'])
    CATEGORY_INDEX = (data, index)


def categories(data, b):
    if CATEGORY_INDEX is not None and CATEGORY_INDEX[0] is data:
        ids = CATEGORY_INDEX[1].get(b["id"], set())
    else:
        ids = {r["categoria_id"] for r in data["libro_categorias"] if r["libro_id"] == b["id"]}
    return sorted((c for c in data["categorias"] if c["id"] in ids and c["activa"]), key=lambda c: (c["orden"], c["id"]))


# Contrato de la tarjeta y la ficha (docs/contrato-tarjeta-libro.md): todos los límites aquí, en un solo sitio.
CARD_TAGS = 2           # etiquetas visibles en la tarjeta
DETAIL_TAGS = 8         # hueco fijo de etiquetas en la ficha (alimentan los filtros)
CARD_TITLE_CHARS = 44   # dos líneas de la tarjeta (~22 caracteres por línea a 200 px)
CARD_SYNOPSIS = 200     # descripción sin distintivo
CARD_SYNOPSIS_BADGE = 150  # con «Novedad» o «Próximamente» la cabecera ocupa más: menos texto, misma altura
NOVELTY_DAYS = 30       # «Novedad» desde el día de salida hasta un mes después; antes, «Próximamente»


def tags(cats, compact=False, limit=None):
    def group(items):
        # La época ya no es filtro del catálogo: se muestra como etiqueta sin enlace.
        return '<ul class="catalogue-tags' + (' catalogue-tags--compact' if compact else '') + '">' + ''.join(f'<li><span>{esc(c["nombre"])}</span></li>' if c['tipo'] == 'epoca' else f'<li><a href="/recomendaciones/#{esc(c["tipo"])}={esc(c["id"])}">{esc(c["nombre"])}</a></li>' for c in items) + '</ul>'
    priority={'genero':0,'temporada':1,'tematica':2,'epoca':3,'contenido':4,'edad':5}
    if compact:
        # La edad ya la sugiere la portada: se queda en filtros y ficha, no en la tarjeta.
        cats = [c for c in cats if c['tipo'] != 'edad']
    if compact or limit:
        # Las más informativas primero; la tarjeta resume y la ficha tiene un hueco fijo.
        cats = sorted(cats, key=lambda c: (priority[c['tipo']], c['orden'], c['id']))[:CARD_TAGS if compact else limit]
    return group(cats)


def synopsis(b):
    return strip_shouting(' '.join(decode_text_entities(b.get('sinopsis_breve') or b['descripcion_breve']).split()))


def clip(text, limit):
    text = ' '.join(text.split())
    return text if len(text) <= limit else text[:limit].rsplit(' ', 1)[0].rstrip(' ,;:.') + '…'


def schema_synopsis(b):
    """Descripción del libro para el JSON-LD: la sinopsis, no la meta de la ficha (que describe la página)."""
    return clip(synopsis(b), 500)


def own_summary(b):
    """«Para quién es» validado, en una línea para índices de texto (llms.txt)."""
    t = OWN_TEXTS.get(b['id'])
    block = next((x for x in t['bloques'] if x['modulo'] == 'para_quien'), None) if t else None
    return clip(block['texto'], 200) if block else ''


def synopsis_paragraphs(b):
    """Sinopsis entera para la ficha; el extracto breve si la fuente aún no se ha releído.
    Sin titulares en mayúsculas ni citas de prensa pegados al texto (ficha, tarjeta y meta)."""
    if b.get('sinopsis_tipo') != 'resumen_propio' and b.get('sinopsis_completa'):
        return [strip_shouting(' '.join(decode_text_entities(p).split())) for p in b['sinopsis_completa'].split('\n\n') if p.strip()]
    return [synopsis(b)]


def cut(text, limit):
    """Corte en origen por palabra con «…»: la tarjeta no recorta texto con CSS (reflujo al 200 %)."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(' ', 1)[0].rstrip(' ,;:-–—') + '…'


def card_synopsis(b, limit=None, anchor=None):
    """Primer tramo de la sinopsis completa; más corto si la tarjeta lleva distintivo, para que todas cuadren."""
    if limit is None:
        limit = CARD_SYNOPSIS_BADGE if badge(b, anchor) else CARD_SYNOPSIS
    return cut(' '.join(synopsis_paragraphs(b)), limit)


def card_title(b):
    """Título de la tarjeta en dos líneas: primero la versión sin serie ni subtítulo, y si aún no cabe, «…»."""
    name = next((t for t in short_titles(b['titulo']) if len(t) <= CARD_TITLE_CHARS), short_titles(b['titulo'])[-1])
    return cut(name, CARD_TITLE_CHARS)


def badge(b, anchor=None):
    """'proximamente', 'novedad' o '' según la fecha de Amazon frente a hoy (la web lo recalcula cada día en JS)."""
    stamp = b.get('fecha_publicacion')
    if not stamp:
        return ''
    today = date.fromisoformat(anchor[:10]) if anchor else date.today()
    days = (today - date.fromisoformat(stamp)).days
    return 'proximamente' if days < 0 else 'novedad' if days <= NOVELTY_DAYS else ''


def meta_synopsis(b):
    return ' '.join(synopsis_paragraphs(b)).rstrip('…')


_SHARED_META = {}


def book_meta_description(data, b):
    """Descripción meta única: si otra ficha publicada comparte el texto editorial
    (sagas con la misma contracubierta) en los 160 caracteres visibles, se antepone el título."""
    books = [x for x in data['libros'] if x['estado'] == 'publicado']
    key = tuple(x['id'] for x in books)
    if _SHARED_META.get('key') != key:
        seen = {}
        for x in books:
            seen.setdefault(meta_synopsis(x)[:157], set()).add(x['id'])
        _SHARED_META.update(key=key, shared={text for text, ids in seen.items() if len(ids) > 1})
    text = meta_synopsis(b)
    return b['titulo'] + ': ' + text if text[:157] in _SHARED_META['shared'] else text
TEXTS_DIR = 'data/reading-texts'
OWN_TEXTS = {}
# Títulos visibles de cada módulo de orientación (scripts/reading-texts.py decide cuáles admite cada familia).
MODULE_TITLES = {
    'para_quien': 'Para quién es',
    'edad_y_sensibilidad': 'Edad recomendada y contenido',
    'encaje_documentado': 'Qué tipo de lectura propone',
    'esta_edicion': 'Qué distingue esta edición',
    'temas_y_enfoque': 'Qué cuestiones aborda',
    'contenido_y_uso': 'Qué incluye y cómo está organizado',
    'como_se_utiliza': 'Cómo se juega con este libro',
    'edad_y_formato': 'Edad y características del libro',
    'que_formato_elegir': 'Qué formato elegir',
    'lecturas_afines': 'Con qué otros libros compararlo',
}


def load_own_texts(root):
    """Módulos validados por scripts/reading-texts.py, uno por libro y fuera del JSON que reescribe el barrido."""
    texts = {}
    for path in sorted((root / TEXTS_DIR).glob('*.json')):
        t = json.loads(path.read_text(encoding='utf-8'))
        require(t.get('id') == path.stem, f'{path.name}: id distinto del nombre del fichero')
        require(all(x.get('modulo') in MODULE_TITLES for x in t.get('bloques', [])), f'{path.name}: módulo desconocido')
        if t.get('bloques'):
            texts[t['id']] = t
    return texts


def own_block_html(x, live):
    """Un módulo; las comparaciones enlazan cada título a su ficha y desaparecen si un afín ya no está publicado."""
    text = esc(x['texto'])
    for i in x.get('enlaces', []):
        if i not in live:
            return ''
        title = esc(live[i]['titulo'])
        text = text.replace(title, '<a href="' + url(live[i]) + '">' + title + '</a>', 1)
    return '<h3>' + MODULE_TITLES[x['modulo']] + '</h3><p>' + text + '</p>'


def own_text_section(b, data=None):
    """«Antes de elegir este libro»: solo aparece si el libro tiene módulos validados."""
    t = OWN_TEXTS.get(b['id'])
    live = {x['id']: x for x in (data or {}).get('libros', []) if x['estado'] == 'publicado'}
    blocks = ''.join(own_block_html(x, live) for x in t['bloques']) if t else ''
    if not blocks:
        return ''
    return ('<section class="catalogue-own-text"><h2>Antes de elegir este libro</h2>' + blocks
            + '</section><h2 class="catalogue-synopsis-heading">Sinopsis de la editorial</h2>')


def age_phrase(age):
    return '' if not age else age[0].lower() + age[1:] if age.startswith(('A partir', 'De ', 'Desde ')) else 'para ' + age.lower()


def own_meta_description(b):
    """Meta con datos de la edición y lo que aporta la ficha; nunca la escribe el redactor."""
    t = OWN_TEXTS.get(b['id'])
    if not t:
        return None
    fmt, pages, age = (b.get('formato_edicion', '').replace('-', ' '), f"{b['numero_paginas']} páginas" if b.get('numero_paginas') else '',
                       age_phrase(b.get('edad_recomendada', '')))
    # Cabe en 160 sin cortar frases: primero cae el segundo tema y después la nota de edición o la serie del título;
    # si aún no cabe (autorías largas), los datos de la edición se recortan: páginas, formato y por último la edad.
    for parts in ((fmt, pages, age), (fmt, age), (age,), ()):
        facts = ', '.join(f for f in parts if f)
        for name in short_titles(b['titulo']):
            for n in (2, 1):
                topics = ' y '.join(MODULE_TITLES[x['modulo']].lower() for x in t['bloques'][:n])
                text = f"{name}, de {', '.join(b['autores'])}" + (': ' + facts if facts else '') + '. Antes de elegirlo: ' + topics + '.'
                if len(text) <= 160:
                    return text
    return text




def synopsis_attribution(b):
    return ''


def approved_reviews_for(book, root=ROOT):
    path=root/'data/reading-reviews-approved.json'
    if not path.is_file():
        return []
    payload=json.loads(path.read_text(encoding='utf-8'))
    require(set(payload)=={'schema_version','reviews'} and payload['schema_version']==1 and isinstance(payload['reviews'],list), 'Reseñas públicas: contrato inválido')
    fields={'review_id','libro_id','isbn13','nombre_publico','puntuacion','titulo_resena','texto_resena','fecha_envio'}
    selected=[]
    seen=set()
    for review in payload['reviews']:
        require(isinstance(review,dict) and set(review)==fields, 'Reseña con campos no públicos o incompleta')
        require(isinstance(review['review_id'],str) and review['review_id'] and review['review_id'] not in seen, 'ID de reseña duplicado o vacío')
        seen.add(review['review_id'])
        require(type(review['puntuacion']) is int and 1<=review['puntuacion']<=5, 'Puntuación de reseña inválida')
        for key,limit in [('nombre_publico',80),('titulo_resena',120),('texto_resena',2000)]:
            require(isinstance(review[key],str) and 0<len(review[key].strip())<=limit, 'Texto de reseña inválido')
        day(review['fecha_envio'],'Fecha de reseña')
        if review['libro_id']==book['id']:
            require(review['isbn13']==book.get('isbn13'), 'La reseña no coincide con la edición')
            selected.append(review)
    return selected


def render_approved_reviews(reviews):
    if not reviews:
        return ''
    average=sum(r['puntuacion'] for r in reviews)/len(reviews)
    block='<details class="catalogue-details catalogue-reader-reviews"><summary>Opiniones de lectores ('+str(len(reviews))+')</summary><p>'+str(round(average,2)).replace('.',',')+'/5 · Opiniones publicadas en esta web</p>'
    for review in reviews:
        block+='<article><h3>'+esc(review['titulo_resena'])+'</h3><p>'+esc(review['nombre_publico'])+' · '+str(review['puntuacion'])+'/5 · <time datetime="'+review['fecha_envio']+'">'+esc(review['fecha_envio'])+'</time></p><p class="catalogue-review-text">'+esc(review['texto_resena'])+'</p></article>'
    return block+'</details>'


def image(b, lazy=False, sizes='(max-width: 600px) 35vw, 260px', cls='catalogue-book-cover', alt=None):
    loading = 'loading="lazy"' if lazy else 'fetchpriority="high"'
    preview = b['portada_local'].replace('.webp', '-320.webp')
    responsive = f' srcset="{esc(preview)} 320w, {esc(b["portada_local"])} {b["portada_ancho"]}w" sizes="{esc(sizes)}"' if b['portada_local'].startswith('/assets/reading-covers/isbn-') else ''
    alt = f'Portada de {b["titulo"]} — {b["edicion"]}' if alt is None else alt
    return f'<img class="{cls}" src="{esc(b["portada_local"])}"{responsive} alt="{esc(alt)}" width="{b["portada_ancho"]}" height="{b["portada_alto"]}" {loading} decoding="async">'


def novelty(b, fallback):
    if not b.get('fecha_publicacion'):
        return ''
    return '<span class="catalogue-novelty" data-release-label="' + esc(b.get('fecha_publicacion', '')) + '" hidden>Novedad</span>'


def short_titles(title):
    """Versiones cada vez más cortas del título: sin la nota de edición, sin la serie entre paréntesis y sin subtítulo."""
    out = [title]
    for pattern in (r'\s*[(\[]?\s*\bedici[oó]n\s+(?:especial|limitada|coleccionista|ilustrada|exclusiva|aniversario|conmemorativa|deluxe|serie)\b.*$', r'\s*\([^()]*\)\s*$', r'\s*:[^:]*$'):
        t = re.sub(pattern, '', out[-1], flags=re.I).strip(' -–—:.,')
        if t and t != out[-1]:
            out.append(t)
    return out


def book_title(b, books=()):
    """Título SEO de hasta 75 caracteres que conserva el autor; el ISBN solo entra si el título corto choca con otra ficha."""
    if isinstance(books, dict):
        # Firma de main: el catálogo entero; solo cuentan las fichas publicadas.
        books = [x for x in books.get('libros', []) if x.get('estado') == 'publicado']
    authors = ', '.join(b['autores'])
    clash = {x['titulo'].casefold() for x in books if x['id'] != b['id'] and x['autores'] == b['autores']}
    clash |= {t.casefold() for x in books if x['id'] != b['id'] and x['autores'] == b['autores'] for t in short_titles(x['titulo'])}
    for i, name in enumerate(short_titles(b['titulo'])):
        if i and name.casefold() in clash:
            break
        # El sufijo de marca solo si todo cabe en los ~60 caracteres que Google muestra sin cortar.
        for title, limit in ((f'{name} · {authors} | Libros recomendados', 60), (f'{name} · {authors}', 75)):
            if len(title) <= limit:
                return title
    # Con muchas firmas (guías, obras colectivas) cabe «primer autor y otros»: el autor no se pierde nunca.
    lead = ' · ' + b['autores'][0] + (' y otros' if len(b['autores']) > 1 else '')
    tails = [' · ' + authors] + ([lead] if lead != ' · ' + authors else [])
    for tail in tails:
        cut = b['titulo'][:74-len(tail)].rsplit(' ', 1)[0].rstrip(' -–—:.,')
        if len(cut) >= 20 and not any(t.startswith(cut.casefold()) for t in clash):
            return cut + '…' + tail
    suffix = ' · ' + (b.get('isbn13') or hashlib.sha256(b['id'].encode()).hexdigest()[:8])
    tail = next((t for t in tails if len(t) <= 30), '')
    suffix = tail + suffix  # El autor es lo que se busca: se queda también junto al ISBN.
    return b['titulo'][:74-len(suffix)].rsplit(' ', 1)[0] + '…' + suffix


AUTHOR_CACHE = {}


def author_records(root=ROOT):
    """Autores validados; se leen una vez por versión del archivo, no una por ficha."""
    path = root / 'data/reading-authors.json'
    if not path.exists():
        return []
    stat = path.stat()
    key = (str(path), stat.st_mtime_ns, stat.st_size)
    if key not in AUTHOR_CACHE:
        AUTHOR_CACHE.clear()
        AUTHOR_CACHE[key] = load_author_records(path)
    return AUTHOR_CACHE[key]


def load_author_records(path):
    payload = json.loads(path.read_text(encoding='utf-8'))
    require(set(payload) == {'schema_version', 'autores'} and payload['schema_version'] == 1, 'Contrato de autores inválido')
    names, slugs = set(), set()
    for a in payload['autores']:
        required = {'slug', 'nombre', 'descripcion', 'fuentes', 'fecha_verificacion'}
        optional = {'biografia_breve', 'biografia_fuente_url', 'biografia_fecha_revision', 'biografia_fuente_nombre', 'biografia_ultimo_intento'}
        require(set(a) - optional == required | ({'tipo'} if a.get('tipo') == 'bibliografico' else {'nacimiento'}), 'Campos de autor inválidos')
        if a.get('biografia_breve'):
            require(30 <= len(a['biografia_breve']) <= 700 and https(a.get('biografia_fuente_url')), 'Biografía sin fuente o inválida')
            day(a.get('biografia_fecha_revision'), 'biografía revisada')
        require(SLUG.fullmatch(a['slug']) and a['slug'] not in slugs and a['nombre'] not in names, 'Autor duplicado o slug inválido')
        require(isinstance(a['descripcion'], str) and len(a['descripcion']) >= 60, 'Autor sin descripción')
        if a.get('nacimiento'):
            day(a['nacimiento'], 'nacimiento')
        day(a['fecha_verificacion'], 'autor verificado')
        require(a['fuentes'] and all(set(s) == {'titulo', 'url'} and s['titulo'] and https(s['url']) for s in a['fuentes']), 'Autor sin fuentes')
        names.add(a['nombre']); slugs.add(a['slug'])
    return payload['autores']


def publisher_records(root=ROOT):
    """Sellos que aparecen en el catálogo pero no en el directorio de editoriales que aceptan manuscritos."""
    path = root / 'data/reading-publishers.json'
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding='utf-8'))
    require(set(payload) == {'schema_version', 'editoriales'} and payload['schema_version'] == 1, 'Contrato de sellos inválido')
    slugs, names = set(), set()
    for p in payload['editoriales']:
        require(set(p) == {'slug', 'nombre', 'grupo', 'fuentes', 'fecha_verificacion'}, 'Campos de sello inválidos')
        require(SLUG.fullmatch(p['slug']) and p['slug'] not in slugs and p['nombre'].casefold() not in names, 'Sello duplicado o slug inválido')
        require(2 <= len(p['nombre']) <= 60 and 2 <= len(p['grupo']) <= 80, 'Nombre o grupo de sello inválido')
        day(p['fecha_verificacion'], 'sello verificado')
        require(p['fuentes'] and all(set(s) == {'titulo', 'url'} and s['titulo'] and https(s['url']) for s in p['fuentes']), 'Sello sin fuentes')
        slugs.add(p['slug']); names.add(p['nombre'].casefold())
    return payload['editoriales']


def collection_modified(record, books):
    """Fecha de la página de autor o editorial: su última verificación o la última actualización de sus libros."""
    return max([record.get('fecha_verificacion', ''), *(b['fecha_actualizacion'] for b in books)])


def publisher_url(p):
    return '/recomendaciones/editoriales/' + p['slug'] + '/'


def author_url(a):
    return '/recomendaciones/autores/' + a['slug'] + '/'


def author_links(b, authors=None, compact=False):
    authors = author_records() if authors is None else authors
    links = []
    destination = 'libros' if compact else 'información y libros'
    for name in b['autores']:
        a = next((a for a in authors if a['nombre'] == name), None)
        links.append(f'<a href="{author_url(a)}" target="_blank" rel="noopener" aria-label="{esc(name)}: {destination} (otra pestaña)">{esc(name)} <span aria-hidden="true">↗</span></a>' if a else esc(name))
    return ', '.join(links)


def purchase_formats(b):
    return b.get('formatos_compra', [])


def money(cents):
    return f'{cents // 100},{cents % 100:02d} €'


def amazon_prices(b):
    """Amazon price per format, refreshed by the nightly sweep: the only price the site shows."""
    return [o for o in sorted(purchase_formats(b), key=lambda o: list(FORMATS).index(o['formato'])) if o.get('precio_centimos')]


DIGITAL_FORMATS = ('ebook', 'audiolibro')


def print_list_prices(b):
    """PVP y precios de las ediciones en papel: en un ebook no son un «precio antes», sino otro formato."""
    out = {b.get('pvp_centimos')}
    for o in purchase_formats(b):
        if o['formato'] not in DIGITAL_FORMATS:
            out |= {o.get('precio_centimos'), o.get('precio_referencia_centimos')}
    return out - {None}


def offer_is_current(o, anchor):
    """Comprobada por Amazon en los últimos OFFER_MAX_DAYS días respecto a la fecha de los datos."""
    try:
        return (date.fromisoformat(anchor) - date.fromisoformat(o.get('fecha_verificacion', ''))).days <= OFFER_MAX_DAYS
    except ValueError:
        return False


def price_discount(b, o, anchor=None):
    """(precio de referencia de Amazon, % redondeado como Amazon) o None. Solo cuenta el precio de referencia
    (savingBasis) que da Amazon: no una bajada respecto a un precio nuestro anterior (petición de David, 2026-11-05).
    En digital se ignora la referencia que es el precio de la versión impresa (2026-11-04: 12 ebooks salían al 50 %)."""
    if anchor and not offer_is_current(o, anchor):
        return None
    # 2026-11-05: 26 audiolibros salían todos al -30 % exacto: es el precio de socio de Audible frente al precio
    # sin suscripción, no una oferta. Colaban libros en «25 % o más» sin descuento real visible.
    if o['formato'] == 'audiolibro':
        return None
    base = o.get('precio_referencia_centimos', 0)
    paper = print_list_prices(b)
    if o['formato'] in DIGITAL_FORMATS and base in paper:
        return None
    # 2026-11-05: ebooks «-70 %» contra 22,39 € (papel de otra edición). Un Kindle no cuesta el 80 % del papel:
    # esa referencia es la «versión impresa», no un descuento.
    if o['formato'] == 'ebook' and paper and base * 5 >= min(paper) * 4:
        return None
    if not o.get('precio_centimos') or base <= o['precio_centimos']:
        return None
    return base, ((base - o['precio_centimos']) * 200 + base) // (2 * base)


def lowest_price(b):
    prices = [o['precio_centimos'] for o in amazon_prices(b)]
    return min(prices) if prices else None


def publisher_link(b):
    if not b.get('editorial'):
        return ''
    if b.get('editorial_slug'):
        return '<a class="catalogue-publisher" href="/editoriales/' + esc(b['editorial_slug']) + '/">' + esc(b['editorial']) + '</a>'
    if b.get('editorial_catalogo_slug'):
        return '<a class="catalogue-publisher" href="/recomendaciones/editoriales/' + esc(b['editorial_catalogo_slug']) + '/">' + esc(b['editorial']) + '</a>'
    return esc(b['editorial'])


def amazon_destination(b):
    """Verified product page (the edition's own format first), otherwise tagged ISBN search."""
    printed = {o['formato']: o['url'] for o in purchase_formats(b)}
    edition = next((printed[f] for f in (b.get('formato_edicion'), 'tapa-blanda', 'tapa-dura') if f in printed), None)
    own = b.get('url_amazon_afiliada')
    # El sync renueva la URL de cada formato (detailPageURL de Amazon); si el enlace propio es el
    # mismo ASIN, se usa esa URL para que portada y botón del formato lleven al mismo sitio.
    same = next((o['url'] for o in purchase_formats(b) if own and amazon_asin(o['url']) and amazon_asin(o['url']) == amazon_asin(own)), None)
    return amazon_es(same or own or edition or b.get('amazon_busqueda_isbn'))


def amazon_asin(link):
    match = re.search(r'amazon\.es/(?:[^?#]*/)?(?:dp|gp/product)/([A-Z0-9]{10})', link or '')
    return match[1] if match else None


def amazon_action_label(b):
    return 'Comprar en Amazon'


def primary_format(b):
    """Formato de la caja al que lleva el botón principal (None si es búsqueda o un enlace sin formato)."""
    destination = amazon_destination(b)
    found = next((o['formato'] for o in purchase_formats(b) if amazon_es(o['url']) == destination), None)
    # Sin ficha de producto, la búsqueda por ISBN compra justo esta edición: su formato.
    if not found and b.get('formato_edicion') and b.get('amazon_busqueda_isbn') and destination == amazon_es(b['amazon_busqueda_isbn']):
        found = b['formato_edicion']
    return found


LANGUAGES = {'es': 'Español', 'ca': 'Català', 'gl': 'Galego', 'eu': 'Euskara', 'en': 'Inglés', 'fr': 'Francés', 'it': 'Italiano', 'pt': 'Portugués', 'de': 'Alemán'}


# Aviso para lectores de pantalla en enlaces de texto que abren otra pestaña (WCAG G201).
NEW_TAB='<span class="visually-hidden"> (otra pestaña)</span>'


def newtab(html):
    """Los enlaces internos del contenido abren pestaña nueva; migas de pan, pie y descargas se quedan igual."""
    def mark(m):
        t = m.group(0)
        if not re.search(r'href="/(?!/)', t) or 'target=' in t or '.ics' in t:
            return t
        return t[:-1] + ' target="_blank" rel="noopener">'
    anchors = lambda chunk: re.sub(r'<a[^>]*>', mark, chunk)
    keep = re.compile(r'<nav class="book-breadcrumb"[\s\S]*?</nav>|<div class="catalogue-end">[\s\S]*?</div>')
    out, pos = [], 0
    for m in keep.finditer(html):
        out += [anchors(html[pos:m.start()]), m.group(0)]
        pos = m.end()
    return ''.join(out + [anchors(html[pos:])])


def release_line(b, upcoming=False):
    """«Próximamente · 18 de noviembre de 2026» en la línea superior, sin un bloque aparte."""
    when = publication_date_label(b)
    if not when:
        return ''
    stamp = b.get('fecha_publicacion') or b.get('fecha_publicacion_parcial') or str(b.get('anio_publicacion'))
    line = novelty(b, '') + '<time class="catalogue-date" datetime="' + esc(stamp) + '">' + esc(when) + '</time>'
    if upcoming:
        line += '<a class="catalogue-calendar" href="/' + ICS_PATH + '">Añadir al calendario</a>'
    return line


def byline(b):
    """Editorial y páginas justo debajo del autor, sin etiquetas."""
    parts = [publisher_link(b), ('<span class="catalogue-pages">' + esc(b['numero_paginas']) + ' páginas</span>') if b.get('numero_paginas') else '']
    return '<p class="catalogue-byline">' + '<span aria-hidden="true"> · </span>'.join(x for x in parts if x) + '</p>' if any(parts) else ''


BOX_ORDER = ('tapa-dura', 'tapa-blanda', 'ebook', 'audiolibro')


def amazon_es(link):
    """Amazon.es en español aunque el navegador tenga otro idioma guardado (el recuadro de compra salía en inglés)."""
    if not link or not re.match(r'https://(www\.)?amazon\.es/', link) or 'language=' in link:
        return link
    return link + ('&' if '?' in link else '?') + 'language=es_ES'


SEARCH_INDEX = {'ebook': 'digital-text', 'audiolibro': 'audible', 'tapa-dura': 'stripbooks', 'tapa-blanda': 'stripbooks'}


def amazon_format_search(b, f):
    """Búsqueda etiquetada por título y autor en la sección del formato: no se afirma que exista ni que falte."""
    raw = b.get('amazon_busqueda_isbn') or ''
    tag = (parse_qs(urlparse(raw).query).get('tag') or [''])[0]
    if not tag:
        return None
    words = ' '.join([b.get('titulo', '')] + list(b.get('autores', [])[:1])).strip()
    return 'https://www.amazon.es/s?' + urlencode({'k': words, 'i': SEARCH_INDEX[f], 'tag': tag})


def format_box(b, compact=False, anchor=None):
    """Los cuatro formatos siempre en el mismo orden.

    Precio de Amazon cuando el barrido lo comprobó. El formato de esta edición (ISBN) existe siempre: sin precio
    comprobado lleva a la búsqueda por ISBN. Los demás formatos sin comprobar no se marcan como «no disponible»
    (que el barrido no los encontrase no prueba que no existan): se ofrecen como búsqueda en su sección de Amazon.
    """
    by_format = {o['formato']: o for o in purchase_formats(b)}
    main = None if compact else primary_format(b)
    own = b.get('formato_edicion')
    cells = []
    for f in BOX_ORDER:
        o = by_format.get(f)
        if not o and f == own and b.get('amazon_busqueda_isbn'):
            o = {'formato': f, 'url': b['amazon_busqueda_isbn']}
        if o:
            price = money(o['precio_centimos']) if o.get('precio_centimos') else 'Ver precio'
            found = price_discount(b, o, anchor) if anchor and o.get('fecha_verificacion') else None
            # Porcentaje rojo junto al precio; el navegador lo quita si la comprobación caduca (data-offer-checked).
            badge = f' <em class="catalogue-format__off" data-offer-checked="{esc(o["fecha_verificacion"])}">-{found[1]} %</em>' if found else ''
            said = f', {found[1]} % de descuento sobre {money(found[0])}' if found else ''
            cells.append(f'<li><a class="catalogue-format{" is-primary" if f == main else ""}" data-purchase-format="{f}" href="{esc(amazon_es(o["url"]))}" target="_blank" rel="sponsored nofollow noopener noreferrer" aria-label="{FORMATS[f]}: {price}{said} en Amazon (otra pestaña)"><span>{FORMATS[f]}</span><strong>{price}{badge}</strong></a></li>')
        elif (search := amazon_format_search(b, f)):
            cells.append(f'<li><a class="catalogue-format is-missing" data-missing-format="{f}" href="{esc(amazon_es(search))}" target="_blank" rel="sponsored nofollow noopener noreferrer" aria-label="{FORMATS[f]}: sin precio comprobado, buscar en Amazon (otra pestaña)"><span>{FORMATS[f]}</span><strong>Buscar</strong></a></li>')
        else:
            cells.append(f'<li><span class="catalogue-format is-missing" data-missing-format="{f}" aria-label="{FORMATS[f]}: sin precio comprobado en Amazon"><span>{FORMATS[f]}</span><strong>—</strong></span></li>')
    if compact:
        # The enclosing region already names Amazon; retain format, price and new-tab hint.
        cells = [cell.replace(' en Amazon (otra pestaña)', ' (otra pestaña)').replace(', buscar en Amazon (otra pestaña)', ', buscar (otra pestaña)').replace(' comprobado en Amazon"', ' comprobado"') for cell in cells]
    heading = '' if compact else '<h2>Formatos y precios en Amazon</h2>'
    return f'<section class="catalogue-formats{" catalogue-formats--card" if compact else ""}" aria-label="Formatos y precios en Amazon">{heading}<ul>' + ''.join(cells) + '</ul></section>'


MONTHS_ES = ('', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')


ICS_PATH = 'recomendaciones/proximos-lanzamientos.ics'
DEALS_PATH = 'recomendaciones/ofertas.json'
DEALS_SEASON = 'ofertas-amazon'  # opción de «Temporada» calculada en el navegador (assets/reading-catalogue.js)


def render_deals(books):
    """Ofertas comprobadas en Amazon (precio de referencia o bajada reciente), para un canal de avisos como Telegram."""
    deals, anchor = [], data_anchor(books)
    for b in books:
        for o in amazon_prices(b):
            if found := price_discount(b, o, anchor):
                base, pct = found
                deals.append({'libro_id': b['id'], 'titulo': b['titulo'], 'autores': b['autores'], 'ficha': SITE + url(b),
                              'portada': SITE + b['portada_local'], 'formato': o['formato'], 'url': o['url'],
                              'precio_centimos': o['precio_centimos'], 'precio_antes_centimos': base,
                              'descuento_pct': pct,
                              'tipo': 'descuento',
                              'comprobado': o['fecha_verificacion']})
    deals.sort(key=lambda d: (-d['descuento_pct'], d['titulo'].casefold(), d['formato']))
    return json.dumps({'schema_version': 1, 'ofertas': deals}, ensure_ascii=False, indent=2) + '\n'


def data_anchor(books):
    """Fecha de referencia derivada de los datos (no del reloj): la salida es determinista."""
    return max((b.get('fecha_actualizacion') or b.get('fecha_verificacion') or '' for b in books), default='')


def upcoming_books(books):
    anchor = data_anchor(books)
    return sorted((b for b in books if b.get('fecha_publicacion', '') > anchor), key=lambda b: (b['fecha_publicacion'], b['titulo']))


def ics_text(value):
    BS = chr(92)
    normalized = str(value).replace(chr(13) + chr(10), chr(10)).replace(chr(13), chr(10))
    return normalized.replace(BS, BS * 2).replace(chr(10), BS + 'n').replace(',', BS + ',').replace(';', BS + ';')


def ics_fold(line):
    out, cur = [], ''
    for ch in line:
        if len((cur + ch).encode('utf-8')) > 75:
            out.append(cur)
            cur = ' ' + ch
        else:
            cur += ch
    out.append(cur)
    return (chr(13) + chr(10)).join(out)


def render_release_ics(books):
    """Calendario .ics de próximos lanzamientos (eventos de día completo)."""
    stamp = data_anchor(books).replace('-', '')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//David Porto Diaz//Proximos lanzamientos//ES', 'CALSCALE:GREGORIAN',
             'METHOD:PUBLISH', 'X-WR-CALNAME:Próximos lanzamientos de libros recomendados']
    for b in upcoming_books(books):
        d = date.fromisoformat(b['fecha_publicacion'])
        lines += ['BEGIN:VEVENT', 'UID:' + b['id'].lower() + '@davidportodiaz.com', 'DTSTAMP:' + stamp + 'T000000Z',
                  'DTSTART;VALUE=DATE:' + d.strftime('%Y%m%d'), 'DTEND;VALUE=DATE:' + (d + timedelta(days=1)).strftime('%Y%m%d'),
                  'SUMMARY:' + ics_text('Sale a la venta: ' + b['titulo']),
                  'DESCRIPTION:' + ics_text(', '.join(b['autores']) + ' · ' + (b.get('editorial') or '')
                                            + (chr(10) + 'Comprar en Amazon: ' + amazon_destination(b) if amazon_destination(b) else '')
                                            + chr(10) + 'Ficha: ' + SITE + url(b)),
                  'URL:' + SITE + url(b), 'END:VEVENT']
    lines += ['END:VCALENDAR', '']
    return (chr(13) + chr(10)).join(ics_fold(line) for line in lines)


LLMS_PATH = 'recomendaciones/llms.txt'


def render_llms_index(data, books, authors, publishers):
    """Índice en texto plano (formato llms.txt) de todas las fichas, para buscadores y asistentes de IA."""
    formats = {'tapa-dura': 'tapa dura', 'tapa-blanda': 'tapa blanda', 'ebook': 'ebook', 'audiolibro': 'audiolibro'}
    lines = ['# Libros recomendados de otros autores · davidportodiaz.com', '',
             '> Catálogo de lecturas seleccionadas por David Porto Díaz. Cada obra tiene una ficha con URL estable, autoría, '
             'datos de la edición (editorial, ISBN, formato, páginas), orientación propia («Para quién es»), sinopsis de la editorial y fuentes. '
             'Estas obras son de sus autores: no atribuirlas a David Porto Díaz.', '',
             f'- Catálogo con filtros: {SITE}/recomendaciones/',
             f'- Autores del catálogo ({len(authors)}): {SITE}/recomendaciones/autores/',
             f'- Editoriales del catálogo ({len(publishers)}): {SITE}/recomendaciones/editoriales/',
             f'- Política de recomendaciones: {SITE}/recomendaciones/politica-de-recomendaciones/', '',
             f'## Libros ({len(books)})', '']
    for b in sorted(books, key=lambda b: (b['titulo'].casefold(), b['id'])):
        cats = categories(data, b)
        facts = [', '.join(b['autores']), b.get('editorial'), b.get('anio_publicacion') and str(b['anio_publicacion']), formats.get(b.get('formato_edicion')),
                 b.get('numero_paginas') and f"{b['numero_paginas']} páginas", b.get('isbn13') and 'ISBN ' + b['isbn13']]
        facts += [label + ': ' + ', '.join(names) for label, tipo in (('Género', 'genero'), ('Temas', 'tematica'))
                  if (names := [c['nombre'] for c in cats if c['tipo'] == tipo])]
        age = b.get('edad_recomendada') or ', '.join(c['nombre'] for c in cats if c['tipo'] == 'edad')
        who = own_summary(b)
        facts += [age and 'Edad: ' + age]
        head = f"- [{b['titulo']}]({SITE}{url(b)}): " + '. '.join(f.rstrip('.') for f in facts if f) + '. '
        # El «Para quién es» cede espacio para que la sinopsis conserve al menos 60 caracteres sin pasar de 690.
        who = who and clip(who, max(40, 690 - 60 - len(head) - len('Para quién es: . Sinopsis de la editorial: ')))
        head += (who and 'Para quién es: ' + who.rstrip('.') + '. ') + 'Sinopsis de la editorial: '
        # Cada línea cabe en 700 caracteres: la sinopsis de la editorial se queda con el espacio que deja lo propio.
        synopsis = clip(b['sinopsis_breve'], max(60, min(300, 690 - len(head))))
        lines.append(head + synopsis.rstrip('.') + ('' if synopsis.endswith('…') else '.'))
    return '\n'.join(lines) + '\n'


def publication_date_label(b):
    """Never manufacture a precise release day from year/month metadata."""
    exact = b.get('fecha_publicacion')
    if exact:
        d = date.fromisoformat(exact)
        return f'{d.day} de {MONTHS_ES[d.month]} de {d.year}'
    partial = b.get('fecha_publicacion_parcial')
    if partial:
        year, month = (int(part) for part in partial.split('-'))
        return f'{MONTHS_ES[month]} de {year}'
    return str(b.get('anio_publicacion') or '')


def age_order(c):
    """Adultos y Juvenil primero; después las franjas de edad de menor a mayor («De 0 a 3» antes que «A partir de 4»)."""
    if c['id'] in ('adultos', 'juvenil'):
        return (0 if c['id'] == 'adultos' else 1, 0, 0)
    ages = [int(n) for n in re.findall(r'\d+', c['id'])] or [99]
    return (2, ages[0], ages[-1] if len(ages) > 1 else 99)


def format_discounts(b, anchor=None):
    """«formato:%:fecha» del descuento sobre el precio de referencia de Amazon; el navegador lo retira al caducar."""
    out = []
    for o in amazon_prices(b):
        if found := price_discount(b, o, anchor):
            out.append(f"{o['formato']}:{found[1]}:{o['fecha_verificacion']}")
    return ' '.join(out)


def format_prices(b):
    """«formato:céntimos» por cada formato con precio en Amazon, para ordenar y filtrar dentro de un mismo formato."""
    return ' '.join(f"{o['formato']}:{o['precio_centimos']}" for o in amazon_prices(b))


def facet_group(key, label, options, opened=False):
    boxes = ''.join(f'<label class="catalogue-check"><input type="checkbox" id="{key}={esc(v)}" name="{key}" value="{esc(v)}" data-facet="{key}"><span>{esc(t)}</span><small data-facet-count></small></label>' for v, t in options)
    return f'<details class="catalogue-facet" data-facet-group="{key}"' + (' open' if opened else '') + f'><summary>{esc(label)} <small data-facet-selected></small></summary><div class="catalogue-facet__options">{boxes}</div></details>'


def render_filters(data, type_options):
    def select(key, label, options, extra=''):
        return f'<label>{label}<select name="{key}" data-filter="{key}" {extra}>' + ''.join(f'<option value="{esc(v)}">{esc(t)}</option>' for v, t in options) + '</select></label>'
    search = '<label class="catalogue-search">Buscar por título, autor o ISBN<input type="search" name="q" data-filter="q" maxlength="200" autocomplete="off" placeholder="¿Qué te apetece leer?"></label>'
    used = {r['categoria_id'] for r in data['libro_categorias']}
    facets = facet_group('grupo', 'Tipo de libro', type_options, True)
    for kind, label in TYPES.items():
        if kind == 'epoca':
            continue  # «Época» no ayudaba a elegir: casi todo el catálogo es actual.
        # Una categoría sin libros solo añadiría una casilla muerta al filtro.
        choices = sorted((c for c in data['categorias'] if c['tipo'] == kind and c['activa'] and c['id'] in used), key=age_order if kind == 'edad' else lambda c: (c['orden'], c['id']))
        if not choices:
            continue
        options = [(c['id'], c['nombre']) for c in choices]
        if kind == 'temporada':
            # Prime Day y Black Friday no son un tema: son los libros con una oferta vigente de Amazon (≥10 %),
            # que el navegador calcula con las fechas de comprobación; aparece y desaparece sola con las ofertas.
            options.append((DEALS_SEASON, 'Prime Day y Black Friday'))
        facets += facet_group(kind, label, options)
    facets += facet_group('formato', 'Formato', list(FORMATS.items()))
    price_format = '<label class="catalogue-price-range__format">Formato<select name="precio_formato" data-filter="precio_formato">' + '<option value="">Cualquier formato</option>' + ''.join(f'<option value="{k}">{esc(FORMATS[k])}</option>' for k in BOX_ORDER) + '</select></label>'
    facets += '<div class="catalogue-facet catalogue-price-range"><p class="catalogue-facet__title">Precio (€)</p><p class="catalogue-price-range__hint">Elige el formato para no mezclar precios de Kindle y de papel.</p>' + price_format + '<div class="catalogue-price-range__fields">' + ''.join(f'<label>{t}<input type="number" min="0" max="100000" step="0.01" inputmode="decimal" name="{k}" data-filter="{k}" placeholder="{ph}"></label>' for k, t, ph in (('precio_min', 'Desde', '0'), ('precio_max', 'Hasta', '100'))) + '</div></div>'
    controls = select('novedad', 'Novedades', [('', 'Cualquier fecha'), ('15', 'Novedad · menos de 15 días'), ('30', 'Últimos 30 días'), ('90', 'Últimos 90 días'), ('180', 'Últimos 180 días')])
    controls += select('paginas', 'Extensión', [('', 'Cualquier extensión'), ('breve', 'Menos de 200 páginas'), ('media', 'De 200 a 399 páginas'), ('larga', 'De 400 a 599 páginas'), ('muy-larga', '600 páginas o más')])
    advanced = '<div class="catalogue-filter-grid">'
    for key,label in [('desde', 'Publicado desde'), ('hasta', 'Publicado hasta')]:
        advanced += f'<label>{label}<input type="date" name="{key}" data-filter="{key}" min="1000-01-01" max="2100-12-31"></label>'
    advanced += select('descuento', 'Ofertas', [('', 'Todos los precios'), ('1', 'Con descuento o bajada de precio'), ('5', '5 % o más'), ('10', '10 % o más'), ('25', '25 % o más'), ('50', '50 % o más')], 'data-market-control="offers" disabled')
    advanced += select('valoracion', 'Valoración de lectores', [('', 'Todas las valoraciones'), ('menos-3', 'Menos de 3 estrellas'), ('3', '3 estrellas o más'), ('4', '4 estrellas o más'), ('4.5', '4,5 estrellas o más'), ('5', '5 estrellas')], 'data-market-control="ratings" disabled')
    advanced += '</div>'
    # En móvil (≤900 px) solo la búsqueda queda a la vista; el resto de filtros se pliega tras
    # «Filtros» para que los libros aparezcan en la primera pantalla. En escritorio el panel
    # siempre está abierto y el botón no se muestra (lo decide el CSS: sin salto al cargar).
    toggle = '<button type="button" class="catalogue-refine-toggle" aria-expanded="false" aria-controls="catalogue-refine" data-catalogue-refine-toggle>Filtros <span class="catalogue-refine-count" data-catalogue-refine-count></span><span aria-hidden="true">＋</span></button>'
    return ('<aside class="catalogue-sidebar"><form class="catalogue-filters" data-catalogue-filters><fieldset disabled><legend>Encuentra tu próxima lectura</legend>' + search + toggle
            + '<div class="catalogue-refine" id="catalogue-refine" data-catalogue-refine><div class="catalogue-facets">' + facets + '</div><div class="catalogue-filter-grid">' + controls + '</div>'
            '<details class="catalogue-details catalogue-more-filters"><summary>Más filtros: fechas, ofertas y valoraciones <span aria-hidden="true">＋</span></summary>' + advanced + '</details>'
            '<div class="catalogue-filter-actions"><button type="submit">Buscar libros</button><button type="reset" disabled>Restablecer</button></div></div></fieldset></form></aside>')


# Tipo de libro para el selector «Todos / Novela / Cocina…» junto al catálogo.
# Orden = prioridad: gana el primer grupo que contenga alguna categoría del libro.
BOOK_GROUPS = (
    ('cocina', 'Cocina y alimentación', {'cocina', 'nutricion-y-bienestar'}),
    ('crecimiento', 'Crecimiento personal', {'desarrollo-personal', 'familia-y-crianza', 'tema-ocio-y-tiempo-libre', 'psicologia', 'mindfulness', 'motivacion'}),
    ('poesia', 'Poesía', {'poesia'}),
    ('infantil', 'Infantil y juvenil', {'infantil', 'narrativa-juvenil', 'juvenil', 'fantasia-juvenil'}),
    ('viajes', 'Viajes', {'tema-viajes'}),
    ('ensayo', 'Ensayo, historia y memorias', {'biografias-y-memorias', 'historia', 'ensayo', 'divulgacion-cientifica', 'psicologia', 'comic-y-novela-grafica', 'filosofia',
                                               'tema-cronica', 'tema-memoria', 'tema-religion-y-espiritualidad', 'tema-poder-y-politica', 'tema-economia-y-empresa',
                                               'tema-economia-politica-sociedad-y-actualidad'}),
    ('novela', 'Novela', {'fantasia', 'fantasia-juvenil', 'fantasia-oscura', 'romantasy', 'romance', 'portales', 'magia-con-coste', 'terror', 'mundos-paralelos', 'misterio', 'misterio-y-thriller', 'novela-historica', 'narrativa', 'aventuras', 'ciencia-ficcion', 'clasicos', 'humor', 'tema-amor-y-pareja'}),
)


def book_group(cats):
    ids = {c['id'] for c in cats}
    # Sin cajón «Otros»: lo que no encaja en ningún tipo es no ficción (crónica, actualidad, religión…).
    return next((gid for gid, _label, members in BOOK_GROUPS if ids & members), 'ensayo')


def group_options(groups):
    display_order = ('novela', 'poesia', 'infantil', 'cocina', 'crecimiento', 'ensayo', 'viajes')
    return sorted(((gid, label) for gid, label, _m in BOOK_GROUPS if gid in groups), key=lambda g: display_order.index(g[0]))


CATALOGUE_PAGE_SIZE = 96


def catalogue_page_url(number):
    return '/recomendaciones/' if number == 1 else f'/recomendaciones/pagina/{number}/'


def catalogue_pager(number, pages):
    if pages <= 1:
        return ''
    links = ''.join(f'<span aria-current="page">{i}</span>' if i == number else
                    f'<a href="{catalogue_page_url(i)}" target="_self" data-catalogue-page aria-label="Página {i}">{i}</a>'
                    for i in range(1, pages + 1))
    return '<nav class="catalogue-pagination catalogue-static-pagination" data-catalogue-static-pagination aria-label="Páginas del catálogo">' + links + '</nav>'


def render_hub(data, books, template, page_number=1):
    anchor = data_anchor(books) or None
    cards = []
    groups = {}
    books = sorted(books, key=lambda b: (b.get('fecha_publicacion') or b.get('fecha_publicacion_parcial') or str(b.get('anio_publicacion', '')), b['titulo'].casefold()), reverse=True)
    # Los próximos lanzamientos van detrás: así el HTML ya coincide con la vista por defecto («Ya publicados»)
    # y el primer filtrado del JS no mueve la página (CLS); sin JS siguen todas las fichas.
    anchor = data_anchor(books)
    books.sort(key=lambda b: b.get('fecha_publicacion', '') > anchor)
    page_count = max(1, math.ceil(len(books) / CATALOGUE_PAGE_SIZE))
    require(type(page_number) is int and 1 <= page_number <= page_count, 'Página de catálogo fuera de rango')
    offset = (page_number - 1) * CATALOGUE_PAGE_SIZE
    visible_books = books[offset:offset + CATALOGUE_PAGE_SIZE]
    canonical = SITE + catalogue_page_url(page_number)
    version = hashlib.sha256(json.dumps(books, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    for book in books:
        group = book_group(categories(data, book))
        groups[group] = groups.get(group, 0) + 1
    for i,b in enumerate(visible_books):
        cats = categories(data,b)
        group = book_group(cats)
        formats = ' '.join(sorted(set([o['formato'] for o in purchase_formats(b)] + ([b['formato_edicion']] if b.get('formato_edicion') else []))))
        published = b.get('fecha_publicacion', '')
        year = '' if published or b.get('fecha_publicacion_parcial') else b.get('anio_publicacion', '')
        attrs = f'data-catalogue-book data-group="{group}" data-book-id="{esc(b["id"])}" data-categories="{esc(" ".join(c["id"] for c in cats))}" data-title="{esc(b["titulo"])}" data-author="{esc(", ".join(b["autores"]))}" data-formats="{formats}" data-published="{esc(published)}" data-published-month="{esc(b.get("fecha_publicacion_parcial", ""))}" data-year="{esc(year)}" data-pages="{esc(b.get("numero_paginas", ""))}" data-format-prices="{format_prices(b)}" data-format-discounts="{format_discounts(b, anchor)}"'
        # Missing optional values have the same runtime meaning as empty ones.
        attrs = re.sub(r' data-(?:published|published-month|year|pages|format-prices|format-discounts)=""', '', attrs)
        affiliate_link = amazon_destination(b)
        affiliate_cta = ('<a class="catalogue-buy-link catalogue-card__buy" href="' + esc(affiliate_link) + '" target="_blank" aria-label="' + esc(amazon_action_label(b)) + ': ' + esc(b["titulo"]) + ' (otra pestaña)" rel="sponsored nofollow noopener noreferrer">' + esc(amazon_action_label(b)) + ' <span aria-hidden="true">↗</span></a>') if affiliate_link else ''
        # Portada y título llevan directamente a Amazon con la etiqueta de afiliado; «Ver ficha» abre la ficha propia.
        # Sin enlace de Amazon comprobado, portada y título siguen abriendo la ficha.
        if affiliate_link:
            amazon_attrs = f'href="{esc(affiliate_link)}" target="_blank" rel="sponsored nofollow noopener noreferrer"'
            cover_link = amazon_attrs + f' aria-label="{esc(b["titulo"])} en Amazon (otra pestaña)"'
            title_link = amazon_attrs + f' aria-label="{esc(b["titulo"])} en Amazon (otra pestaña)"'
        else:
            cover_link = f'href="{url(b)}" target="_blank" rel="noopener noreferrer" aria-label="Ver ficha de {esc(b["titulo"])} (otra pestaña)"'
            title_link = f'href="{url(b)}" target="_blank" rel="noopener noreferrer" aria-label="Abrir ficha de {esc(b["titulo"])} en otra pestaña"'
        cards.append(f'<li class="catalogue-card" {attrs}><a class="catalogue-card__cover" {cover_link}>{image(b,i>1)}</a><div><p class="eyebrow catalogue-when">{release_line(b)}</p>{tags(cats, compact=True)}<h3><a {title_link}>{esc(card_title(b))}</a></h3><p class="catalogue-author">{author_links(b, compact=True)}</p>{byline(b)}<p class="catalogue-card__description">{esc(card_synopsis(b, anchor=anchor))}</p><div class="catalogue-rating" data-rating-book="{esc(b["id"])}" data-isbn="{esc(b.get("isbn13", ""))}"></div>{format_box(b, compact=True, anchor=anchor)}<a class="text-action catalogue-card__ficha" href="{url(b)}" target="_blank" rel="noopener noreferrer" aria-label="Ver ficha de {esc(b["titulo"])} (se abre en otra pestaña)">Ver ficha</a>' + affiliate_cta + '</div></li>')
    sort = '<label>Ordenar por<select name="orden" data-filter="orden" form="catalogue-search-form" disabled><option value="editorial">Publicación · más reciente primero</option><option value="fecha_asc">Publicación · más antigua primero</option><option value="paginas_asc">Páginas · menor a mayor</option><option value="paginas_desc">Páginas · mayor a menor</option>' + ''.join(f'<option value="precio_{k}">{esc(FORMATS[k])} · del más barato al más caro</option>' for k in BOX_ORDER) + '<option value="valoracion_desc" data-sort-market="ratings" disabled>Valoración · mayor a menor</option></select></label>'
    # Lo primero que se ve son los libros ya publicados (los más recientes arriba); los próximos lanzamientos van aparte.
    show = '<label>Mostrar<select name="estado" data-filter="estado" form="catalogue-search-form" disabled><option value="">Ya publicados</option><option value="proximos" id="estado=proximos">Próximos lanzamientos</option><option value="todos">Todos</option></select></label>'
    upcoming = '<a class="catalogue-upcoming-link" href="#estado=proximos" data-catalogue-upcoming>Ver los próximos lanzamientos →</a>'
    filters = render_filters(data, group_options(groups)).replace('<form class=', '<form id="catalogue-search-form" class=',1)
    if page_number > 1:
        filters = show = sort = upcoming = ''
    static_count = f'Mostrando {offset + 1}–{offset + len(visible_books)} de {len(books)} libros' if books else '0 libros'
    catalogue = '<section class="catalogue-section" id="catalogo" aria-label="Buscar libros recomendados"><div class="' + ('catalogue-layout' if page_number == 1 else 'catalogue-static-layout') + '">' + filters + '<div class="catalogue-main"><div class="catalogue-results-head"><h2>El catálogo</h2><div class="catalogue-results-controls">' + show + sort + '</div>' + upcoming + '<p role="status" aria-live="polite" data-catalogue-count>' + static_count + '</p></div><ul class="catalogue-grid">' + newtab(''.join(cards)) + '</ul>' + catalogue_pager(page_number, page_count) + '<div class="catalogue-empty" data-catalogue-empty' + (' hidden' if books else '') + '><h2>' + ('No hay libros con estos filtros' if books else 'Estamos preparando la selección') + '</h2><p>Prueba con otros filtros o restablece la búsqueda.</p><a class="text-action" href="/cuaderno/#lecturas">Explorar las guías de lectura</a></div><noscript><p>Puedes consultar todas las fichas recorriendo las páginas del catálogo. Los filtros requieren JavaScript.</p></noscript></div></div></section>'
    if page_number > 1:
        catalogue = '<p><a class="text-action" href="/recomendaciones/#catalogo" target="_self">Buscar en todo el catálogo</a></p>' + catalogue
    quiz='<details class="catalogue-quiz"><summary>¿Qué te apetece leer? Haz el test y encuentra tu próximo libro</summary><div class="catalogue-quiz__panel"><p>Puedes recorrer las páginas del catálogo para consultar todas las fichas.</p></div></details>' if books and page_number == 1 else ''
    page=template.replace('{{catalogue}}',quiz+catalogue)
    page = page.replace('data-reading-catalogue data-family=', f'data-reading-catalogue data-catalogue-total="{len(books)}" data-catalogue-version="{version}" data-family=')
    modified=max((b['fecha_actualizacion'] for b in books),default='2026-10-20')
    page=re.sub(r'("dateModified":\s*")[^"]*',lambda match:match[1]+modified,page,count=1)
    if books:
        schema={'@context':'https://schema.org','@type':'ItemList','@id':canonical+'#catalogo','name':'Libros recomendados','numberOfItems':len(visible_books),'itemListElement':[{'@type':'ListItem','position':i+1,'item':{'@type':'Book','@id':SITE+url(b)+'#book','name':b['titulo'],'url':SITE+url(b),'image':SITE+b['portada_local']}} for i,b in enumerate(visible_books)]}
        page=page.replace('</head>','<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+'</script>\n</head>')
    crumbs = [('Inicio','/'),('Libros recomendados','/recomendaciones/')] + ([(f'Página {page_number}', catalogue_page_url(page_number))] if page_number > 1 else [])
    breadcrumb={'@context':'https://schema.org',**_breadcrumb_schema(crumbs)}
    page=page.replace('</head>','<script type="application/ld+json">'+json.dumps(breadcrumb,ensure_ascii=False)+'</script>\n</head>',1)
    if page_number > 1:
        title = f'Libros recomendados: página {page_number} | David Porto Díaz'
        description = f'Página {page_number} del catálogo de libros recomendados: fichas de lectura, autores, formatos y fuentes. Vuelve al catálogo para buscar en todas las páginas.'
        page = page.replace(' data-reading-catalogue ', ' ')
        page = page.replace('<h1>Libros recomendados</h1>', f'<h1>Libros recomendados: página {page_number}</h1>')
        page = page.replace('<li aria-current="page">Libros recomendados</li>', f'<li><a href="/recomendaciones/">Libros recomendados</a></li><li aria-current="page">Página {page_number}</li>')
        page = re.sub(r'<title>.*?</title>', lambda _: '<title>' + esc(title) + '</title>', page, count=1)
        for key, value in {'description':description,'og:title':title,'og:description':description,'og:url':canonical,'twitter:title':title,'twitter:description':description}.items():
            page = re.sub(r'(<meta (?:name|property)="'+re.escape(key)+r'" content=")[^"]*', lambda m:m[1]+esc(value), page)
        page = page.replace('href="'+SITE+'/recomendaciones/"', 'href="'+canonical+'"')
        def collection(match):
            node = json.loads(match[1])
            node.update({'@id':canonical,'url':canonical,'name':title,'description':description})
            return '<script type="application/ld+json">'+json.dumps(node, ensure_ascii=False)+'</script>'
        page = re.sub(r'<script type="application/ld\+json">(.*?)</script>', collection, page, count=1, flags=re.S)
    return inject_shell_auto(page)


def render_book(data,b,template):
    canonical=SITE+url(b)
    title=book_title(b,[x for x in data['libros'] if x['estado']=='publicado'])
    description=own_meta_description(b) or book_meta_description(data,b)
    own_before=own_text_section(b,data)
    cats=categories(data,b)
    upcoming=b in upcoming_books([book for book in data['libros'] if book['estado'] == 'publicado'])
    rows=[('Edición',b['edicion'].split(' · ')[0]),('ISBN-13',b.get('isbn13')),('Idioma',LANGUAGES.get(b.get('idioma'),b.get('idioma')))]
    details='<details class="catalogue-details"><summary>Más datos de la edición</summary><dl>'+''.join(f'<dt>{esc(k)}</dt><dd>{esc(v)}</dd>' for k,v in rows if v)+'</dl></details>'
    fragment=''  # Audio and samples are not rendered until all editions can support them.
    reviews=approved_reviews_for(b)
    extra=render_approved_reviews(reviews)
    external=[r for r in b.get('resenas', []) if not r['url'].startswith('https://www.goodreads.com/search?')]
    if external:
        extra+='<details class="catalogue-details"><summary>Opiniones y referencias externas ('+str(len(external))+')</summary><ul>'+''.join(f'<li><a href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">{esc(r["titulo"])}{NEW_TAB}</a></li>' for r in external)+'</ul></details>'
    destination=amazon_destination(b)
    main_format=primary_format(b)
    buy_label=amazon_action_label(b)+(' · '+FORMATS[main_format] if main_format else '')
    buy=format_box(b, anchor=data_anchor([x for x in data['libros'] if x['estado']=='publicado']))+(('<a class="catalogue-buy-link" href="'+esc(destination)+'" target="_blank" aria-label="'+esc(buy_label)+' (otra pestaña)" rel="sponsored nofollow noopener noreferrer">'+esc(buy_label)+' <span aria-hidden="true">↗</span></a>') if destination else '')
    cover=image(b, sizes='(max-width: 600px) 65vw, 400px')
    amazon_href = amazon_destination(b)
    if amazon_href:
        cover='<a href="'+esc(amazon_href)+'" aria-label="'+esc(amazon_action_label(b))+': '+esc(b['titulo'])+' (otra pestaña)" target="_blank" rel="sponsored nofollow noopener noreferrer">'+cover+'</a>'
    speech=''
    main='<main id="contenido" tabindex="-1" class="v1-main reading-catalogue" data-family="recomendaciones" data-reading-catalogue><nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol><li><a href="/">Inicio</a></li><li><a href="/recomendaciones/">Libros recomendados</a></li><li aria-current="page">'+esc(b['titulo'])+'</li></ol></nav><article class="catalogue-book-layout"><div class="catalogue-cover-panel">'+cover+'</div><div><header class="catalogue-book-heading"><p class="eyebrow catalogue-when">'+release_line(b,upcoming)+'</p><h1>'+esc(b['titulo'])+'</h1><p class="catalogue-author">'+author_links(b)+'</p>'+byline(b)+'<div class="catalogue-rating" data-rating-book="'+esc(b['id'])+'" data-isbn="'+esc(b.get('isbn13',''))+'"></div></header>'+buy+own_before+'<div class="catalogue-synopsis" data-catalogue-description>'+''.join('<p>'+esc(p)+'</p>' for p in synopsis_paragraphs(b))+'</div>'+tags(cats, limit=DETAIL_TAGS)
    if b.get('autoria_propia'):
        main+='<p>Obra de David Porto Díaz.</p>'
    if b.get('avisos_contenido'):
        main+='<p><strong>Sobre el contenido:</strong> '+esc(b['avisos_contenido'])+'</p>'
    main+=details+extra+'</div></article>'+related_books(data,b)+'<div class="catalogue-end"><a class="text-action" href="/recomendaciones/">Volver al catálogo</a></div></main>'
    authors=author_records()
    schema={'@context':'https://schema.org','@graph':[{'@type':'Book','@id':canonical+'#book','url':canonical,'name':b['titulo'],'description':schema_synopsis(b),'author':[{'@type':'Person','name':name,**({'@id':SITE+author_url(a)+'#person','url':SITE+author_url(a)} if (a:=next((a for a in authors if a['nombre']==name),None)) else {})} for name in b['autores']],'image':SITE+b['portada_local'],'bookEdition':b['edicion'],**({'publisher':{'@type':'Organization','name':b['editorial'],**({'url':SITE+'/editoriales/'+b['editorial_slug']+'/'} if b.get('editorial_slug') else {})}} if b.get('editorial') else {}),**({'inLanguage':b['idioma']} if b.get('idioma') else {}),**({'numberOfPages':b['numero_paginas']} if b.get('numero_paginas') else {}),**({'bookFormat':'https://schema.org/'+{'tapa-dura':'Hardcover','tapa-blanda':'Paperback','ebook':'EBook','audiolibro':'AudiobookFormat'}[b['formato_edicion']]} if b.get('formato_edicion') else {}),**({'genre':g} if (g:=[c['nombre'] for c in cats if c['tipo']=='genero']) else {}),**({'keywords':', '.join(k)} if (k:=[c['nombre'] for c in cats if c['tipo'] in ('tematica','epoca','temporada')]) else {}),**({'audience':{'@type':'PeopleAudience','audienceType':e[0]}} if (e:=[c['nombre'] for c in cats if c['tipo']=='edad']) else {}),**({'sameAs':[b['fuente_bibliografica_url']]} if b.get('fuente_bibliografica_url','').startswith('https://') else {}),**({'isbn':b['isbn13']} if b.get('isbn13') else {}),**({'datePublished':d} if (d:=b.get('fecha_publicacion') or b.get('fecha_publicacion_parcial')) and d<=b['fecha_actualizacion'] else {})},{'@type':'WebPage','@id':canonical+'#page','url':canonical,'name':title,'description':description,'dateModified':b['fecha_actualizacion'],'mainEntity':{'@id':canonical+'#book'}},{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':label,'item':SITE+href} for i,(label,href) in enumerate([('Inicio','/'),('Libros recomendados','/recomendaciones/'),(b['titulo'],url(b))])]}]}
    if reviews:
        schema['@graph'][0]['review']=[{'@type':'Review','author':{'@type':'Person','name':r['nombre_publico']},'datePublished':r['fecha_envio'],'name':r['titulo_resena'],'reviewBody':r['texto_resena'],'reviewRating':{'@type':'Rating','ratingValue':r['puntuacion'],'bestRating':5,'worstRating':1}} for r in reviews]
        schema['@graph'][0]['aggregateRating']={'@type':'AggregateRating','ratingValue':round(sum(r['puntuacion'] for r in reviews)/len(reviews),2),'ratingCount':len(reviews),'bestRating':5,'worstRating':1}
    return render_detail_page(template,main,canonical,title,description,schema,b)


AUDIENCES=(('infantil',{'infantil'}),('juvenil',{'juvenil','fantasia-juvenil'}),('adultos',{'adultos'}))


def audience(cat_ids):
    """Público declarado (infantil, juvenil, adultos) o None si no consta."""
    return next((name for name,ids in AUDIENCES if cat_ids & ids),None)


def min_age(b):
    """Edad mínima de lectura declarada (Adultos = 18) o None."""
    age=b.get('edad_recomendada') or ''
    if age.casefold().startswith('adult'):
        return 18
    m=re.search(r'\d+',age)
    return int(m.group(0)) if m else None


def related_books(data, book):
    # Cada categoría compartida pesa por lo rara que es («Hockey» dice más que «Romance») y no se cruzan públicos.
    own={c['id'] for c in categories(data,book)}
    wanted={c['id'] for c in categories(data,book) if c['tipo'] in {'genero','tematica'}}
    pool=[(x,{c['id'] for c in categories(data,x)}) for x in data['libros'] if x['estado']=='publicado' and x['id']!=book['id']]
    total=len(pool)+1
    df={c:1+sum(c in cats for _,cats in pool) for c in wanted}
    public,age=audience(own),min_age(book)
    ranked=[]
    for candidate,cats in pool:
        shared=wanted & cats
        same_author=bool(set(book['autores']) & set(candidate['autores']))
        other,other_age=audience(cats),min_age(candidate)
        if not same_author and ((public and other and public!=other) or (age is not None and other_age is not None and abs(age-other_age)>4)):
            continue
        if shared or same_author:
            ranked.append((same_author,sum(math.log(total/df[c]) for c in sorted(shared)),candidate))  # orden fijo: el redondeo no depende del hash
    ranked.sort(key=lambda row:(-row[0],-row[1],row[2]['titulo'].casefold(),row[2]['id']))
    if not ranked:
        return ''
    return '<section class="catalogue-related" aria-labelledby="related-books"><h2 id="related-books">También te puede interesar</h2><ul>'+''.join('<li><a class="catalogue-related__cover" href="'+url(candidate)+'" tabindex="-1" aria-hidden="true">'+image(candidate,True,'120px','catalogue-related__image','')+'</a><a href="'+url(candidate)+'">'+esc(candidate['titulo'])+'</a><p>'+esc(', '.join(candidate['autores']))+'</p></li>' for _,_,candidate in ranked[:6])+'</ul></section>'


def render_detail_page(template,main,canonical,title,description,schema,b=None):
    if len(title) > 75:
        title = title[:63].rsplit(' ', 1)[0] + ' · ' + hashlib.sha256(canonical.encode()).hexdigest()[:8]
    page=template.replace('{{catalogue}}','')
    main=newtab(main)
    page=re.sub(r'<main\b[\s\S]*?</main>',lambda _:main,page,count=1)
    page=re.sub(r'<title>.*?</title>',lambda _:'<title>'+esc(title)+'</title>',page,count=1)
    description=description if len(description)<=160 else description[:157].rsplit(' ',1)[0].rstrip('.,;:')+'…'
    values={'description':description,'og:title':title,'og:description':description,'og:url':canonical,'twitter:title':title,'twitter:description':description}
    if b:
        values.update({'og:image':SITE+b['portada_local'],'og:image:alt':'Portada de '+b['titulo'],'og:image:width':b['portada_ancho'],'og:image:height':b['portada_alto'],'twitter:image':SITE+b['portada_local'],'twitter:image:alt':'Portada de '+b['titulo']})
    book=next((n for n in schema.get('@graph',[]) if n.get('@type')=='Book'),None)
    if book:
        values['og:type']='book'
    for key,value in values.items():
        page=re.sub(r'(<meta (?:name|property)="'+re.escape(key)+r'" content=")[^"]*',lambda m:m[1]+esc(value),page)
    if book:
        # Open Graph de libro: ISBN, páginas de autor y fecha de la edición.
        book_meta=[('book:isbn',book.get('isbn'))]+[('book:author',p.get('url')) for p in book['author']]+[('book:release_date',book.get('datePublished'))]
        page=re.sub(r'<meta property="og:type" content="book">',lambda m:m[0]+''.join(f'\n  <meta property="{k}" content="{esc(v)}">' for k,v in book_meta if v),page,count=1)
    page=page.replace('href="'+SITE+'/recomendaciones/"','href="'+canonical+'"')
    page=re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>',lambda _:'<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')+'</script>',page,count=1)
    return inject_shell_auto(page)


def render_author(a,data,books,template,all_authors=()):
    selected=sorted([b for b in books if a['nombre'] in b['autores']], key=lambda b:(b.get('fecha_publicacion') or b.get('fecha_publicacion_parcial') or str(b.get('anio_publicacion','')), b['titulo']), reverse=True)
    canonical=SITE+author_url(a)
    topics={c['id']:c for b in selected for c in categories(data,b) if c['tipo'] in {'genero','tematica'}}
    publishers={b.get('editorial_slug') or b.get('editorial'):b for b in selected if b.get('editorial')}
    count=len(selected)
    summary=a['nombre']+': '+str(count)+(' libro disponible' if count==1 else ' libros disponibles')+' en este catálogo.'
    bio=a.get('biografia_breve') or (a['descripcion'] if a.get('tipo') != 'bibliografico' else summary)
    biography_source=('<p class="catalogue-source"><a href="'+esc(a['biografia_fuente_url'])+'" target="_blank" rel="noopener noreferrer">Nota biográfica: '+esc(a.get('biografia_fuente_nombre') or 'editorial')+' ↗'+NEW_TAB+'</a>'+(' · Texto de Wikipedia con licencia CC BY-SA 4.0' if a.get('biografia_fuente_nombre') == 'Wikipedia' else '')+'</p>') if a.get('biografia_breve') else ''
    context='<section aria-labelledby="author-context"><h2 id="author-context">Su obra en este catálogo</h2><p>'+esc(summary)+'</p>'
    if topics:
        context+='<p>Géneros y temas presentes en sus libros:</p>'+tags(list(topics.values()))
    if publishers:
        context+='<p>Editoriales: '+', '.join(publisher_link(b) for b in publishers.values())+'.</p>'
    related=[]
    if topics and all_authors:
        by_author={}
        for b in books:
            for name in b['autores']:
                by_author.setdefault(name,[]).append(b)
        for other in all_authors:
            if other['nombre']==a['nombre']: continue
            shared=sum(1 for b in by_author.get(other['nombre'],()) for c in categories(data,b) if c['id'] in topics)
            if shared: related.append((-shared,other['nombre'],other))
        related=[o for _,_,o in sorted(related, key=lambda t:(t[0],t[1]))[:6]]
    if related:
        context+='<p>Autores con géneros y temas parecidos: '+', '.join('<a href="'+esc(author_url(o))+'">'+esc(o['nombre'])+'</a>' for o in related)+'.</p>'
    context+='</section>'
    items=''
    for b in selected:
        metadata=' · '.join(str(v) for v in (publication_date_label(b),b.get('editorial'),(str(b['numero_paginas'])+' páginas') if b.get('numero_paginas') else '') if v)
        items+='<li><a href="'+url(b)+'" target="_blank" rel="noopener noreferrer">'+image(b,True)+'<span>'+esc(b['titulo'])+'</span>'+NEW_TAB+'</a><p>'+esc(metadata)+'</p></li>'
    main='<main id="contenido" tabindex="-1" class="v1-main reading-catalogue catalogue-author-page" data-family="recomendaciones"><nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol><li><a href="/">Inicio</a></li><li><a href="/recomendaciones/">Libros recomendados</a></li><li aria-current="page">'+esc(a['nombre'])+'</li></ol></nav><header class="catalogue-author-hero"><p class="eyebrow">Autores · Libros recomendados</p><h1>'+esc(a['nombre'])+'</h1><p>'+esc(bio)+'</p>'+biography_source+'</header>'+context+'<section aria-labelledby="author-books"><h2 id="author-books">Libros de '+esc(a['nombre'])+' en el catálogo</h2><p>Ediciones ordenadas de la más reciente a la más antigua.</p><ul class="catalogue-author-books">'+items+'</ul></section><div class="catalogue-end"><a class="text-action" href="/recomendaciones/">Explorar todos los libros</a></div></main>'
    person={'@type':'Person','@id':canonical+'#person','name':a['nombre'],'url':canonical,'description':bio}
    if a.get('nacimiento'):
        person['birthDate']=a['nacimiento']
    if a.get('biografia_fuente_url'):
        person['sameAs']=[a['biografia_fuente_url']]
    elif a.get('tipo') != 'bibliografico':
        person['sameAs']=[source['url'] for source in a['fuentes']]
    schema={'@context':'https://schema.org','@graph':[person,{'@type':'CollectionPage','@id':canonical,'url':canonical,'name':a['nombre']+' · Información y libros','dateModified':collection_modified(a,selected),'mainEntity':{'@id':canonical+'#person'},'hasPart':[{'@id':SITE+url(b)+'#book'} for b in selected]},{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':label,'item':SITE+href} for i,(label,href) in enumerate([('Inicio','/'),('Libros recomendados','/recomendaciones/'),(a['nombre'],author_url(a))])]}]}
    titles=', '.join(b['titulo'] for b in selected[:2])
    meta=a['nombre']+': '+(str(count)+(' libro recomendado' if count==1 else ' libros recomendados')+(' ('+titles+')' if titles else '')+', ' if count else '')+'biografía, géneros y editoriales.'
    if len(meta)>160: meta=a['nombre']+': '+str(count)+(' libro recomendado' if count==1 else ' libros recomendados')+', biografía, géneros y editoriales.'
    return render_detail_page(template,main,canonical,a['nombre']+': libros y biografía | David Porto Díaz',meta if a.get('tipo') != 'bibliografico' or count else bio,schema,selected[0] if selected else None)


def _newest_first(books):
    return sorted(books, key=lambda b: (b.get('fecha_publicacion') or b.get('fecha_publicacion_parcial') or str(b.get('anio_publicacion', '')), b['titulo']), reverse=True)


def _book_items(selected):
    items = ''
    for b in selected:
        metadata = ' · '.join(str(v) for v in (publication_date_label(b), b.get('editorial'), (str(b['numero_paginas']) + ' páginas') if b.get('numero_paginas') else '') if v)
        items += '<li><a href="' + url(b) + '" target="_blank" rel="noopener noreferrer">' + image(b, True) + '<span>' + esc(b['titulo']) + '</span>' + NEW_TAB + '</a><p>' + esc(metadata) + '</p></li>'
    return items


def _breadcrumb_schema(trail):
    return {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': label, 'item': SITE + href} for i, (label, href) in enumerate(trail)]}


def render_publisher(p, data, books, template, author_names=(), authors=()):
    """Ficha de un sello que aparece en el catálogo (distinta del directorio de manuscritos)."""
    selected = _newest_first([b for b in books if b.get('editorial_catalogo_slug') == p['slug']])
    canonical = SITE + publisher_url(p)
    count = len(selected)
    topics = {c['id']: c for b in selected for c in categories(data, b) if c['tipo'] in {'genero', 'tematica'}}
    profiles_list = authors
    authors = sorted({name for b in selected for name in b['autores']}, key=str.casefold)
    summary = p['nombre'] + ' (' + p['grupo'] + '): ' + str(count) + (' libro' if count == 1 else ' libros') + ' en este catálogo, según las fichas oficiales de la editorial.'
    context = '<section aria-labelledby="publisher-context"><h2 id="publisher-context">Este sello en el catálogo</h2><p>Pertenece a ' + esc(p['grupo']) + ' y reúne ' + str(count) + (' libro' if count == 1 else ' libros') + ' de este catálogo.</p>'
    if topics:
        context += '<p>Géneros y temas de sus libros:</p>' + tags(list(topics.values()))
    if authors:
        profiles = {a['nombre']: a for a in profiles_list}
        context += '<p>Autores: ' + ', '.join('<a href="' + author_url(profiles[n]) + '">' + esc(n) + '</a>' if n in profiles else esc(n) for n in authors) + '.</p>'
    context += '<p class="catalogue-source">Este sello no figura en nuestro <a href="/editoriales/">directorio de editoriales que aceptan manuscritos</a>.</p></section>'
    main = ('<main id="contenido" tabindex="-1" class="v1-main reading-catalogue catalogue-author-page" data-family="recomendaciones"><nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol><li><a href="/">Inicio</a></li><li><a href="/recomendaciones/">Libros recomendados</a></li><li><a href="/recomendaciones/editoriales/">Editoriales del catálogo</a></li><li aria-current="page">' + esc(p['nombre']) + '</li></ol></nav>'
            '<header class="catalogue-author-hero"><p class="eyebrow">Editoriales · Libros recomendados</p><h1>' + esc(p['nombre']) + '</h1><p>' + esc(summary) + '</p></header>' + context
            + '<section aria-labelledby="publisher-books"><h2 id="publisher-books">Libros de ' + esc(p['nombre']) + ' en el catálogo</h2><p>Ediciones ordenadas de la más reciente a la más antigua.</p><ul class="catalogue-author-books">' + _book_items(selected) + '</ul></section>'
            '<details class="catalogue-details"><summary>Fuentes</summary><ul>' + ''.join('<li><a href="' + esc(s['url']) + '" target="_blank" rel="noopener noreferrer">' + esc(s['titulo']) + NEW_TAB + '</a></li>' for s in p['fuentes']) + '</ul></details>'
            '<div class="catalogue-end"><a class="text-action" href="/recomendaciones/">Explorar todos los libros</a></div></main>')
    # Un sello que comparte nombre con un autor (p. ej. «DK») se distingue para no mezclar entidades.
    org_name = p['nombre'] + ' (editorial)' if p['nombre'] in author_names else p['nombre']
    org = {'@type': 'Organization', '@id': canonical + '#org', 'name': org_name, 'url': canonical, 'parentOrganization': {'@type': 'Organization', 'name': p['grupo']}}
    schema = {'@context': 'https://schema.org', '@graph': [org, {'@type': 'CollectionPage', '@id': canonical, 'url': canonical, 'name': p['nombre'] + ' · Libros del catálogo', 'dateModified': collection_modified(p, selected), 'mainEntity': {'@id': canonical + '#org'}, 'hasPart': [{'@id': SITE + url(b) + '#book'} for b in selected]},
                                                  _breadcrumb_schema([('Inicio', '/'), ('Libros recomendados', '/recomendaciones/'), ('Editoriales del catálogo', '/recomendaciones/editoriales/'), (p['nombre'], publisher_url(p))])]}
    return render_detail_page(template, main, canonical, p['nombre'] + ' · Libros del catálogo | David Porto Díaz', summary, schema, selected[0] if selected else None)


def first_sentence(text, limit=160):
    sentence = re.split(r'(?<=[.!?])\s+', text, 1)[0]
    return sentence if len(sentence) <= limit else sentence[:limit - 1].rsplit(' ', 1)[0].rstrip(' ,;:') + '…'


def render_authors_index(authors, books, template):
    canonical = SITE + '/recomendaciones/autores/'
    rows = sorted(((a, [b for b in books if a['nombre'] in b['autores']]) for a in authors), key=lambda r: r[0]['nombre'].casefold())
    rows = [(a, bs) for a, bs in rows if bs]
    items = ''.join('<li><a href="' + author_url(a) + '">' + image(_newest_first(bs)[0], True, '120px', 'catalogue-index__image', '') + '<span>' + esc(a['nombre']) + '</span></a><p>' + str(len(bs)) + (' libro' if len(bs) == 1 else ' libros') + ' · ' + esc(', '.join(b['titulo'] for b in _newest_first(bs)[:2])) + ('…' if len(bs) > 2 else '') + '</p>' + ('<p class="catalogue-index__bio">' + esc(first_sentence(a['biografia_breve'])) + '</p>' if a.get('biografia_breve') else '') + '</li>' for a, bs in rows)
    summary = 'Autores de los libros recomendados: ' + str(len(rows)) + ' fichas con sus libros, ediciones y editoriales.'
    main = ('<main id="contenido" tabindex="-1" class="v1-main reading-catalogue catalogue-author-page" data-family="recomendaciones"><nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol><li><a href="/">Inicio</a></li><li><a href="/recomendaciones/">Libros recomendados</a></li><li aria-current="page">Autores</li></ol></nav>'
            '<header class="catalogue-author-hero"><p class="eyebrow">Libros recomendados</p><h1>Autores</h1><p>' + esc(summary) + '</p></header>'
            '<section aria-labelledby="authors-list"><h2 id="authors-list">Todos los autores</h2><ul class="catalogue-author-books">' + items + '</ul></section>'
            '<div class="catalogue-end"><a class="text-action" href="/recomendaciones/">Explorar todos los libros</a></div></main>')
    schema = {'@context': 'https://schema.org', '@graph': [{'@type': 'CollectionPage', '@id': canonical, 'url': canonical, 'name': 'Autores de los libros recomendados', 'dateModified': collection_modified({}, books), 'hasPart': [{'@id': SITE + author_url(a) + '#person'} for a, _ in rows]},
                                                  _breadcrumb_schema([('Inicio', '/'), ('Libros recomendados', '/recomendaciones/'), ('Autores', '/recomendaciones/autores/')])]}
    return render_detail_page(template, main, canonical, 'Autores de los libros recomendados | David Porto Díaz', summary, schema, None)


def render_publishers_index(catalogue_publishers, books, template):
    """Sellos con libros en el catálogo: los del directorio enlazan a su ficha de manuscritos."""
    canonical = SITE + '/recomendaciones/editoriales/'
    entries = {}
    for b in books:
        if b.get('editorial_catalogo_slug'):
            p = next(p for p in catalogue_publishers if p['slug'] == b['editorial_catalogo_slug'])
            entries.setdefault(p['slug'], [p['nombre'], publisher_url(p), 0, b, p['grupo']])[2] += 1
        elif b.get('editorial_slug'):
            entries.setdefault(b['editorial_slug'], [b['editorial'], '/editoriales/' + b['editorial_slug'] + '/', 0, b, ''])[2] += 1
    ordered = sorted(entries.values(), key=lambda e: e[0].casefold())
    items = ''.join('<li><a href="' + e[1] + '">' + image(e[3], True, '120px', 'catalogue-index__image', '') + '<span>' + esc(e[0]) + '</span></a><p>' + str(e[2]) + (' libro' if e[2] == 1 else ' libros') + ' en el catálogo' + (' · ' + esc(e[4]) if e[4] else '') + '</p></li>' for e in ordered)
    summary = 'Editoriales de los libros recomendados: ' + str(len(ordered)) + ' sellos con sus libros.'
    main = ('<main id="contenido" tabindex="-1" class="v1-main reading-catalogue catalogue-author-page" data-family="recomendaciones"><nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol><li><a href="/">Inicio</a></li><li><a href="/recomendaciones/">Libros recomendados</a></li><li aria-current="page">Editoriales del catálogo</li></ol></nav>'
            '<header class="catalogue-author-hero"><p class="eyebrow">Libros recomendados</p><h1>Editoriales del catálogo</h1><p>' + esc(summary) + '</p></header>'
            '<section aria-labelledby="publishers-list"><h2 id="publishers-list">Todos los sellos</h2><ul class="catalogue-author-books">' + items + '</ul></section>'
            '<div class="catalogue-end"><a class="text-action" href="/editoriales/">Directorio de editoriales que aceptan manuscritos</a> · <a class="text-action" href="/recomendaciones/">Explorar todos los libros</a></div></main>')
    schema = {'@context': 'https://schema.org', '@graph': [{'@type': 'CollectionPage', '@id': canonical, 'url': canonical, 'name': 'Editoriales del catálogo', 'dateModified': collection_modified({}, books)},
                                                  _breadcrumb_schema([('Inicio', '/'), ('Libros recomendados', '/recomendaciones/'), ('Editoriales del catálogo', '/recomendaciones/editoriales/')])]}
    return render_detail_page(template, main, canonical, 'Editoriales de los libros recomendados | David Porto Díaz', summary, schema, None)


def registry_entries(books):
    return [{"id": "reading-book-" + b["id"], "url": url(b), "label": b["titulo"], "shortLabel": b["titulo"], "type": "article", "territory": "recomendaciones", "parentId": "recommendations-hub", "hubId": "recommendations-hub", "discoverability": "secondary", "audience": ["reader"], "jobs": ["buscar-lecturas"], "sourceFile": url(b).lstrip('/') + 'index.html'} for b in books]


def render_map(original, books, authors=(), publishers=()):
    start, end = '<!-- reading-catalogue-map:start -->', '<!-- reading-catalogue-map:end -->'
    original = re.sub(re.escape(start) + r'[\s\S]*?' + re.escape(end) + r'\n?', '', original)
    if not books:
        return original
    links = ''.join(f'<li><a href="{url(b)}">{esc(b["titulo"])} — {esc(", ".join(b["autores"]))}</a></li>' for b in books)
    continuation_links = ''.join(f'<li><a href="{catalogue_page_url(n)}">Catálogo: página {n}</a></li>' for n in range(2, math.ceil(len(books) / CATALOGUE_PAGE_SIZE) + 1))
    author_links = ''.join(f'<li><a href="{author_url(a)}">{esc(a["nombre"])}</a></li>' for a in authors if any(a['nombre'] in b['autores'] for b in books))
    block = start + '<section class="directory-section"><h2>Libros recomendados</h2><p><a href="/recomendaciones/">Explorar el catálogo de lectura</a> · <a href="/recomendaciones/autores/">Autores</a> · <a href="/recomendaciones/editoriales/">Editoriales del catálogo</a></p><details class="directory-reading-books"><summary>Ver las fichas de lectura</summary><ul class="directory-list">' + links + '</ul></details></section>' + end + '\n'
    if author_links:
        block = block.replace('</section>', '<details class="directory-reading-books"><summary>Ver autores del catálogo</summary><ul class="directory-list">' + author_links + '</ul></details></section>')
    if continuation_links:
        block = block.replace('<details', '<ul class="directory-list">' + continuation_links + '</ul><details', 1)
    publisher_links = ''.join(f'<li><a href="{publisher_url(p)}">{esc(p["nombre"])}</a></li>' for p in publishers if any(b.get('editorial_catalogo_slug') == p['slug'] for b in books))
    if publisher_links:
        block = block.replace('</section>', '<details class="directory-reading-books"><summary>Ver editoriales del catálogo</summary><ul class="directory-list">' + publisher_links + '</ul></details></section>')
    require('</main>' in original, 'Mapa del sitio sin main')
    return original.replace('</main>', block + '</main>', 1)


def render_outputs(root, data):
    """Every file this builder owns, as {relative path: text}; the publisher allowlist must admit them all."""
    books = validate(data, root)
    OWN_TEXTS.clear()
    OWN_TEXTS.update(load_own_texts(root))
    index_categories(data)
    authors = author_records(root)
    template = (root / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
    outputs = {'recomendaciones/index.html': render_hub(data, books, template)}
    for number in range(2, max(1, math.ceil(len(books) / CATALOGUE_PAGE_SIZE)) + 1):
        outputs[catalogue_page_url(number).lstrip('/') + 'index.html'] = render_hub(data, books, template, number)
    map_path = root / 'mapa-del-sitio/index.html'
    if map_path.exists():
        outputs['mapa-del-sitio/index.html'] = render_map(map_path.read_text(encoding='utf-8'), books, authors, publisher_records(root))
    for b in books:
        outputs[url(b).lstrip('/') + 'index.html'] = render_book(data, b, template)
    active_authors = [a for a in authors if any(a['nombre'] in b['autores'] for b in books)]
    for a in active_authors:
        outputs[author_url(a).lstrip('/') + 'index.html'] = render_author(a, data, books, template, active_authors)
    outputs['recomendaciones/autores/index.html'] = render_authors_index(active_authors, books, template)
    catalogue_publishers = publisher_records(root)
    active_publishers = [p for p in catalogue_publishers if any(b.get('editorial_catalogo_slug') == p['slug'] for b in books)]
    for p in active_publishers:
        outputs[publisher_url(p).lstrip('/') + 'index.html'] = render_publisher(p, data, books, template, {a['nombre'] for a in authors}, active_authors)
    outputs['recomendaciones/editoriales/index.html'] = render_publishers_index(catalogue_publishers, books, template)
    outputs[ICS_PATH] = render_release_ics(books)
    outputs[DEALS_PATH] = render_deals(books)
    outputs[LLMS_PATH] = render_llms_index(data, books, active_authors, active_publishers)
    existing = root / 'recomendaciones/libros'
    orphans = [p for p in existing.glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
    orphans += [p for p in (root / 'recomendaciones/pagina').glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
    orphans += [p for p in (root / 'recomendaciones/autores').glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
    orphans += [p for p in (root / 'recomendaciones/editoriales').glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
    require(not orphans, 'Hay fichas existentes fuera de los datos: revisar retirada/URL antes de eliminarlas')
    registry = json.loads((root / 'data/content-registry.json').read_text(encoding='utf-8'))
    registry['entries'] = [e for e in registry['entries'] if not e['id'].startswith(('reading-book-', 'reading-author-', 'reading-publisher-', 'reading-index-', 'reading-page-'))] + registry_entries(books)
    registry['entries'] += [{'id': 'reading-author-' + a['slug'], 'url': author_url(a), 'label': a['nombre'], 'shortLabel': a['nombre'], 'type': 'article', 'territory': 'recomendaciones', 'parentId': 'recommendations-hub', 'hubId': 'recommendations-hub', 'discoverability': 'secondary', 'audience': ['reader'], 'jobs': ['buscar-lecturas'], 'sourceFile': author_url(a).lstrip('/') + 'index.html'} for a in active_authors]
    registry['entries'] += [{'id': 'reading-publisher-' + p['slug'], 'url': publisher_url(p), 'label': p['nombre'], 'shortLabel': p['nombre'], 'type': 'article', 'territory': 'recomendaciones', 'parentId': 'recommendations-hub', 'hubId': 'recommendations-hub', 'discoverability': 'secondary', 'audience': ['reader'], 'jobs': ['buscar-lecturas'], 'sourceFile': publisher_url(p).lstrip('/') + 'index.html'} for p in active_publishers]
    registry['entries'] += [{'id': 'reading-index-' + key, 'url': '/recomendaciones/' + key + '/', 'label': label, 'shortLabel': label, 'type': 'article', 'territory': 'recomendaciones', 'parentId': 'recommendations-hub', 'hubId': 'recommendations-hub', 'discoverability': 'secondary', 'footerEligible': True, 'audience': ['reader'], 'jobs': ['buscar-lecturas'], 'sourceFile': 'recomendaciones/' + key + '/index.html'} for key, label in (('autores', 'Autores'), ('editoriales', 'Editoriales del catálogo'))]
    registry['entries'] += [{'id':f'reading-page-{n}','url':catalogue_page_url(n),'label':f'Libros recomendados: página {n}','shortLabel':f'Página {n}','type':'article','territory':'recomendaciones','parentId':'recommendations-hub','hubId':'recommendations-hub','discoverability':'secondary','searchIndex':False,'sourceFile':catalogue_page_url(n).lstrip('/')+'index.html'} for n in range(2, max(1, math.ceil(len(books) / CATALOGUE_PAGE_SIZE)) + 1)]
    outputs['data/content-registry.json'] = json.dumps(registry, ensure_ascii=False, indent=2) + '\n'
    return books, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--data', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        data = json.loads((args.data or root / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books, outputs = render_outputs(root, data)
        drift = []
        for rel, text in outputs.items():
            target = root / rel
            current = None if not target.exists() else (target.read_bytes().decode('utf-8') if rel.endswith('.ics') else target.read_text(encoding='utf-8'))
            if current != text:
                drift.append(rel)
                if not args.check:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    (target.write_bytes(text.encode('utf-8')) if rel.endswith('.ics') else target.write_text(text, encoding='utf-8', newline='\n'))
        require(not args.check or not drift, 'Catálogo desactualizado: ' + ', '.join(drift))
        print(f'Catálogo OK: {len(books)} libros publicados; {len(drift)} archivos {"pendientes" if args.check else "actualizados"}.')
        return 0
    except (ValidationError, ValueError, KeyError, TypeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
