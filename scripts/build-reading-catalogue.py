#!/usr/bin/env python3
"""Catálogo estático de lectura. Una obra, una URL; datos privados fuera del HTML.

python scripts/build-reading-catalogue.py [--check] [--root .] [--data ruta.json]
La carga desde Drive y Pinterest pertenecen a fases posteriores.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import html
import json
import math
import os
import re
import unicodedata
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import parse_qs, quote, urlencode, urlparse
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_shell import inject_shell_auto
from reading_intake_core import strip_shouting, decode_text_entities
import reading_cover_store as cover_store
import reading_author_links as third_party_links
import site_clock

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://davidportodiaz.com"
COMMUNITIES = ROOT / "data" / "communities.json"


def community_cta() -> str:
    """Llamada a unirse a Telegram o Discord, plegada junto a «Ver los próximos lanzamientos» para no empujar
    la primera tarjeta (presupuesto de qa/catalogue-mobile-discovery.mjs). Los enlaces salen de
    data/communities.json, los mismos de /comunidad/."""
    config = json.loads(COMMUNITIES.read_text(encoding="utf-8"))
    groups = {g["id"]: g for g in config["groups"]}
    digest = groups["todos"]
    telegram = digest.get("invite") or config["platforms"]["telegram"]["invite"]
    discord = config["platforms"]["discord"]["invite"]
    return (
        '<details class="catalogue-community"><summary class="catalogue-upcoming-link">Recíbelos en Telegram o Discord</summary>'
        '<div class="catalogue-community__panel" id="comunidad" role="region" aria-labelledby="catalogue-community-title">'
        '<h3 id="catalogue-community-title">Únete a la comunidad de Telegram o Discord</h3>'
        '<p>Cada día a las 11:30 avisamos de los libros que salen a la venta en España. Tú eliges cuántos mensajes recibes:</p>'
        '<ul class="catalogue-community__options">'
        f'<li><strong>1 mensaje al día.</strong> {html.escape(digest["name"])}: todos los libros de hoy y un enlace para verlos juntos en Amazon.</li>'
        '<li><strong>1 mensaje los lunes.</strong> Próximos lanzamientos: lo que sale en los 7 días siguientes.</li>'
        '<li><strong>Libro a libro.</strong> Portada, editorial y sinopsis de cada novedad, también solo de tus géneros (thriller, romántica, fantasía, histórica…).</li>'
        '</ul><p class="catalogue-community__actions">'
        f'<a class="catalogue-community__join catalogue-community__join--telegram" href="{html.escape(telegram)}" rel="noopener">Telegram · 1 mensaje al día</a>'
        f'<a class="catalogue-community__join catalogue-community__join--discord" href="{html.escape(discord)}" rel="noopener">Entrar en Discord</a>'
        '<a class="text-action" href="/comunidad/">Ver todos los canales y elegir</a></p>'
        '<p class="catalogue-community__note">Gratis. Si un día no hay libros nuevos, no se publica nada. Puedes silenciar o abandonar cualquier canal cuando quieras.</p>'
        '</div></details>'
    )
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
TYPES = {"genero": "Género", "tematica": "Temática", "temporada": "Temporada", "edad": "Edad", "contenido": "Contenido", "epoca": "Época"}
# Lo único que se enseña y se filtra: género (materias de Amazon y de la editorial) y edad (la declarada).
# Temática, temporada, contenido y época son reglas propias sobre palabras clave: «Día de la Madre» salía
# en cualquier libro de crianza y San Valentín en cualquier romance (David, 08/11). Siguen en los datos
# solo para agrupar (Tipo de libro) y relacionar fichas; nunca como etiqueta, filtro ni texto.
PUBLIC_TYPES = ("genero", "edad")


def public(cats):
    return [c for c in cats if c["tipo"] in PUBLIC_TYPES]
NO_AGE = {"tipo": "edad", "id": "sin-edad", "nombre": "Sin edad indicada"}
NO_GENRE = {"tipo": "genero", "id": "sin-genero", "nombre": "Sin género indicado"}
NO_VALUE = {"edad": NO_AGE, "genero": NO_GENRE}  # por faceta: valor de reserva para los libros que no traen ninguno


def facet_categories(cats):
    """Categorías públicas para filtrar; un libro sin franja de edad o sin género entra en «Sin edad indicada» /
    «Sin género indicado» en vez de quedar fuera del filtro (6 787 de 7 427 no traen edad; 23 no traen género) o de
    contarse como «Adultos» sin saberlo. Vale también para los libros que traiga la carga nocturna."""
    shown = public(cats)
    return shown + [fallback for kind, fallback in NO_VALUE.items() if not any(c["tipo"] == kind for c in shown)]


PRICE_FIELDS = {'precio_centimos', 'precio_referencia_centimos'}
# Una oferta solo se muestra si Amazon la confirmó hace como mucho estos días; después desaparece sola.
OFFER_MAX_DAYS = 3
BOOK_FIELDS = set("id slug titulo autores descripcion_breve estado portada_local portada_fuente_url portada_edicion_verificada autorizacion_o_base_uso portada_fecha_revision portada_ancho portada_alto fuente_bibliografica_url fecha_verificacion descripcion_original_confirmada url_amazon_afiliada isbn13 edicion editorial fecha_publicacion anio_publicacion numero_paginas fuente_publicacion_url idioma edad_recomendada fuente_edad_url avisos_contenido lectura_personal_confirmada evidencia_lectura autoria_propia resenas fragmento_url fecha_actualizacion editorial_catalogo_slug pvp_centimos pvp_fecha_verificacion audio_descripcion audio_voz formatos_compra fragmento_texto fragmento_uso_autorizado fragmento_base_uso audio_fragmento".split())
FORMATS = {"tapa-blanda": "Tapa blanda", "tapa-dura": "Tapa dura", "ebook": "Kindle", "audiolibro": "Audiolibro"}
BOOK_FIELDS.update({'editorial_slug', 'formato_edicion', 'amazon_busqueda_isbn', 'fecha_publicacion_parcial', 'precios_amazon_revision', 'formatos_amazon_buscados', 'formatos_pagina_buscados', 'portadas_amazon_buscadas', 'portada_sustituida'})
BOOK_FIELDS.update({'sinopsis_breve', 'sinopsis_fuente_url', 'sinopsis_tipo', 'categorias_excluidas', 'sinopsis_completa'})


class ValidationError(ValueError):
    """Fallo de validación con su dueño como dato: `libro` (id del libro, o None si es una regla general), `regla`
    (el motivo sin el libro, para agrupar incidencias) y `otro` (el libro gemelo de una portada duplicada). La
    cuarentena aparta por estos atributos; el texto es solo para personas y puede cambiar sin consecuencias.
    `general` marca un fallo de un fichero común (sellos, autores): nunca se atribuye a la ficha en curso, porque
    apartar ese libro ocultaría el error y el siguiente lote lo arrastraría.
    Sin id utilizable (id inválido o repetido) el dueño va por su sitio: `posicion` en `libros` o `relacion` en
    `libro_categorias` (R5-10). `otro` es el libro con el que choca cualquier unicidad entre dos fichas."""

    def __init__(self, message, libro=None, regla=None, otro=None, general=False, posicion=None, relacion=None):
        super().__init__(message)
        self.libro, self.regla, self.otro, self.general = libro, regla, otro, general
        self.posicion, self.relacion = posicion, relacion


def fallo_general(carga):
    """Los fallos al validar un fichero común salen como generales (`ValidationError.general`)."""
    @functools.wraps(carga)
    def envuelta(*args, **kwargs):
        try:
            return carga(*args, **kwargs)
        except ValidationError as exc:
            exc.general, exc.libro = True, None
            raise
    return envuelta


def require(ok, message, libro=None, regla=None, otro=None):
    if not ok:
        raise ValidationError(message, libro=libro, regla=regla, otro=otro)


def _regla(message, libro):
    """El motivo sin el id del libro delante («<id>: …» o «<id>.campo: …»)."""
    if libro and message.startswith(libro):
        return message[len(libro):].lstrip('.:').strip() or message
    return message


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
        raise ValidationError(f"{name}: fecha inválida", regla='fecha inválida') from exc


def valid_isbn(value):
    return isinstance(value, str) and bool(re.fullmatch(r"97[89][0-9]{10}", value)) and sum(int(n) * (1 if i % 2 == 0 else 3) for i, n in enumerate(value)) % 10 == 0


def con_libro(valida):
    """Un fallo dentro de la ficha de un libro sale con ese libro en `ValidationError.libro` (y su motivo en
    `regla`): `valida` anota en `actual['libro']` la ficha que está revisando."""
    @functools.wraps(valida)
    def envuelta(data, root):
        actual = {}
        try:
            return valida(data, root, actual)
        except ValidationError as exc:
            if exc.libro is None and exc.posicion is None and exc.relacion is None and not exc.general:
                exc.libro = actual.get('libro')
                if exc.libro is None:
                    exc.posicion, exc.relacion = actual.get('posicion'), actual.get('relacion')
            if exc.regla is None:
                exc.regla = _regla(str(exc), exc.libro)
            raise
        except Exception as exc:
            # R5-10 (18): un dato con forma inesperada que revienta el código al recorrer una ficha o una relación
            # es de esa ficha; solo lo que salta fuera de ellas (esquema global) sigue sin dueño.
            libro, posicion, relacion = actual.get('libro'), actual.get('posicion'), actual.get('relacion')
            if libro is None and posicion is None and relacion is None:
                raise
            raise ValidationError(f'{libro or "libro"}: excepción {type(exc).__name__}: {exc}'[:300], libro=libro,
                                  regla='excepcion', posicion=None if libro else posicion,
                                  relacion=None if libro else relacion) from exc
    return envuelta


@con_libro
def validate(data, root, actual):
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
    book_ids, covers = set(), set()
    # Cada unicidad entre dos fichas guarda quién tenía ya el valor: el fallo lleva a los dos (`libro` y `otro`) y la
    # cuarentena aparta el que cambió, no el que ya estaba publicado así (R5-10, hallazgo 15).
    slug_owner, isbn_owner, amazon_owner, work_owner, desc_owner, hash_owner = ({} for _ in range(6))

    def unico(owners, key, name, regla):
        require(key not in owners, f'{name}: {regla} (igual que {owners.get(key)})', regla=regla, otro=owners.get(key))
        owners[key] = name

    for pos, b in enumerate(books):
        # Todo fallo desde aquí hasta el final de la ficha es de este libro: por su id si es utilizable y único; si
        # no, por su posición en la lista.
        actual['posicion'] = pos
        actual['libro'] = b['id'] if isinstance(b, dict) and isinstance(b.get('id'), str) and SLUG.fullmatch(b['id']) and b['id'] not in book_ids else None
        unknown = set(b) - BOOK_FIELDS if isinstance(b, dict) else set()
        # Nombrar el libro (y los campos) permite que la cuarentena aparte solo esa ficha; un campo colado
        # por una fase de la carga ya no tumba todo el lote con un error sin dueño.
        require(isinstance(b, dict) and not unknown,
                f"{b['id']}: campos desconocidos: {', '.join(sorted(unknown))}"
                if unknown and isinstance(b.get("id"), str) and SLUG.fullmatch(b["id"]) else "Libro: campos desconocidos")
        for key in ("id", "slug", "titulo", "estado"):
            require(isinstance(b.get(key), str) and b[key].strip(), f"Libro sin {key}")
        name = b["id"]
        require(SLUG.fullmatch(name) and name not in book_ids, f"{name}: id inválido o duplicado", regla='id inválido o duplicado')
        require(SLUG.fullmatch(b["slug"]), f"{name}: slug inválido")
        unico(slug_owner, b['slug'], name, 'slug duplicado')
        book_ids.add(name)
        require(b["estado"] in {"borrador", "listo", "publicado"}, f"{name}: estado inválido")
        require(isinstance(b.get("autores"), list) and b["autores"] and all(isinstance(a, str) and a.strip() for a in b["autores"]), f"{name}: autores debe ser una lista")
        work = (b['titulo'].strip().casefold(), tuple(sorted(a.strip().casefold() for a in b['autores'])))
        unico(work_owner, work, name, 'obra duplicada; reunir las ediciones en una ficha')
        if b.get("isbn13"):
            require(valid_isbn(b["isbn13"]), f"{name}: ISBN inválido")
            unico(isbn_owner, b['isbn13'], name, 'ISBN duplicado')
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
        unico(desc_owner, b['descripcion_breve'].strip().casefold(), name, 'descripción duplicada')
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
        if "fecha_publicacion" in b:  # presente pero null/vacía también se rechaza aquí, no al renderizar
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
        # Portada del repo o, si está en el almacén externo (data/reading-covers-store.json), su copia local cuando la
        # carga la tiene a mano. Sin bytes (build sin copia del almacén) cuenta la huella registrada en el manifiesto:
        # la comprobación de duplicados es la misma para las dos (Codex/CodeRabbit #1495).
        stored = cover_store.stored_digest(cover, root)
        local = cover_store.local_file(cover, root)
        file = local.resolve() if local else (root / cover.lstrip("/")).resolve()
        if local is None and stored:
            digest = stored
        else:
            inside = file.is_relative_to(root.resolve()) or (stored is not None and local is not None)
            require(inside and file.is_file(), f"{name}: portada local inexistente")
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            require(stored is None or digest == stored, f"{name}: la portada del almacén no coincide con su huella", regla='portada corrupta')
        require(cover not in covers and digest not in hash_owner, f"{name}: portada duplicada (igual que {hash_owner.get(digest, 'otra ruta')})",
                regla='portada duplicada', otro=hash_owner.get(digest))
        covers.add(cover); hash_owner[digest] = b.get("id", name)
        require(all(type(b.get(k)) is int and b[k] > 0 for k in ("portada_ancho", "portada_alto")), f"{name}: dimensiones de portada obligatorias")
        if local is not None or not stored:
            try:
                with Image.open(file) as img:
                    require(img.size == (b['portada_ancho'], b['portada_alto']), f"{name}: dimensiones no coinciden con la portada")
                    require(img.format in {'JPEG', 'PNG', 'WEBP'}, f"{name}: formato de portada inválido")
                    img.verify()
            except OSError as exc:
                raise ValidationError(f"{name}: portada corrupta", libro=name, regla='portada corrupta') from exc
        if b.get("url_amazon_afiliada"):
            url = b["url_amazon_afiliada"]
            require(https(url), f"{name}: URL Amazon inválida")
            parsed = urlparse(url)
            direct = parsed.hostname in {"amazon.es", "www.amazon.es"} and bool(re.fullmatch(r"/(?:[^/]+/)?(?:dp|gp/product)/[A-Z0-9]{10}/?", parsed.path)) and bool(re.fullmatch(r"[a-zA-Z0-9-]+", parse_qs(parsed.query).get("tag", [""])[0]))
            short = parsed.hostname == "amzn.to" and bool(re.fullmatch(r"/[A-Za-z0-9]+", parsed.path)) and not parsed.query
            require(direct or short, f"{name}: se requiere enlace de producto Amazon.es con tag o enlace corto verificado")
            product = (parsed.hostname, parsed.path) if short else re.search(r"(?:dp|gp/product)/([A-Z0-9]{10})", parsed.path).group(1)
            unico(amazon_owner, product, name, 'producto Amazon duplicado')
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
    actual['libro'] = actual['posicion'] = None
    excluded_by_book = {}
    for b in books:
        excluded = b.get('categorias_excluidas', [])
        require(isinstance(excluded, list) and all(isinstance(c, str) and c in ids for c in excluded), f"{b['id']}: exclusiones de categorías inválidas", libro=b['id'])
        excluded_by_book[b['id']] = set(excluded)
    seen = set()
    for i, rel in enumerate(relations):
        # Una relación rota es de su libro si existe; si no, de la propia relación (la cuarentena la quita).
        actual['relacion'] = i
        owner = rel.get('libro_id') if isinstance(rel, dict) else None
        actual['libro'] = owner if isinstance(owner, str) and owner in book_ids else None
        require(isinstance(rel, dict) and set(rel) == {"libro_id", "categoria_id"}
                and isinstance(rel["libro_id"], str) and isinstance(rel["categoria_id"], str), "Relación mal formada")
        pair = (rel["libro_id"], rel["categoria_id"])
        require(pair[0] in book_ids and pair[1] in ids and pair not in seen, "Relación duplicada o referencia inexistente")
        require(pair[1] not in excluded_by_book[pair[0]], f"{pair[0]}: categoría {pair[1]} asignada y excluida simultáneamente",
                libro=pair[0], regla='categoría asignada y excluida simultáneamente')
        seen.add(pair)
    actual['libro'] = actual['relacion'] = None
    # Conjunto precalculado: buscar por libro en todas las relaciones crecía con el cuadrado del catálogo.
    active = {c["id"] for c in cats if c["activa"]}
    with_active = {r["libro_id"] for r in relations if r["categoria_id"] in active}
    for b in books:
        if b["estado"] != "borrador":
            require(b["id"] in with_active, f"{b['id']}: sin categoría activa", libro=b['id'])
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


def category_index(data):
    """Índice libro → categorías: el de main() si está activo para `data`; si no, uno nuevo para esta llamada.

    Quien recorre muchos libros lo pide una vez y lo pasa a categories(): sin índice, cada libro recorre todas las
    relaciones y el coste crece con el cuadrado del catálogo (los contratos que pintan fichas tardaban minutos).
    """
    if CATEGORY_INDEX is not None and CATEGORY_INDEX[0] is data:
        return CATEGORY_INDEX[1]
    index = {}
    for r in data.get('libro_categorias', ()):
        index.setdefault(r['libro_id'], set()).add(r['categoria_id'])
    return index


def categories(data, b, index=None):
    if index is not None:
        ids = index.get(b["id"], set())
    elif CATEGORY_INDEX is not None and CATEGORY_INDEX[0] is data:
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
    cats = public(cats)
    def group(items):
        # La época ya no es filtro del catálogo: se muestra como etiqueta sin enlace.
        return '<ul class="catalogue-tags' + (' catalogue-tags--compact' if compact else '') + '">' + ''.join(f'<li><span>{esc(c["nombre"])}</span></li>' if c['tipo'] == 'epoca' else f'<li><a href="/recomendaciones/#{esc(c["tipo"])}={esc(c["id"])}">{esc(c["nombre"])}</a></li>' for c in items) + '</ul>'
    priority={'genero':0,'temporada':1,'tematica':2,'epoca':3,'contenido':4,'edad':5}
    if compact:
        # La edad ya la sugiere la portada: se queda en filtros y ficha, no en la tarjeta.
        cats = [c for c in cats if c['tipo'] != 'edad']
    if compact or limit:
        # Las más informativas primero; la tarjeta resume y la ficha tiene un hueco fijo.
        from reading_taxonomy import category_priority
        cats = sorted(cats, key=category_priority)[:CARD_TAGS if compact else limit]
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
    today = date.fromisoformat(anchor[:10]) if anchor else site_clock.site_today()
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
        # Un fichero de textos roto no tumba el lote: se salta con aviso (la puerta de scripts/reading-texts.py lo
        # rechaza en su PR) y el libro conserva su descripción base.
        if t.get('id') != path.stem or not all(isinstance(x, dict) and x.get('modulo') in MODULE_TITLES for x in t.get('bloques', [])):
            print(f'::warning::{path.name}: textos propios ignorados (id distinto del fichero o módulo desconocido)', flush=True)
            continue
        if t.get('bloques'):
            texts[t['id']] = t
    return texts


AUTHOR_TEXTS_DIR = 'data/reading-author-texts'
AUTHOR_TEXTS = {}
AUTHOR_TEXT_KEYS = ('intro', 'biografia', 'por_donde_empezar', 'obras', 'faq', 'fuentes')


def load_author_texts(root):
    """Fichas de autor validadas por scripts/reading-author-texts.py, una por slug. Un fichero roto se ignora con aviso
    y la ficha sigue con los datos de Wikidata y del catálogo."""
    texts = {}
    for path in sorted((root / AUTHOR_TEXTS_DIR).glob('*.json')):
        try:
            t = json.loads(path.read_text(encoding='utf-8'))
        except ValueError:
            t = None
        ok = isinstance(t, dict) and t.get('slug') == path.stem and t.get('identificado') is True and all(t.get(k) for k in AUTHOR_TEXT_KEYS) \
            and all(isinstance(t.get(k, []), list) for k in ('por_donde_empezar', 'obras', 'sagas', 'parecidos', 'faq', 'fuentes')) \
            and all(isinstance(x, dict) and re.fullmatch(r'https://[^\s<>"]+', str(x.get('url', ''))) for x in t['fuentes'])
        if not ok:
            print(f'::warning::{path.name}: texto de autor ignorado (slug distinto, incompleto o con fuentes no https)', flush=True)
            continue
        texts[t['slug']] = t
    return texts


def own_block_html(x, live):
    """Un módulo; las comparaciones enlazan cada título a su ficha y desaparecen si un afín ya no está publicado.

    Las posiciones se resuelven sobre el texto ORIGINAL, no sobre el texto ya etiquetado: un reemplazo en cadena
    (text.replace tras otro text.replace) anidaba un <a> dentro de otro cuando un título era substring de otro
    (p. ej. «Japón 2027-2028» dentro de «Explora Japón 2027-2028 (Guías Explora Lonely Planet)»), lo que test-dom-integrity.py
    rechaza como anidamiento interactivo inválido.
    """
    text = esc(x['texto'])
    spans = []  # (inicio, fin, i) resueltos sobre el texto original, sin solaparse entre sí
    for i in x.get('enlaces', []):
        if i not in live:
            return ''
        title = esc(live[i]['titulo'])
        start = 0
        while True:
            pos = text.find(title, start)
            if pos == -1:
                break
            end = pos + len(title)
            if any(pos < e and s < end for s, e, _ in spans):
                start = pos + 1
                continue
            spans.append((pos, end, i))
            break
    out, cursor = [], 0
    for start, end, i in sorted(spans):
        out.append(text[cursor:start])
        out.append('<a href="' + url(live[i]) + '">' + text[start:end] + '</a>')
        cursor = end
    out.append(text[cursor:])
    return '<h3>' + MODULE_TITLES[x['modulo']] + '</h3><p>' + ''.join(out) + '</p>'


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
    # Si ni así cabe (obras colectivas, títulos bilingües «… / …»), la autoría pasa a «primer autor y otros» y el
    # título pierde la traducción y, en último caso, palabras del final. La publicación de textos se paró las noches
    # del 09 y 10/11 con 17 y 33 metas largas, y el número solo crecía con el catálogo.
    first = b['autores'][0] if b['autores'] else ''
    authors = [', '.join(b['autores'])] + ([first + ' y otros'] if len(b['autores']) > 1 else [])
    titles = short_titles(b['titulo'])
    plain = titles + [n.split(' / ')[0].strip() for n in titles if ' / ' in n]
    # Etapas: autoría completa, «y otros», título sin traducción y, solo al final, título recortado por palabras.
    stages = [(who, titles) for who in authors] + [(who, plain) for who in authors]
    stages += [(who, [clip_words(plain[-1], 160 - len(f", de {who}. Antes de elegirlo: para quién es."))]) for who in authors[-1:]]
    for who, names in stages:
        for parts in ((fmt, pages, age), (fmt, age), (age,), ()):
            facts = ', '.join(f for f in parts if f)
            for name in names:
                for n in (2, 1):
                    topics = ' y '.join(MODULE_TITLES[x['modulo']].lower() for x in t['bloques'][:n])
                    text = f"{name}, de {who}" + (': ' + facts if facts else '') + '. Antes de elegirlo: ' + topics + '.'
                    if len(text) <= 160:
                        return text
    return text


def clip_words(text, limit):
    """Recorta por palabra completa y marca el corte con «…»; sin cambios si ya cabe."""
    if len(text) <= limit:
        return text
    return text[:max(limit - 1, 1)].rsplit(' ', 1)[0].rstrip(' ,;:.-–—(') + '…' 




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


AUTHOR_STUB_MAX = 28


def author_stub(name):
    """Forma corta de un autor que no cabe entera en el título SEO: sus primeras palabras y «…». Cabe en 75 caracteres con
    un título de al menos 12; los autores que ya caben no se abrevian."""
    if len(name) <= AUTHOR_STUB_MAX:
        return name
    return name[:AUTHOR_STUB_MAX].rsplit(' ', 1)[0].rstrip(' -–—:.,') + '…'


def author_in_title(b, title):
    """El título nombra al primer autor, entero o en su forma corta."""
    return b['autores'][0] in title or author_stub(b['autores'][0]) in title


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
    tails = list(dict.fromkeys([' · ' + authors, lead, ' · ' + b['autores'][0]]))  # Sin «y otros» si no cabe.
    for tail in tails:
        if len(tail) > 54:
            continue  # Con una firma tan larga, el corte negativo devolvería el título entero.
        cut = b['titulo'][:74-len(tail)].rsplit(' ', 1)[0].rstrip(' -–—:.,')
        if len(cut) >= 12 and not any(t.startswith(cut.casefold()) for t in clash):
            return cut + '…' + tail
    # Firma institucional demasiado larga para cualquier cola (p. ej. «Grupo Andaluz de Trabajo en Endometriosis de la SAGO»):
    # se abrevia en vez de perder el autor, que es lo que se busca (la carga apartaba estos libros por «sin autor en el título»).
    stub = ' · ' + author_stub(b['autores'][0])
    cut = b['titulo'][:74-len(stub)].rsplit(' ', 1)[0].rstrip(' -–—:.,')
    if len(cut) >= 12 and not any(t.startswith(cut.casefold()) for t in clash):
        return cut + '…' + stub
    suffix = ' · ' + (b.get('isbn13') or hashlib.sha256(b['id'].encode()).hexdigest()[:8])
    # Con hermanos de título casi idéntico y firma larga, la forma corta del autor acompaña al ISBN: nunca queda sin autor.
    tail = next((t for t in [*tails, stub] if len(t) <= 31), '')
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


# Fichas de autoridad del autor (sameAs), en el orden en que se enseñan.
AUTHOR_ID_LABELS = {'web': 'Web oficial', 'wikipedia': 'Wikipedia', 'bne': 'Biblioteca Nacional de España', 'viaf': 'VIAF', 'isni': 'ISNI', 'goodreads': 'Goodreads'}


@fallo_general
def load_author_records(path):
    payload = json.loads(path.read_text(encoding='utf-8'))
    require(set(payload) == {'schema_version', 'autores'} and payload['schema_version'] == 1, 'Contrato de autores inválido')
    names, slugs = set(), set()
    for a in payload['autores']:
        required = {'slug', 'nombre', 'descripcion', 'fuentes', 'fecha_verificacion'}
        optional = {'biografia_breve', 'biografia_fuente_url', 'biografia_fecha_revision', 'biografia_fuente_nombre', 'biografia_ultimo_intento',
                    'nacimiento', 'fallecimiento', 'foto', 'wikidata', 'amazon_autor_id', 'identificadores'}
        required |= {'tipo'} if a.get('tipo') == 'bibliografico' else {'nacimiento'}
        require(required <= set(a) <= required | optional, 'Campos de autor inválidos')
        require(a['slug'] != 'pagina', 'Slug de autor reservado para la paginación del índice')
        for key in ('nacimiento', 'fallecimiento'):
            if a.get(key):
                require(isinstance(a[key], str) and AUTHOR_LIFE.fullmatch(a[key]), f'{key} de autor inválido (AAAA o AAAA-MM-DD)')
                if len(a[key]) > 4:
                    day(a[key], key)
        require(not (a.get('nacimiento') and a.get('fallecimiento')) or a['nacimiento'][:4] <= a['fallecimiento'][:4], 'Fallecimiento anterior al nacimiento')
        require(not a.get('wikidata') or re.fullmatch(r'Q[1-9]\d*', a['wikidata']), 'Wikidata de autor inválido')
        require(not a.get('amazon_autor_id') or re.fullmatch(r'[A-Z0-9]{10}', a['amazon_autor_id']), 'ID de autor de Amazon inválido')
        ids = a.get('identificadores', {})
        require(isinstance(ids, dict) and set(ids) <= set(AUTHOR_ID_LABELS) and all(isinstance(v, str) and https(v) for v in ids.values()), 'Identificadores de autor inválidos')
        if a.get('foto'):
            # La foto vive en el almacén externo de portadas como ruta lógica: el despliegue la reescribe y la CSP la admite.
            foto = a['foto']
            require(isinstance(foto, dict) and {'url', 'ancho', 'alto', 'autor', 'licencia', 'fuente_url'} <= set(foto) <= {'url', 'ancho', 'alto', 'autor', 'licencia', 'licencia_url', 'fuente_url'}
                    and isinstance(foto['url'], str) and foto['url'].startswith(cover_store.LOGICAL_PREFIX)
                    and cover_store.NAME.fullmatch(foto['url'][len(cover_store.LOGICAL_PREFIX):]) and https(foto['fuente_url']) and (not foto.get('licencia_url') or https(foto['licencia_url']))
                    and all(type(foto[k]) is int and 16 <= foto[k] <= 4000 for k in ('ancho', 'alto')) and foto['autor'] and foto['licencia'], 'Foto de autor inválida')
        if a.get('biografia_breve'):
            require(30 <= len(a['biografia_breve']) <= 700 and https(a.get('biografia_fuente_url')), 'Biografía sin fuente o inválida')
            day(a.get('biografia_fecha_revision'), 'biografía revisada')
        require(SLUG.fullmatch(a['slug']) and a['slug'] not in slugs and a['nombre'] not in names, 'Autor duplicado o slug inválido')
        require(isinstance(a['descripcion'], str) and len(a['descripcion']) >= 60, 'Autor sin descripción')
        day(a['fecha_verificacion'], 'autor verificado')
        require(a['fuentes'] and all(set(s) == {'titulo', 'url'} and s['titulo'] and https(s['url']) for s in a['fuentes']), 'Autor sin fuentes')
        names.add(a['nombre']); slugs.add(a['slug'])
    return payload['autores']


PUBLISHER_CACHE = {}


def publisher_records(root=ROOT):
    """Sellos que aparecen en el catálogo pero no en el directorio de editoriales que aceptan manuscritos.
    Se leen y validan una vez por versión del archivo: la cuarentena de la ingesta valida libro a libro."""
    path = root / 'data/reading-publishers.json'
    if not path.exists():
        return []
    stat = path.stat()
    key = (str(path), stat.st_mtime_ns, stat.st_size)
    if key not in PUBLISHER_CACHE:
        PUBLISHER_CACHE.clear()
        PUBLISHER_CACHE[key] = load_publisher_records(path)
    return PUBLISHER_CACHE[key]


@fallo_general
def load_publisher_records(path):
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
    """Formatos que se enlazan: los que tienen precio de la API y el de la propia edición (su ISBN existe aunque aún no
    haya precio). Un formato hermano sin precio no se enlaza ni cuenta en los filtros: el 08/11, de 39 «Ver precio», 8
    estaban agotados en Amazon y varios eran de otra edición (la ficha de una edición especial agrupa la normal). Su
    casilla queda como búsqueda en esa sección de Amazon hasta que el barrido le encuentre precio."""
    own = b.get('formato_edicion')
    return [o for o in b.get('formatos_compra', []) if o.get('precio_centimos') or o.get('formato') == own]


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
NEW_TAB='<span class="sr-only"> (otra pestaña)</span>'  # sr-only lives in v1-base.css, loaded on every page


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
            cells.append(f'<li><a class="catalogue-format{" is-primary" if f == main else ""}" data-purchase-format="{f}" href="{esc(amazon_es(o["url"]))}" target="_blank" rel="sponsored nofollow noopener noreferrer"><span>{FORMATS[f]}</span> <strong>{price}{badge}</strong><span class="sr-only">{said} en Amazon (otra pestaña)</span></a></li>')
        elif (search := amazon_format_search(b, f)):
            cells.append(f'<li><a class="catalogue-format is-missing" data-missing-format="{f}" href="{esc(amazon_es(search))}" target="_blank" rel="sponsored nofollow noopener noreferrer"><span>{FORMATS[f]}</span> <strong>Buscar</strong><span class="sr-only"> en Amazon, sin precio comprobado (otra pestaña)</span></a></li>')
        else:
            cells.append(f'<li><span class="catalogue-format is-missing" data-missing-format="{f}"><span>{FORMATS[f]}</span> <strong aria-hidden="true">—</strong><span class="sr-only">: sin precio comprobado en Amazon</span></span></li>')
    if compact:
        # The enclosing region already names Amazon; retain format, price and new-tab hint.
        cells = [cell.replace(' en Amazon (otra pestaña)', ' (otra pestaña)').replace(' en Amazon, sin precio comprobado (otra pestaña)', ', sin precio comprobado (otra pestaña)').replace(' comprobado en Amazon</span>', ' comprobado</span>') for cell in cells]
    heading = '' if compact else '<h2>Formatos y precios en Amazon</h2>'
    return f'<section class="catalogue-formats{" catalogue-formats--card" if compact else ""}" aria-label="Formatos y precios en Amazon">{heading}<ul>' + ''.join(cells) + '</ul></section>'


MONTHS_ES = ('', 'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')


ICS_PATH = 'recomendaciones/proximos-lanzamientos.ics'
DEALS_PATH = 'recomendaciones/ofertas.json'
DEALS_SEASON = 'ofertas-amazon'  # antigua opción de «Temporada»; las ofertas se filtran con «Ofertas» (no debe volver)


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


HOY = None  # día del despliegue (--hoy): si se da, manda sobre la fecha de los datos (D1, R4-4)


def dia_del_despliegue(hoy=None, entorno=None):
    """`--hoy` o, si no, CATALOGO_HOY (el despliegue la fija con la fecha de Madrid para toda la cadena de
    materializar); None si no hay ninguna. Una fecha mal escrita aborta (ValueError) en vez de publicar otro día."""
    dia = hoy or site_clock.dia_fijado(entorno or {})
    return dia.isoformat() if dia else None


def data_anchor(books):
    """Fecha de referencia: el día del despliegue (`--hoy`) o, sin él, la derivada de los datos (no del reloj).
    Así el portal cambia de día aunque una noche no haya carga, y la salida sigue siendo determinista."""
    if HOY:
        return HOY
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


LLMS_FACTS_END = 480  # con el mínimo de «Para quién es» (40) y de sinopsis (60) la línea sigue bajo 700


def llms_authors(names, limit=250):
    """Todos los autores mientras quepan; una antología de 40 firmas se resume en «…, y N más»."""
    shown = []
    for name in names:
        if shown and len(', '.join(shown + [name])) > limit:
            break
        shown.append(name)
    rest = len(names) - len(shown)
    return ', '.join(shown) + (f' y {rest} más' if rest else '')


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
    index = category_index(data)
    for b in sorted(books, key=lambda b: (b['titulo'].casefold(), b['id'])):
        cats = categories(data, b, index)
        # Corchetes del título escapados: «Harry Potter [edición…]» rompía el enlace Markdown (2026-11-06).
        link_text = clip(b['titulo'], 160).replace('[', '\\[').replace(']', '\\]')
        head = f"- [{link_text}]({SITE}{url(b)}): "
        # Los datos de la edición van siempre enteros; los autores ceden sitio («y N más») y género, temas y edad
        # entran solo si caben. Lote 42436110753: una antología desbordó la línea (1224) y se revirtió la ingesta.
        edition = [b.get('editorial'), b.get('anio_publicacion') and str(b['anio_publicacion']), formats.get(b.get('formato_edicion')),
                   b.get('numero_paginas') and f"{b['numero_paginas']} páginas", b.get('isbn13') and 'ISBN ' + b['isbn13']]
        edition = '. '.join(f.rstrip('.') for f in edition if f)
        facts = llms_authors(b['autores'], max(40, LLMS_FACTS_END - len(head) - len(edition) - 4)) + '. ' + edition
        age = b.get('edad_recomendada') or ', '.join(c['nombre'] for c in cats if c['tipo'] == 'edad')
        extras = [label + ': ' + ', '.join(names) for label, tipo in (('Género', 'genero'),)
                  if (names := [c['nombre'] for c in cats if c['tipo'] == tipo])] + [age and 'Edad: ' + age]
        for extra in extras:
            if extra and len(head) + len(facts) + len(extra) + 2 <= LLMS_FACTS_END:
                facts += '. ' + extra.rstrip('.')
        head += facts + '. '
        who = own_summary(b)
        # El «Para quién es» cede espacio para que la sinopsis conserve al menos 60 caracteres sin pasar de 690.
        label = 'Sinopsis de la editorial: ' if b.get('sinopsis_breve') else 'Descripción: '
        who = who and clip(who, max(40, 690 - 60 - len(head) - len('Para quién es: . ' + label)))
        head += (who and 'Para quién es: ' + who.rstrip('.') + '. ') + label
        # Cada línea cabe en 700 caracteres: la sinopsis de la editorial se queda con el espacio que deja lo propio.
        text = clip(synopsis(b), max(60, min(300, 690 - len(head))))
        lines.append(head + text.rstrip('.') + ('' if text.endswith('…') else '.'))
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


def facet_counts(data, books, anchor):
    """Recuentos de la vista por defecto (ya publicados, sin filtros) para cada casilla, con la misma lógica que las
    fichas (grupo, categorías públicas y formatos). El catálogo completo solo se descarga al primer toque (rendimiento),
    y hasta entonces las casillas salían sin número: «Novela» sin «(411)» (David, 13/11). El JS los recalcula después."""
    counts = {}
    index = category_index(data)
    for b in books:
        lower = b.get('fecha_publicacion') or ''
        if not lower and (month := b.get('fecha_publicacion_parcial')):
            lower = month + '-01'
        if not lower and b.get('anio_publicacion'):
            lower = f"{b['anio_publicacion']}-01-01"
        if lower and anchor and lower > anchor:
            continue
        cats = categories(data, b, index)
        keys = [('grupo', book_group(cats))] + [(c['tipo'], c['id']) for c in facet_categories(cats)]
        keys += [('formato', f) for f in {o['formato'] for o in purchase_formats(b)} | ({b['formato_edicion']} if b.get('formato_edicion') else set())]
        for key in keys:
            counts[key] = counts.get(key, 0) + 1
    return counts


def facet_group(key, label, options, opened=False, counts=None):
    def badge(v):
        return f'({counts.get((key, v), 0)})' if counts is not None else ''
    boxes = ''.join(f'<label class="catalogue-check"><input type="checkbox" id="{key}={esc(v)}" name="{key}" value="{esc(v)}" data-facet="{key}"><span>{esc(t)}</span><small data-facet-count>{badge(v)}</small></label>' for v, t in options)
    return f'<details class="catalogue-facet" data-facet-group="{key}"' + (' open' if opened else '') + f'><summary>{esc(label)} <small data-facet-selected></small></summary><div class="catalogue-facet__options">{boxes}</div></details>'


def render_filters(data, type_options, counts=None):
    def select(key, label, options, extra=''):
        return f'<label>{label}<select name="{key}" data-filter="{key}" {extra}>' + ''.join(f'<option value="{esc(v)}">{esc(t)}</option>' for v, t in options) + '</select></label>'
    search = '<label class="catalogue-search">Buscar por título, autor o ISBN<input type="search" name="q" data-filter="q" maxlength="200" autocomplete="off" placeholder="¿Qué te apetece leer?"></label>'
    used = {r['categoria_id'] for r in data['libro_categorias']}
    facets = facet_group('grupo', 'Tipo de libro', type_options, True, counts)
    for kind, label in TYPES.items():
        if kind not in PUBLIC_TYPES:
            continue
        # Una categoría sin libros solo añadiría una casilla muerta al filtro.
        choices = sorted((c for c in data['categorias'] if c['tipo'] == kind and c['activa'] and c['id'] in used), key=age_order if kind == 'edad' else lambda c: (c['orden'], c['id']))
        if not choices:
            continue
        options = [(c['id'], c['nombre']) for c in choices] + ([(NO_VALUE[kind]['id'], NO_VALUE[kind]['nombre'])] if kind in NO_VALUE else [])
        # Las ofertas de Amazon se filtran con «Ofertas» (descuento vigente), no como temporada.
        facets += facet_group(kind, label, options, counts=counts)
    facets += facet_group('formato', 'Formato', list(FORMATS.items()), counts=counts)
    price_format = '<label class="catalogue-price-range__format">Formato<select name="precio_formato" data-filter="precio_formato">' + '<option value="">Cualquier formato</option>' + ''.join(f'<option value="{k}">{esc(FORMATS[k])}</option>' for k in BOX_ORDER) + '</select></label>'
    facets += '<div class="catalogue-facet catalogue-price-range"><p class="catalogue-facet__title">Precio (€)</p><p class="catalogue-price-range__hint">Elige el formato para no mezclar precios de Kindle y de papel.</p>' + price_format + '<div class="catalogue-price-range__fields">' + ''.join(f'<label>{t}<input type="number" min="0" max="100000" step="0.01" inputmode="decimal" name="{k}" data-filter="{k}" placeholder="{ph}"></label>' for k, t, ph in (('precio_min', 'Desde', '0'), ('precio_max', 'Hasta', '100'))) + '</div></div>'
    # Orden de las preguntas (David, 09/11): qué libro (tipo, género, edad), cómo leerlo (formato, precio de ese
    # formato, extensión) y cuándo salió y si está de oferta. Sin «Novedades»: «Publicado desde» ya lo cubre.
    controls = select('paginas', 'Extensión', [('', 'Cualquier extensión'), ('breve', 'Menos de 200 páginas'), ('media', 'De 200 a 399 páginas'), ('larga', 'De 400 a 599 páginas'), ('muy-larga', '600 páginas o más')])
    for key,label in [('desde', 'Publicado desde'), ('hasta', 'Publicado hasta')]:
        controls += f'<label>{label}<input type="date" name="{key}" data-filter="{key}" min="1000-01-01" max="2100-12-31"></label>'
    controls += select('descuento', 'Ofertas', [('', 'Todos los precios'), ('1', 'Con descuento o bajada de precio'), ('5', '5 % o más'), ('10', '10 % o más'), ('25', '25 % o más'), ('50', '50 % o más')], 'data-market-control="offers" disabled')
    # En móvil (≤900 px) solo la búsqueda queda a la vista; el resto de filtros se pliega tras
    # «Filtros» para que los libros aparezcan en la primera pantalla. En escritorio el panel
    # siempre está abierto y el botón no se muestra (lo decide el CSS: sin salto al cargar).
    toggle = '<button type="button" class="catalogue-refine-toggle" aria-expanded="false" aria-controls="catalogue-refine" data-catalogue-refine-toggle>Filtros <span class="catalogue-refine-count" data-catalogue-refine-count></span><span aria-hidden="true">＋</span></button>'
    return ('<aside class="catalogue-sidebar"><form class="catalogue-filters" data-catalogue-filters><fieldset disabled><legend>Encuentra tu próxima lectura</legend>' + search + toggle
            + '<div class="catalogue-refine" id="catalogue-refine" data-catalogue-refine><div class="catalogue-facets">' + facets + '</div><div class="catalogue-filter-grid">' + controls + '</div>'
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


# «Nutrición y bienestar» sale de palabras clave editoriales como «salud», que también aparecen en cuentos
# infantiles y novelas: sin «cocina», no saca de su tipo a un libro de ficción, infantil o poesía.
WEAK_COOKING = 'nutricion-y-bienestar'
OVER_WEAK_COOKING = ('novela', 'infantil', 'poesia')


def book_group(cats):
    ids = {c['id'] for c in cats}
    if WEAK_COOKING in ids and 'cocina' not in ids:
        other = next((gid for gid, _label, members in BOOK_GROUPS if gid != 'cocina' and ids & members), None)
        if other in OVER_WEAK_COOKING:
            return other
    # Sin cajón «Otros»: lo que no encaja en ningún tipo es no ficción (crónica, actualidad, religión…).
    return next((gid for gid, _label, members in BOOK_GROUPS if ids & members), 'ensayo')


def group_options(groups):
    display_order = ('novela', 'poesia', 'infantil', 'cocina', 'crecimiento', 'ensayo', 'viajes')
    return sorted(((gid, label) for gid, label, _m in BOOK_GROUPS if gid in groups), key=lambda g: display_order.index(g[0]))


CATALOGUE_PAGE_SIZE = 96


def catalogue_page_url(number, base='/recomendaciones/'):
    return base if number == 1 else f'{base}pagina/{number}/'


def pager_window(number, pages):
    """Páginas visibles de un paginador (patrón GOV.UK): primera, última y vecinas de la actual; None = hueco «…»."""
    out, last = [], 0
    for page in sorted({1, pages, *range(max(1, number - 1), min(pages, number + 1) + 1)}):
        if page - last > 1:
            out.append(None)
        out.append(page)
        last = page
    return out


def catalogue_pager(number, pages, base='/recomendaciones/'):
    """Paginador estático: Anterior · 1 … n-1 [n] n+1 … N · Siguiente, y caja «Ir a la página» (se activa con JS).
    Sin JS se recorre todo con Anterior/Siguiente; el JS sabe cuántas páginas hay por data-catalogue-page-count."""
    if pages <= 1:
        return ''
    def link(page, text, extra=''):
        return f'<a href="{catalogue_page_url(page, base)}" target="_self" data-catalogue-page{extra}>{text}</a>'
    numbers = ''.join('<span class="catalogue-pagination__gap" aria-hidden="true">…</span>' if page is None else
                      f'<span aria-current="page">{page}</span>' if page == number else
                      link(page, str(page), f' aria-label="Página {page}"')
                      for page in pager_window(number, pages))
    prev = link(number - 1, '← Anterior', ' rel="prev"') if number > 1 else ''
    nxt = link(number + 1, 'Siguiente →', ' rel="next"') if number < pages else ''
    jump = (f'<form class="catalogue-pagination__jump" data-catalogue-jump hidden><label>Ir a la página '
            f'<input type="number" name="pagina" min="1" max="{pages}" value="{number}" inputmode="numeric" required></label> '
            '<button type="submit">Ir</button></form>')
    return (f'<nav class="catalogue-pagination catalogue-static-pagination" data-catalogue-static-pagination data-catalogue-page-count="{pages}" aria-label="Páginas del catálogo">'
            + prev + '<span class="catalogue-pagination__pages">' + numbers + '</span>' + nxt
            + f'<span class="catalogue-pagination__position">Página {number} de {pages}</span>' + jump + '</nav>')


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
    index = category_index(data)
    for book in books:
        group = book_group(categories(data, book, index))
        groups[group] = groups.get(group, 0) + 1
    for i,b in enumerate(visible_books):
        cats = categories(data,b,index)
        group = book_group(cats)
        formats = ' '.join(sorted(set([o['formato'] for o in purchase_formats(b)] + ([b['formato_edicion']] if b.get('formato_edicion') else []))))
        published = b.get('fecha_publicacion', '')
        year = '' if published or b.get('fecha_publicacion_parcial') else b.get('anio_publicacion', '')
        attrs = f'data-catalogue-book data-group="{group}" data-book-id="{esc(b["id"])}" data-categories="{esc(" ".join(c["id"] for c in facet_categories(cats)))}" data-title="{esc(b["titulo"])}" data-author="{esc(", ".join(b["autores"]))}" data-isbn="{esc(b.get("isbn13", ""))}" data-formats="{formats}" data-published="{esc(published)}" data-published-month="{esc(b.get("fecha_publicacion_parcial", ""))}" data-year="{esc(year)}" data-pages="{esc(b.get("numero_paginas", ""))}" data-format-prices="{format_prices(b)}" data-format-discounts="{format_discounts(b, anchor)}"'
        # Missing optional values have the same runtime meaning as empty ones.
        attrs = re.sub(r' data-(?:isbn|published|published-month|year|pages|format-prices|format-discounts)=""', '', attrs)
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
        cards.append(f'<li class="catalogue-card" {attrs}><a class="catalogue-card__cover" {cover_link}>{image(b,i>1)}</a><div><p class="eyebrow catalogue-when">{release_line(b)}</p>{tags(cats, compact=True)}<h3><a {title_link}>{esc(card_title(b))}</a></h3><p class="catalogue-author">{author_links(b, compact=True)}</p>{byline(b)}<p class="catalogue-card__description">{esc(card_synopsis(b, anchor=anchor))}</p>{format_box(b, compact=True, anchor=anchor)}<a class="text-action catalogue-card__ficha" href="{url(b)}" target="_blank" rel="noopener noreferrer" aria-label="Ver ficha de {esc(b["titulo"])} (se abre en otra pestaña)">Ver ficha</a>' + affiliate_cta + '</div></li>')
    sort = '<label>Ordenar por<select name="orden" data-filter="orden" form="catalogue-search-form" disabled><option value="editorial">Publicación · más reciente primero</option><option value="fecha_asc">Publicación · más antigua primero</option><option value="paginas_asc">Páginas · menor a mayor</option><option value="paginas_desc">Páginas · mayor a menor</option>' + ''.join(f'<option value="precio_{k}">{esc(FORMATS[k])} · del más barato al más caro</option>' for k in BOX_ORDER) + '<option value="ventas" data-sort-market="sales_ranks" disabled hidden>Amazon.es · más vendidos</option></select></label>'
    # Lo primero que se ve son los libros ya publicados (los más recientes arriba); los próximos lanzamientos van aparte.
    show = '<label>Mostrar<select name="estado" data-filter="estado" form="catalogue-search-form" disabled><option value="">Ya publicados</option><option value="proximos" id="estado=proximos">Próximos lanzamientos</option><option value="todos">Todos</option></select></label>'
    upcoming = ('<div class="catalogue-shortcuts"><a class="catalogue-upcoming-link" href="#estado=proximos" data-catalogue-upcoming>Ver los próximos lanzamientos →</a>'
                + community_cta() + '</div>')
    filters = render_filters(data, group_options(groups), facet_counts(data, books, anchor)).replace('<form class=', '<form id="catalogue-search-form" class=',1)
    if page_number > 1:
        filters = show = sort = upcoming = ''
    static_count = f'Mostrando {offset + 1}–{offset + len(visible_books)} de {len(books)} libros' if books else '0 libros'
    catalogue = '<section class="catalogue-section" id="catalogo" aria-label="Buscar libros recomendados"><div class="' + ('catalogue-layout' if page_number == 1 else 'catalogue-static-layout') + '">' + filters + '<div class="catalogue-main"><div class="catalogue-results-head"><h2>El catálogo</h2><div class="catalogue-results-controls">' + show + sort + '</div>' + upcoming + '<div class="catalogue-count-line"><p role="status" aria-live="polite" data-catalogue-count>' + static_count + '</p>' + ('<button type="button" class="catalogue-clear-link" data-catalogue-clear hidden>Eliminar filtros</button>' if filters else '') + '</div>' + ('<div class="catalogue-active" data-catalogue-active hidden></div>' if filters else '') + '</div><ul class="catalogue-grid">' + ''.join(cards) + '</ul>' + catalogue_pager(page_number, page_count) + '<div class="catalogue-empty" data-catalogue-empty' + (' hidden' if books else '') + '><h2>' + ('No hay libros con estos filtros' if books else 'Estamos preparando la selección') + '</h2><p>Prueba con otros filtros o restablece la búsqueda.</p><a class="text-action" href="/cuaderno/#lecturas">Explorar las guías de lectura</a></div><noscript><p>Puedes consultar todas las fichas recorriendo las páginas del catálogo. Los filtros requieren JavaScript.</p></noscript></div></div></section>'
    if page_number > 1:
        catalogue = '<p class="catalogue-static-note">Estás en el listado completo, sin filtros. <a class="text-action" href="/recomendaciones/#catalogo" target="_self">Filtrar, buscar y ordenar todo el catálogo →</a></p>' + catalogue
    quiz='<details class="catalogue-quiz"><summary>¿Qué te apetece leer? Haz el test y encuentra tu próximo libro</summary><div class="catalogue-quiz__panel"><p>Puedes recorrer las páginas del catálogo para consultar todas las fichas.</p></div></details>' if books and page_number == 1 else ''
    page=template.replace('{{catalogue}}',quiz+catalogue)
    if page_number == 1:
        page = page.replace('<link rel="stylesheet" href="/assets/reading-catalogue.css?v=36">', '<link rel="stylesheet" href="/assets/reading-catalogue.css?v=36"><link rel="stylesheet" href="/assets/v1-catalogue-community.css?v=2">', 1)
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


_RELATED_POOL = {}


def related_pool(data):
    """Rasgos de los libros publicados (categorías activas, público, edad) y cuántos tiene cada categoría.

    Con el índice de main() se calcula una vez por índice: recalculado por ficha, el coste crecía con el cuadrado
    del catálogo y medio (55 s con 1.841 libros, ~30 min con 10.000). Sin índice (tests) se calcula al vuelo.
    """
    indexed = CATEGORY_INDEX is not None and CATEGORY_INDEX[0] is data
    if indexed and _RELATED_POOL.get('index') is CATEGORY_INDEX:
        return _RELATED_POOL
    books = [x for x in data['libros'] if x['estado'] == 'publicado']
    index = category_index(data)
    cats = {x['id']: {c['id'] for c in categories(data, x, index)} for x in books}
    counts = {}
    for ids in cats.values():
        for c in ids:
            counts[c] = counts.get(c, 0) + 1
    pool = {'books': books, 'cats': cats, 'counts': counts,
            'publics': {i: audience(ids) for i, ids in cats.items()}, 'ages': {x['id']: min_age(x) for x in books}}
    if indexed:
        _RELATED_POOL.clear()
        _RELATED_POOL.update(pool, index=CATEGORY_INDEX)
    return pool


def related_books(data, book):
    # Cada categoría compartida pesa por lo rara que es («Hockey» dice más que «Romance») y no se cruzan públicos.
    own={c['id'] for c in categories(data,book)}
    wanted={c['id'] for c in categories(data,book) if c['tipo'] in {'genero','tematica'}}
    pool=related_pool(data)
    inside=book['id'] in pool['cats']  # el propio libro no cuenta en el total ni en la rareza de sus categorías
    total=len(pool['books'])-inside+1
    df={c:1+pool['counts'].get(c,0)-(inside and c in own) for c in wanted}
    public,age=audience(own),min_age(book)
    authors=set(book['autores'])
    ranked=[]
    for candidate in pool['books']:
        if candidate['id']==book['id']:
            continue
        shared=wanted & pool['cats'][candidate['id']]
        same_author=bool(authors.intersection(candidate['autores']))
        if not shared and not same_author:
            continue
        other,other_age=pool['publics'][candidate['id']],pool['ages'][candidate['id']]
        if not same_author and ((public and other and public!=other) or (age is not None and other_age is not None and abs(age-other_age)>4)):
            continue
        # Orden fijo (no depende del hash) y redondeo a 9 decimales: empates reales que math.log resolvía por el
        # último bit distinto en Windows y en Linux cambiaban los relacionados entre local y CI (PR #1227).
        ranked.append((same_author,round(sum(math.log(total/df[c]) for c in sorted(shared)),9),candidate))
    ranked.sort(key=lambda row:(-row[0],-row[1],row[2]['titulo'].casefold(),row[2]['id']))
    if not ranked:
        return ''
    return '<section class="catalogue-related" aria-labelledby="related-books"><h2 id="related-books">También te puede interesar</h2><ul>'+''.join('<li><a class="catalogue-related__cover" href="'+url(candidate)+'" tabindex="-1" aria-hidden="true">'+image(candidate,True,'120px','catalogue-related__image','')+'</a><a href="'+url(candidate)+'">'+esc(candidate['titulo'])+'</a><p>'+esc(', '.join(candidate['autores']))+'</p></li>' for _,_,candidate in ranked[:6])+'</ul></section>'


def render_detail_page(template,main,canonical,title,description,schema,b=None):
    if len(title) > 75:
        title = title[:63].rsplit(' ', 1)[0] + ' · ' + hashlib.sha256(canonical.encode()).hexdigest()[:8]
    page=template.replace('{{catalogue}}','')
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


def author_genres(data, selected):
    """Géneros del autor por número de libros (los temas no cuentan como «escribe»)."""
    counted = {}
    for b in selected:
        for c in public(categories(data, b)):
            if c['tipo'] == 'genero':
                counted.setdefault(c['id'], [c, 0])[1] += 1
    return [c for c, _ in sorted(counted.values(), key=lambda t: (-t[1], t[0]['nombre']))]


def _on_date(label):
    """«en 1999» si solo hay año; «el 3 de mayo de 1999» si hay día."""
    return ('en ' if len(label) == 4 else 'el ') + label


def author_faq(a, selected, genres, anchor):
    """Preguntas con respuesta en los propios datos: lo que se busca de un autor y lo que un buscador o una IA puede citar."""
    name, out = a['nombre'], []
    released = [b for b in selected if (b.get('fecha_publicacion') or '') <= anchor]
    upcoming = sorted((b for b in selected if (b.get('fecha_publicacion') or '') > anchor), key=lambda b: b['fecha_publicacion'])
    if upcoming:
        b = upcoming[0]
        question = f'¿Hay nuevas ediciones de {name}?' if a.get('fallecimiento') else f'¿Qué libros de {name} se publican próximamente?'
        out.append((question, f'La próxima edición en España es «{b["titulo"]}», con salida prevista ' + _on_date(life_date_label(b['fecha_publicacion'])) + (f' en {b["editorial"].rstrip(".")}' if b.get('editorial') else '') + '.'))
    if released:
        b = released[0]
        when = publication_date_label(b)
        out.append((f'¿Cuál es el último libro de {name} publicado en España?', f'La edición más reciente es «{b["titulo"]}»' + (', publicada ' + _on_date(when) if when else '') + (f' por {b["editorial"].rstrip(".")}' if b.get('editorial') else '') + '.'))
    if a.get('nacimiento'):
        answer = _on_date(life_date_label(a['nacimiento']))
        if a.get('fallecimiento'):
            answer += '; falleció ' + _on_date(life_date_label(a['fallecimiento']))
        out.append((f'¿Cuándo nació {name}?', answer[0].upper() + answer[1:] + '.'))
    if genres:
        names = [g['nombre'].lower() for g in genres[:3]]
        out.append((f'¿Qué tipo de libros escribe {name}?', 'En este catálogo, sobre todo ' + (', '.join(names[:-1]) + ' y ' + names[-1] if len(names) > 1 else names[0]) + '.'))
    titles = ', '.join('«' + b['titulo'] + '»' for b in selected[:3])
    out.append((f'¿Dónde comprar los libros de {name}?', 'En Amazon.es: cada libro de esta página enlaza a su ficha de compra' + (f' ({titles}' + (' y más)' if len(selected) > 3 else ')') if titles else '') + ', y el botón «Sus libros en Amazon» abre la página del autor con todas sus ediciones.'))
    return out


EDITION_WORDS = re.compile(r'edicion|ed\.|bolsillo|ilustrad[ao]|coleccionista|limitad[ao]|especial|exclusiva|aniversario|rustica|tapa (?:dura|blanda)|cartone|estuche|best ?seller|booket|debolsillo|movie tie|serie de netflix')
EDITION_NOISE = re.compile(r'\([^)]*\)|\[[^\]]*\]|edicion (?:especial|limitada|de bolsillo|ilustrada|de coleccionista|exclusiva)[^.:]*|coleccion especial')
BRACKETS = re.compile(r'\(([^)]*)\)|\[([^\]]*)\]')


def _plain(title):
    return unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode().casefold()


def edition_key(title):
    """Misma obra en otra edición: título sin acentos, sin marcas de edición ni paréntesis («(Bolsillo)»,
    «(Biblioteca Agatha Christie)»). Los paréntesis que distinguen obras los separa `group_editions`."""
    t = EDITION_NOISE.sub(' ', _plain(title))
    return re.sub(r'[^a-z0-9]+', ' ', t).strip() or title


def edition_subject(title):
    """Lo que dicen los paréntesis que no son marca de edición: «(Química)» → «quimica»; «(Bolsillo)» → ''."""
    parts = [a or b for a, b in BRACKETS.findall(_plain(title))]
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', p).strip() for p in parts if not EDITION_WORDS.search(p)).strip()


def group_editions(selected):
    """[(principal, [otras ediciones])] en el orden de `selected`; la principal es la primera (la más reciente).
    Dentro de un mismo título, dos paréntesis distintos que no son de edición («(Química)», «(Hostelería y
    Turismo)») son obras distintas; uno solo (una colección, una serie) no separa nada."""
    groups = {}
    for b in selected:
        groups.setdefault(edition_key(b['titulo']), []).append(b)
    out = []
    for g in groups.values():
        subjects = {edition_subject(b['titulo']) for b in g} - {''}
        if len(subjects) < 2:
            out.append((g[0], g[1:]))
            continue
        parts = {}
        for b in g:  # el que no tiene paréntesis va con el primero que sí
            parts.setdefault(edition_subject(b['titulo']) or next(edition_subject(x['titulo']) for x in g if edition_subject(x['titulo'])), []).append(b)
        out.extend((p[0], p[1:]) for p in parts.values())
    first = {id(b): i for i, b in enumerate(selected)}
    return sorted(out, key=lambda pair: first[id(pair[0])])


def similar_authors(a, data, books, all_authors, limit=6):
    """Autores con los mismos géneros, pesando más los géneros poco frecuentes (un género que escriben
    todos no acerca a nadie) y normalizando por la amplitud de cada autor (coseno)."""
    by_author = {}
    for b in books:
        ids = {c['id'] for c in public(categories(data, b)) if c['tipo'] == 'genero'}
        for name in b['autores']:
            by_author.setdefault(name, set()).update(ids)
    mine = by_author.get(a['nombre'], set())
    if not mine:
        return []
    total = len(by_author)
    df = {}
    for ids in by_author.values():
        for g in ids:
            df[g] = df.get(g, 0) + 1
    weight = {g: math.log(total / df[g]) for g in df}
    # Sumas en orden fijo y puntuación redondeada: iterar un set de cadenas cambia con PYTHONHASHSEED y los
    # empates decididos por el último bit hacían que cada build reordenara «Si te gusta» (salida no determinista).
    norm_mine = math.sqrt(sum(weight[g] ** 2 for g in sorted(mine))) or 1
    ranked = []
    for other in all_authors:
        theirs = by_author.get(other['nombre'], set())
        shared = mine & theirs
        if other['nombre'] == a['nombre'] or other['nombre'] in COLLECTIVE_AUTHORS or not shared:
            continue
        score = round(sum(weight[g] ** 2 for g in sorted(shared)) / (norm_mine * (math.sqrt(sum(weight[g] ** 2 for g in sorted(theirs))) or 1)), 9)
        if score >= 0.35:
            ranked.append((-score, other['nombre'], other))
    return [o for _, _, o in sorted(ranked, key=lambda t: (t[0], t[1]))[:limit]]


def author_title_link(title, a, by_key):
    """Título de una obra: a su ficha si está en el catálogo; si no, a la búsqueda de Amazon con el autor y el tag."""
    b = by_key.get(edition_key(title))
    if b:
        return '<a href="' + url(b) + '">' + esc(title) + '</a>'
    search = amazon_es('https://www.amazon.es/s?k=' + quote(title + ' ' + a['nombre']) + '&i=stripbooks&tag=' + AUTHOR_TAG)
    return ('<a href="' + esc(search) + '" target="_blank" rel="sponsored nofollow noopener noreferrer">' + esc(title)
            + ' <span aria-hidden="true">↗</span>' + NEW_TAB + '</a>')


def author_text_sections(a, t, selected, related_by_name):
    """Secciones del texto propio: (índice de la página, antes de las ediciones, después de las ediciones)."""
    name = a['nombre']
    by_key = {}
    for b in selected:
        by_key.setdefault(edition_key(b['titulo']), b)
    link = lambda title: author_title_link(title, a, by_key)
    nav = [('empezar', 'Por dónde empezar'), ('obras', 'Libros en orden'), ('author-books', 'Ediciones en España')]
    before = ('<section aria-labelledby="empezar"><h2 id="empezar">Por dónde empezar a leer a ' + esc(name) + '</h2><ol class="catalogue-author-start">'
              + ''.join('<li><strong>' + link(x['titulo']) + '</strong><p>' + esc(x['motivo']) + '</p></li>' for x in t['por_donde_empezar']) + '</ol></section>')
    before += ('<section aria-labelledby="obras"><h2 id="obras">Libros de ' + esc(name) + ' en orden de publicación</h2>'
               '<p>Año de la primera edición original.</p><ol class="catalogue-author-works">'
               + ''.join('<li><span class="catalogue-author-works__year">' + str(w['anio']) + '</span> ' + link(w['titulo'])
                         + (' <span class="catalogue-author-works__original">(' + esc(w['titulo_original']) + ')</span>' if w.get('titulo_original') else '')
                         + (' · <span>' + esc(w['saga']) + '</span>' if w.get('saga') else '') + '</li>' for w in t['obras']) + '</ol></section>')
    if t.get('sagas'):
        nav.insert(2, ('sagas', 'Sagas'))
        before += ('<section aria-labelledby="sagas"><h2 id="sagas">Sagas de ' + esc(name) + ' y orden de lectura</h2>'
                   + ''.join('<h3>' + esc(s['nombre']) + '</h3><ol class="catalogue-author-works">' + ''.join('<li>' + link(x) + '</li>' for x in s['libros']) + '</ol>' for s in t['sagas'])
                   + '</section>')
    paragraphs = [p.strip() for p in t['biografia'].split('\n\n') if p.strip()]
    after = ('<section aria-labelledby="biografia"><h2 id="biografia">Biografía de ' + esc(name) + '</h2>' + ''.join('<p>' + esc(p) + '</p>' for p in paragraphs)
             + '<p class="catalogue-source">Fuentes: ' + ' · '.join(('<a href="' + esc(f['url']) + '" target="_blank" rel="noopener noreferrer">' + esc(f.get('titulo') or f['url']) + NEW_TAB + '</a>')
                                                                  if third_party_links.alive(f['url']) else esc(f.get('titulo') or f['url']) for f in t['fuentes'])
             + ('. Revisado ' + esc(_on_date(life_date_label(t['fecha_revision']))) if t.get('fecha_revision') else '') + '.</p></section>')
    nav.append(('biografia', 'Biografía'))
    similar = [(related_by_name[x['nombre']], x['motivo']) for x in t.get('parecidos', []) if x.get('nombre') in related_by_name]
    if similar:
        after += ('<section aria-labelledby="parecidos"><h2 id="parecidos">Si te gusta ' + esc(name) + '</h2><ul class="catalogue-author-start">'
                  + ''.join('<li><strong><a href="' + esc(author_url(o)) + '">' + esc(o['nombre']) + '</a></strong><p>' + esc(m) + '</p></li>' for o, m in similar) + '</ul></section>')
        nav.append(('parecidos', 'Autores parecidos'))
    nav.append(('author-faq', 'Preguntas frecuentes'))
    nav_html = ('<nav class="catalogue-author-toc" aria-label="En esta página"><p>En esta página:</p><ul>'
                + ''.join('<li><a href="#' + i + '">' + esc(label) + '</a></li>' for i, label in nav) + '</ul></nav>')
    return nav_html, before, after


def render_author(a,data,books,template,all_authors=(),anchor=None):
    selected=_newest_first([b for b in books if a['nombre'] in b['autores']])
    canonical=SITE+author_url(a)
    anchor=anchor or data_anchor(books)
    topics={c['id']:c for b in selected for c in categories(data,b) if c['tipo'] in {'genero','tematica'}}
    genres=author_genres(data,selected)
    publishers={b.get('editorial_slug') or b.get('editorial'):b for b in selected if b.get('editorial')}
    count=len(selected)
    person_like=a['nombre'] not in COLLECTIVE_AUTHORS
    summary=a['nombre']+': '+str(count)+(' libro disponible' if count==1 else ' libros disponibles')+' en este catálogo.'
    has_bio=bool(a.get('biografia_breve')) or a.get('tipo') != 'bibliografico'
    genre_names=[g['nombre'].lower() for g in genres[:2]]
    genre_line=(a['nombre']+(' escribió sobre todo ' if a.get('fallecimiento') else ' escribe sobre todo ')+' y '.join(genre_names)+'. Aquí están sus libros publicados en España y los próximos lanzamientos.') if genre_names and person_like else summary
    own=AUTHOR_TEXTS.get(a.get('slug')) if person_like else None
    bio=a.get('biografia_breve') or (a['descripcion'] if a.get('tipo') != 'bibliografico' else genre_line)
    if own:
        bio=own['intro']
        has_bio=True
    biography_source='' if own else ('<p class="catalogue-source"><a href="'+esc(a['biografia_fuente_url'])+'" target="_blank" rel="noopener noreferrer">Nota biográfica: '+esc(a.get('biografia_fuente_nombre') or 'editorial')+' ↗'+NEW_TAB+'</a>'+(' · Texto de Wikipedia con licencia CC BY-SA 4.0' if a.get('biografia_fuente_nombre') == 'Wikipedia' else '')+'</p>') if a.get('biografia_breve') else ''
    context='<section aria-labelledby="author-context"><h2 id="author-context">Su obra en este catálogo</h2><p>'+esc(summary)+'</p>'
    if topics:
        context+='<p>Géneros y temas presentes en sus libros:</p>'+tags(list(topics.values()))
    if publishers:
        context+='<p>Editoriales: '+', '.join(publisher_link(b) for b in publishers.values())+'.</p>'
    related=similar_authors(a,data,books,all_authors) if all_authors else []
    related_pool={o['nombre']:o for o in (similar_authors(a,data,books,all_authors,limit=8) if own and all_authors else [])}
    if related and not (own and any(x.get('nombre') in related_pool for x in own.get('parecidos',[]))):
        context+='<p>Autores de géneros parecidos: '+', '.join('<a href="'+esc(author_url(o))+'">'+esc(o['nombre'])+'</a>' for o in related)+'.</p>'
    context+='</section>'
    sponsored=' target="_blank" rel="sponsored nofollow noopener noreferrer"'
    items=''
    for b,others in group_editions(selected):
        metadata=' · '.join(str(v) for v in (publication_date_label(b),b.get('editorial'),(str(b['numero_paginas'])+' páginas') if b.get('numero_paginas') else '') if v)
        buy=amazon_destination(b)
        more=('<p>Otras ediciones: '+', '.join('<a href="'+url(o)+'">'+esc(' · '.join(str(v) for v in (o.get('editorial'),publication_date_label(o)) if v) or o['titulo'])+'</a>' for o in others)+'</p>') if others else ''
        items+=('<li><a href="'+url(b)+'">'+image(b,True)+'<span>'+esc(b['titulo'])+'</span></a><p>'+esc(metadata)+'</p>'+more
                +('<a class="catalogue-buy-link" href="'+esc(buy)+'"'+sponsored+' aria-label="Comprar «'+esc(b['titulo'])+'» en Amazon (otra pestaña)">'+amazon_action_label(b)+' <span aria-hidden="true">↗</span></a>' if buy else '')+'</li>')
    life=life_line(a) if person_like else ''
    chips=''.join('<li><a href="'+AUTHORS_BASE+'#genero='+esc(g['id'])+'">'+esc(g['nombre'])+'</a></li>' for g in genres[:3])
    cta=('<p class="catalogue-author-cta"><a class="catalogue-buy-link" href="'+esc(amazon_author_destination(a))+'"'+sponsored+'>Sus libros en Amazon <span aria-hidden="true">↗</span>'+NEW_TAB+'</a></p>') if person_like else ''
    photo=('<figure class="catalogue-author-figure">'+author_photo(a,False)+(('<figcaption>'+photo_credit(a)+'</figcaption>') if a.get('foto') else '')+'</figure>') if person_like else ''
    faq=author_faq(a,selected,genres,anchor) if person_like else []
    toc=before=after=''
    if own:
        toc,before,after=author_text_sections(a,own,selected,related_pool)
        # Las del catálogo que el texto propio ya responde (nacimiento, géneros) ceden su sitio a las suyas.
        faq=[(x['pregunta'],x['respuesta']) for x in own['faq']]+[(q,r) for q,r in faq if not q.startswith(('¿Cuándo nació','¿Qué tipo de libros escribe'))]
    shown_ids=[(AUTHOR_ID_LABELS[k],a['identificadores'][k]) for k in ('web','wikipedia') if k in a.get('identificadores',{}) and (k!='web' or third_party_links.alive(a['identificadores'][k]))]
    links=('<p class="catalogue-source">Más sobre '+esc(a['nombre'])+': '+' · '.join('<a href="'+esc(h)+'" target="_blank" rel="noopener noreferrer">'+esc(t)+NEW_TAB+'</a>' for t,h in shown_ids)+'</p>') if shown_ids else ''
    faq_html=('<section aria-labelledby="author-faq" class="catalogue-faq"><h2 id="author-faq">Preguntas frecuentes sobre '+esc(a['nombre'])+'</h2>'+''.join('<details class="catalogue-details"><summary>'+esc(q)+'</summary><p>'+esc(r)+'</p></details>' for q,r in faq)+'</section>') if faq else ''
    trail=[('Inicio','/'),('Libros recomendados','/recomendaciones/'),('Autores',AUTHORS_BASE),(a['nombre'],author_url(a))]
    crumbs=''.join('<li><a href="'+href+'">'+esc(label)+'</a></li>' for label,href in trail[:-1])+'<li aria-current="page">'+esc(a['nombre'])+'</li>'
    main=('<main id="contenido" tabindex="-1" class="v1-main reading-catalogue catalogue-author-page" data-family="recomendaciones"><nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol>'+crumbs+'</ol></nav>'
          '<header class="catalogue-author-hero'+(' catalogue-author-hero--photo' if photo else '')+'">'+photo+'<div><p class="eyebrow">Autores · Libros recomendados</p><h1>'+esc(a['nombre'])+'</h1>'
          +('<p class="catalogue-author-life">'+esc(life)+'</p>' if life else '')+('<ul class="catalogue-tags catalogue-tags--compact">'+chips+'</ul>' if chips else '')
          +'<p>'+esc(bio)+'</p>'+biography_source+links+cta+'</div></header>'+toc+before
          +'<section aria-labelledby="author-books"><h2 id="author-books">Libros de '+esc(a['nombre'])+'</h2><p>Ediciones ordenadas de la más reciente a la más antigua.</p><ul class="catalogue-author-books">'+items+'</ul></section>'
          +after+context+faq_html+'<div class="catalogue-end"><a class="text-action" href="'+AUTHORS_BASE+'">Ver todos los autores</a> <a class="text-action" href="/recomendaciones/">Explorar todos los libros</a></div></main>')
    person={'@type':'Person' if person_like else 'Organization','@id':canonical+'#person','name':a['nombre'],'url':canonical,'description':bio}
    if a.get('nacimiento'):
        person['birthDate']=a['nacimiento']
    if a.get('fallecimiento'):
        person['deathDate']=a['fallecimiento']
    if a.get('foto'):
        person['image']=SITE+a['foto']['url']
    if genres and person_like:
        person['knowsAbout']=[g['nombre'] for g in genres[:5]]
    same=[a['biografia_fuente_url']] if a.get('biografia_fuente_url') else ([source['url'] for source in a['fuentes']] if a.get('tipo') != 'bibliografico' else [])
    if a.get('wikidata'):
        same.append('https://www.wikidata.org/wiki/'+a['wikidata'])
    same+=[a['identificadores'][k] for k in AUTHOR_ID_LABELS if k in a.get('identificadores',{}) and (k!='web' or third_party_links.alive(a['identificadores'][k]))]
    if same:
        person['sameAs']=list(dict.fromkeys(same))
    modified=max(collection_modified(a,selected),(own or {}).get('fecha_revision',''))
    graph=[person,{'@type':'CollectionPage','@id':canonical,'url':canonical,'name':a['nombre']+' · Información y libros','dateModified':modified,'mainEntity':{'@id':canonical+'#person'},'hasPart':[{'@id':SITE+url(b)+'#book'} for b in selected]},_breadcrumb_schema(trail)]
    if own:
        graph.append({'@type':'ItemList','@id':canonical+'#obras','name':'Libros de '+a['nombre']+' en orden de publicación','itemListOrder':'https://schema.org/ItemListOrderAscending',
                      'itemListElement':[{'@type':'ListItem','position':i,'item':{'@type':'Book','name':w['titulo'],**({'datePublished':str(w['anio'])} if str(w['anio'])<=(anchor or data_anchor(books))[:4] else {}),'author':{'@id':canonical+'#person'}}} for i,w in enumerate(own['obras'],1)]})
    schema={'@context':'https://schema.org','@graph':graph}
    titles=', '.join(b['titulo'] for b in selected[:2])
    meta=a['nombre']+': '+(str(count)+(' libro recomendado' if count==1 else ' libros recomendados')+(' ('+titles+')' if titles else '')+', ' if count else '')+('biografía, géneros y editoriales.' if has_bio else 'géneros y editoriales.')
    if own:
        meta=a['nombre']+': por dónde empezar a leerle, sus libros en orden de publicación'+(', sagas' if own.get('sagas') else '')+' y biografía.'
    if len(meta)>160: meta=a['nombre']+': '+str(count)+(' libro recomendado' if count==1 else ' libros recomendados')+(', biografía, géneros y editoriales.' if has_bio else ', géneros y editoriales.')
    if own and a.get('fallecimiento'):
        title=a['nombre']+(' ('+a['nacimiento'][:4]+'–'+a['fallecimiento'][:4]+')' if a.get('nacimiento') else '')+': libros en orden y biografía'
    elif own:
        title=a['nombre']+': libros en orden'+(', sagas' if own.get('sagas') else '')+' y biografía'
    elif not person_like or count < 2:
        title='Libros de '+a['nombre']+': títulos y novedades'
    elif a.get('fallecimiento'):
        years=' ('+a['nacimiento'][:4]+'–'+a['fallecimiento'][:4]+')' if a.get('nacimiento') else ''
        title=a['nombre']+years+(': libros y biografía' if has_bio else ': libros y ediciones actuales')
    else:
        title=a['nombre']+(': libros, últimas novedades y biografía' if has_bio else ': libros y últimas novedades')
    if len(title)+len(' | David Porto Díaz')<=75:
        title+=' | David Porto Díaz'
    return render_detail_page(template,main,canonical,title,meta if a.get('tipo') != 'bibliografico' or count else bio,schema,selected[0] if selected else None)

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
    # Desempate por el nombre exacto: «Varios Autores»/«VARIOS AUTORES» empataban y el orden del set cambiaba la
    # página en cada ejecución (2026-11-06, --check fallaba en un sello distinto cada vez).
    authors = sorted({name for b in selected for name in b['autores']}, key=lambda n: (n.casefold(), n))
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


AUTHORS_ASSET_VERSION = '2'


AUTHOR_TAG = 'davidporto-21'
# Obras colectivas, no personas: tienen ficha, pero no tarjeta de autor (ni foto, ni página de autor en Amazon).
COLLECTIVE_AUTHORS = frozenset({'Varios autores', 'Anónimo'})


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()).strip('-')


AUTHORS_BASE = '/recomendaciones/autores/'
AUTHOR_LIFE = re.compile(r'\d{4}(?:-\d{2}-\d{2})?')
ROMAN = {15: 'XV', 16: 'XVI', 17: 'XVII', 18: 'XVIII', 19: 'XIX', 20: 'XX', 21: 'XXI'}


def life_date_label(value):
    """«10 de noviembre de 1960» o solo «1960» si la fuente da el año; nunca se inventa un día."""
    if not value:
        return ''
    if len(value) == 4:
        return value
    d = date.fromisoformat(value)
    return f'{d.day} de {MONTHS_ES[d.month]} de {d.year}'


def life_line(a):
    born, died = life_date_label(a.get('nacimiento')), life_date_label(a.get('fallecimiento'))
    if born and died:
        return born + ' – ' + died
    if died:
        return 'Falleció: ' + died
    return ('Nació: ' + born) if born else ''


def author_century(a):
    year = int(a['nacimiento'][:4]) if a.get('nacimiento') else 0
    century = (year - 1) // 100 + 1 if year else 0
    return f'siglo-{century}' if century in ROMAN else ''


def amazon_author_destination(a):
    """Página de autor de Amazon.es con la etiqueta; sin ID conocido, búsqueda etiquetada por autor en Libros."""
    if a.get('amazon_autor_id'):
        return amazon_es('https://www.amazon.es/stores/author/' + a['amazon_autor_id'] + '?tag=' + AUTHOR_TAG)
    return amazon_es('https://www.amazon.es/s?i=stripbooks&rh=' + quote('p_27:' + a['nombre'], safe='') + '&tag=' + AUTHOR_TAG)


def author_photo(a, lazy=True):
    foto = a.get('foto')
    if not foto:
        initials = ''.join(w[0] for w in re.findall(r'[^\W\d_][\w\'’-]*', a['nombre'])[:2]).upper() or '·'
        return f'<span class="catalogue-author-photo catalogue-author-photo--initials" aria-hidden="true">{esc(initials)}</span>'
    return (f'<img class="catalogue-author-photo" src="{esc(foto["url"])}" width="{foto["ancho"]}" height="{foto["alto"]}" alt="Retrato de {esc(a["nombre"])}"'
            + (' loading="lazy"' if lazy else ' fetchpriority="high"') + ' decoding="async">')


def photo_credit(a):
    foto = a.get('foto')
    if not foto:
        return ''
    return ('<small class="catalogue-photo-credit">Foto: <a href="' + esc(foto['fuente_url']) + '" target="_blank" rel="noopener noreferrer">' + esc(foto['autor']) + NEW_TAB + '</a> · '
            + ('<a href="' + esc(foto['licencia_url']) + '" target="_blank" rel="noopener noreferrer license">' + esc(foto['licencia']) + NEW_TAB + '</a>' if foto.get('licencia_url') else esc(foto['licencia'])) + '</small>')


def author_rows(authors, books, data, publishers, anchor):
    """Una fila por autor con libros: lo que piden la tarjeta, las facetas y la ordenación del índice."""
    index = category_index(data)
    groups_by_slug = {p['slug']: p['grupo'] for p in publishers}
    by_author = {}
    for b in books:
        for name in b['autores']:
            by_author.setdefault(name, []).append(b)
    rows = []
    for a in authors:
        bs = by_author.get(a['nombre'])
        if not bs or a['nombre'] in COLLECTIVE_AUTHORS:
            continue
        cats = {b['id']: categories(data, b, index) for b in bs}
        shown = {}
        for b in bs:
            for c in public(cats[b['id']]):
                shown.setdefault(c['tipo'], {}).setdefault(c['id'], [c, 0])[1] += 1
        pairs = [(kind, cid) for kind in PUBLIC_TYPES for cid in shown.get(kind, {})] + [(kind, NO_VALUE[kind]['id']) for kind in NO_VALUE if kind not in shown]
        facet_values = [cid for _kind, cid in pairs]
        genres = sorted(shown.get('genero', {}).values(), key=lambda t: (-t[1], t[0]['nombre']))
        spans = sorted(((s, b) for b in bs if (s := publication_bounds(b))), key=lambda t: (t[0], t[1]['id']))
        dates = sorted({lo for (lo, _hi), _b in spans})
        released = [(hi, b) for (lo, hi), b in spans if lo <= anchor]
        latest = max(released, key=lambda t: t[0]) if released else None
        coming = [b for (lo, _hi), b in spans if lo > anchor]
        imprints = {}
        for b in bs:
            if b.get('editorial'):
                imprints[b['editorial']] = imprints.get(b['editorial'], 0) + 1
        owners = sorted({groups_by_slug[b['editorial_catalogo_slug']] for b in bs if b.get('editorial_catalogo_slug') in groups_by_slug})
        extra = ([author_century(a)] if author_century(a) else []) + ['editorial-' + slugify(o) for o in owners]
        pairs += [('epoca' if v.startswith('siglo-') else 'editorial', v) for v in extra]
        rows.append({'a': a, 'books': _newest_first(bs), 'groups': sorted({book_group(cats[b['id']]) for b in bs}), 'categories': facet_values + extra, 'pairs': pairs,
                     'genres': [g for g, _ in genres], 'dates': dates, 'latest': latest[0] if latest else '', 'upcoming': [publication_bounds(b)[0] for b in coming],
                     'latest_label': publication_date_label(latest[1]) if latest else '', 'upcoming_label': publication_date_label(coming[0]) if coming else '',
                     'imprint': max(imprints.items(), key=lambda kv: (kv[1], kv[0]))[0] if imprints else '', 'owners': owners,
                     'score': author_score(dates, anchor, len(bs))})
    # Orden de la vista por defecto (con libros publicados, el último más reciente arriba); los que solo tienen
    # próximos lanzamientos van detrás: el primer filtrado del JS no mueve la página.
    rows.sort(key=lambda r: (r['latest'] or '', r['a']['nombre'].casefold()), reverse=True)
    rows.sort(key=lambda r: bool(r['dates']) and not r['latest'])
    return rows


def publication_bounds(b):
    """(primer día, último día) posibles de la publicación, como `boundsOf` en las fichas de libro: un libro con solo
    mes o año no se queda sin fecha (Codex, PR #1546: «Eva está dormida», 2026-04, sacaba a Francesca Melandri del
    filtro «publicado desde» y del orden por fecha)."""
    if exact := b.get('fecha_publicacion'):
        return exact, exact
    if month := b.get('fecha_publicacion_parcial'):
        y, m = (int(p) for p in month.split('-'))
        return month + '-01', (date(y + m // 12, m % 12 + 1, 1) - timedelta(days=1)).isoformat()
    if year := b.get('anio_publicacion'):
        return f'{year}-01-01', f'{year}-12-31'
    return None


def author_score(dates, anchor, count):
    """«Destacados»: próximo libro en 180 días (35), publicado en el último año (30), libros en el catálogo hasta 5 (20)
    y foto/biografía no cuentan; entero para que el orden sea estable y comparable en el JS."""
    day = date.fromisoformat(anchor)
    soon = any(anchor < d <= (day + timedelta(days=180)).isoformat() for d in dates)
    fresh = any((day - timedelta(days=365)).isoformat() <= d <= anchor for d in dates)
    return 35 * soon + 30 * fresh + 4 * min(count, 5)


def author_card(r, lazy=True):
    a, bs = r['a'], r['books']
    titles = ' '.join(b['titulo'] for b in bs)
    isbns = ' '.join(b['isbn13'] for b in bs if b.get('isbn13'))
    born = a.get('nacimiento', '')[:4]
    attrs = (f'data-catalogue-book data-group="{" ".join(r["groups"])}" data-book-id="{esc(a["slug"])}" data-categories="{esc(" ".join(r["categories"]))}" data-title="{esc(a["nombre"])}"'
             f' data-sort-name="{esc(a["nombre"].casefold())}" data-score="{r["score"]}" data-search="{esc(a["nombre"] + " " + titles + " " + isbns)}" data-books="{len(bs)}"'
             + (f' data-dates="{" ".join(r["dates"])}"' if r['dates'] else '') + (f' data-published="{r["latest"]}"' if r['latest'] else '') + (f' data-born="{born}"' if born else ''))
    destination = amazon_author_destination(a)
    amazon = f'href="{esc(destination)}" target="_blank" rel="sponsored nofollow noopener noreferrer"'
    if r['upcoming']:
        when = 'Próximo libro · ' + r['upcoming_label']
    elif r['latest']:
        when = 'Último libro · ' + r['latest_label']
    else:
        when = ''
    genres = r['genres'][:2] if len(r['genres']) <= 2 else []
    chips = ''.join(f'<li><a href="{AUTHORS_BASE}#genero={esc(c["id"])}">{esc(c["nombre"])}</a></li>' for c in genres) or ('<li><span>Varios géneros</span></li>' if r['genres'] else '')
    bio = a.get('biografia_breve')
    if bio:
        description = first_sentence(bio)
    else:
        shown = ', '.join('«' + b['titulo'] + '»' for b in bs[:2])
        description = 'En el catálogo: ' + shown + (f' y {len(bs) - 2} más.' if len(bs) > 2 else '.')
    life = life_line(a)
    count = str(len(bs)) + (' libro' if len(bs) == 1 else ' libros') + ' en el catálogo'
    return (f'<li class="catalogue-card" {attrs}><a class="catalogue-card__cover" {amazon} aria-label="Libros de {esc(a["nombre"])} en Amazon (otra pestaña)">{author_photo(a, lazy)}</a>'
            + f'<div>{photo_credit(a)}' + (f'<p class="eyebrow catalogue-when">{esc(when)}</p>' if when else '') + (f'<ul class="catalogue-tags catalogue-tags--compact">{chips}</ul>' if chips else '')
            + f'<h3><a {amazon} aria-label="Libros de {esc(a["nombre"])} en Amazon (otra pestaña)">{esc(a["nombre"])}</a></h3>'
            + (f'<p class="catalogue-author-life">{esc(life)}</p>' if life else '')
            + (f'<p class="catalogue-author">{esc(r["imprint"])}</p>' if r['imprint'] else '')
            + f'<p class="catalogue-card__description">{esc(description)}</p><p class="catalogue-author-count">{count}</p>'
            + f'<a class="text-action catalogue-card__ficha" href="{author_url(a)}" target="_blank" rel="noopener noreferrer" aria-label="Ver ficha de {esc(a["nombre"])} (se abre en otra pestaña)">Ver ficha</a>'
            + f'<a class="catalogue-buy-link catalogue-card__buy" {amazon} aria-label="Ver los libros de {esc(a["nombre"])} en Amazon (otra pestaña)">Sus libros en Amazon <span aria-hidden="true">↗</span></a></div></li>')


AUTHOR_HUB_SORTS = (('editorial', 'Último libro · más reciente primero'), ('destacados', 'Destacados · próximos y novedades'), ('nombre', 'Nombre · A–Z'), ('libros_desc', 'Número de libros · de más a menos'))
AUTHOR_BIRTH_SORTS = (('nacimiento_asc', 'Nacimiento · del más antiguo al más reciente'), ('nacimiento_desc', 'Nacimiento · del más reciente al más antiguo'))


def author_facet_counts(rows):
    """Recuentos de la vista por defecto (autores con algún libro publicado, sin filtros); el JS los recalcula."""
    counts = {}
    for r in rows:
        if r['dates'] and not r['latest']:
            continue
        for key in [('grupo', g) for g in r['groups']] + r['pairs']:
            counts[key] = counts.get(key, 0) + 1
    return counts


def render_author_filters(data, rows, counts):
    used = {v for r in rows for v in r['categories']}
    groups = {g for r in rows for g in r['groups']}
    facets = facet_group('grupo', 'Tipo que escribe', group_options(groups), True, counts)
    for kind in PUBLIC_TYPES:
        choices = sorted((c for c in data['categorias'] if c['tipo'] == kind and c['activa'] and c['id'] in used), key=age_order if kind == 'edad' else lambda c: (c['orden'], c['id']))
        options = [(c['id'], c['nombre']) for c in choices] + ([(NO_VALUE[kind]['id'], NO_VALUE[kind]['nombre'])] if NO_VALUE[kind]['id'] in used else [])
        if options:
            facets += facet_group(kind, TYPES[kind] if kind == 'genero' else 'Edad del lector', options, counts=counts)
    centuries = sorted({v for v in used if v.startswith('siglo-')}, key=lambda v: int(v[6:]))
    if len(centuries) > 1:
        facets += facet_group('epoca', 'Época (nacimiento)', [(v, 'Siglo ' + ROMAN[int(v[6:])]) for v in centuries], counts=counts)
    # Solo los grupos con peso (≥5 autores): 77 casillas de un autor cada una no ayudan a descubrir a nadie.
    owners = sorted((o for o in {o for r in rows for o in r['owners']} if counts.get(('editorial', 'editorial-' + slugify(o)), 0) >= 5),
                    key=lambda o: (-counts[('editorial', 'editorial-' + slugify(o))], o.casefold()))
    if len(owners) > 1:
        facets += facet_group('editorial', 'Grupo editorial', [('editorial-' + slugify(o), o) for o in owners], counts=counts)
    controls = '<label>Con algún libro publicado desde<input type="date" name="desde" data-filter="desde" min="1000-01-01" max="2100-12-31"></label>'
    search = '<label class="catalogue-search">Buscar por autor, título o ISBN<input type="search" name="q" data-filter="q" maxlength="200" autocomplete="off" placeholder="Nombre, libro o ISBN"></label>'
    toggle = '<button type="button" class="catalogue-refine-toggle" aria-expanded="false" aria-controls="catalogue-refine" data-catalogue-refine-toggle>Filtros <span class="catalogue-refine-count" data-catalogue-refine-count></span><span aria-hidden="true">＋</span></button>'
    return ('<aside class="catalogue-sidebar"><form id="catalogue-search-form" class="catalogue-filters" data-catalogue-filters><fieldset disabled><legend>Encuentra a tu próximo autor</legend>' + search + toggle
            + '<div class="catalogue-refine" id="catalogue-refine" data-catalogue-refine><div class="catalogue-facets">' + facets + '</div><div class="catalogue-filter-grid">' + controls + '</div>'
            '<div class="catalogue-filter-actions"><button type="submit">Buscar autores</button><button type="reset" disabled>Restablecer</button></div></div></fieldset></form></aside>')


def authors_page_url(number):
    return catalogue_page_url(number, AUTHORS_BASE)


def render_authors_index(authors, books, template, data=None, page_number=1, publishers=()):
    """Índice de autores con el mismo formato que el catálogo de libros: test, filtros con recuentos, «Mostrar»,
    «Ordenar por», tarjetas y páginas estáticas de 96 que el JS une para filtrar y paginar de 24 en 24."""
    anchor = data_anchor(books)
    rows = author_rows(authors, books, data, publishers, anchor)
    page_count = max(1, math.ceil(len(rows) / CATALOGUE_PAGE_SIZE))
    require(type(page_number) is int and 1 <= page_number <= page_count, 'Página de autores fuera de rango')
    offset = (page_number - 1) * CATALOGUE_PAGE_SIZE
    visible = rows[offset:offset + CATALOGUE_PAGE_SIZE]
    canonical = SITE + authors_page_url(page_number)
    all_cards = [author_card(r, i > 3) for i, r in enumerate(rows)]
    version = hashlib.sha256(''.join(all_cards).encode()).hexdigest()[:16]
    cards = all_cards[offset:offset + CATALOGUE_PAGE_SIZE]
    born = any(r['a'].get('nacimiento') for r in rows)
    first = page_number == 1
    filters = render_author_filters(data, rows, author_facet_counts(rows)) if first else ''
    sort = ('<label>Ordenar por<select name="orden" data-filter="orden" form="catalogue-search-form" disabled>' + ''.join(f'<option value="{v}">{esc(t)}</option>' for v, t in AUTHOR_HUB_SORTS + (AUTHOR_BIRTH_SORTS if born else ())) + '</select></label>') if first else ''
    show = '<label>Mostrar<select name="estado" data-filter="estado" form="catalogue-search-form" disabled><option value="">Con libros publicados</option><option value="proximos" id="estado=proximos">Con próximos lanzamientos</option><option value="todos">Todos</option></select></label>' if first else ''
    upcoming = '<div class="catalogue-shortcuts"><a class="catalogue-upcoming-link" href="#estado=proximos" data-catalogue-upcoming>Ver autores con próximos lanzamientos →</a></div>' if first and any(r['upcoming'] for r in rows) else ''
    static_count = f'Mostrando {offset + 1}–{offset + len(visible)} de {len(rows)} autores' if rows else '0 autores'
    catalogue = ('<section class="catalogue-section" id="catalogo" aria-label="Buscar autores"><div class="' + ('catalogue-layout' if first else 'catalogue-static-layout') + '">' + filters
                 + '<div class="catalogue-main"><div class="catalogue-results-head"><h2>Los autores</h2><div class="catalogue-results-controls">' + show + sort + '</div>' + upcoming
                 + '<div class="catalogue-count-line"><p role="status" aria-live="polite" data-catalogue-count>' + static_count + '</p>' + ('<button type="button" class="catalogue-clear-link" data-catalogue-clear hidden>Eliminar filtros</button>' if first else '') + '</div>'
                 + ('<div class="catalogue-active" data-catalogue-active hidden></div>' if first else '') + '</div><ul class="catalogue-grid">' + ''.join(cards) + '</ul>' + catalogue_pager(page_number, page_count, AUTHORS_BASE)
                 + '<div class="catalogue-empty" data-catalogue-empty' + (' hidden' if rows else '') + '><h2>No hay autores con estos filtros</h2><p>Prueba con otros filtros o restablece la búsqueda.</p><a class="text-action" href="/recomendaciones/">Explorar todos los libros</a></div>'
                 '<noscript><p>Puedes consultar todos los autores recorriendo las páginas del índice. Los filtros requieren JavaScript.</p></noscript></div></div></section>')
    if not first:
        catalogue = f'<p class="catalogue-static-note">Estás en el listado completo, sin filtros. <a class="text-action" href="{AUTHORS_BASE}#catalogo" target="_self">Filtrar, buscar y ordenar todos los autores →</a></p>' + catalogue
    quiz = '<details class="catalogue-quiz"><summary>¿Qué te apetece leer? Haz el test y encuentra a tu próximo autor</summary><div class="catalogue-quiz__panel"><p>Puedes recorrer las páginas del índice para consultar todos los autores.</p></div></details>' if rows and first else ''
    crumbs = [('Inicio', '/'), ('Libros recomendados', '/recomendaciones/'), ('Autores', AUTHORS_BASE)] + ([(f'Página {page_number}', authors_page_url(page_number))] if not first else [])
    nav = ''.join(f'<li><a href="{href}">{esc(label)}</a></li>' for label, href in crumbs[:-1]) + f'<li aria-current="page">{esc(crumbs[-1][0])}</li>'
    heading = 'Autores' if first else f'Autores: página {page_number}'
    root_attrs = (f' data-reading-catalogue data-catalogue-total="{len(rows)}"' if first else '') + f' data-catalogue-version="{version}" data-catalogue-base="{AUTHORS_BASE}" data-noun-one="autor" data-noun-many="autores" data-catalogue-market="off"'
    main = (f'<main id="contenido" tabindex="-1" class="v1-main recommendations-hub reading-catalogue catalogue-authors-hub"{root_attrs} data-family="recomendaciones">'
            f'<nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol>{nav}</ol></nav>'
            f'<header class="recommendations-hero catalogue-hero"><p class="eyebrow">Catálogo · Autores</p><h1>{heading}</h1><p>Descubre a los autores de los libros recomendados: qué escriben, sus últimos y próximos libros, y dónde encontrarlos.</p></header>'
            + quiz + catalogue + '<p><a class="text-action" href="/recomendaciones/">Explorar todos los libros</a> · <a class="text-action" href="/recomendaciones/editoriales/">Editoriales del catálogo</a></p></main>')
    title = 'Autores de los libros recomendados | David Porto Díaz' if first else f'Autores de los libros recomendados: página {page_number} | David Porto Díaz'
    description = (f'{len(rows)} autores de los libros recomendados: filtra por tipo de libro, género y edad, y descubre sus últimos y próximos lanzamientos.' if first
                   else f'Página {page_number} del índice de autores de los libros recomendados. Vuelve al índice para filtrar y buscar entre todos.')
    schema = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'CollectionPage', '@id': canonical, 'url': canonical, 'name': title.split(' | ')[0], 'description': description, 'dateModified': collection_modified({}, books), 'inLanguage': 'es', 'isPartOf': {'@id': SITE + '/#website'}, 'mainEntity': {'@id': canonical + '#autores'}},
        {'@type': 'ItemList', '@id': canonical + '#autores', 'name': 'Autores', 'numberOfItems': len(visible), 'itemListElement': [{'@type': 'ListItem', 'position': offset + i + 1, 'item': {'@type': 'Person', '@id': SITE + author_url(r['a']) + '#person', 'name': r['a']['nombre'], 'url': SITE + author_url(r['a'])}} for i, r in enumerate(visible)]},
        _breadcrumb_schema(crumbs)]}
    return render_detail_page(template, main, canonical, title, description, schema, None)


PUBLISHER_SORTS = (('nombre', 'Nombre · A–Z'), ('proximo', 'Próximo libro · el más cercano primero'), ('reciente', 'Último libro · el más reciente primero'), ('libros', 'Número de libros · de más a menos'))
PUBLISHER_STATES = (('', 'Todos los sellos'), ('proximos', 'Con próximos lanzamientos'), ('novedad', 'Con novedad en los últimos 30 días'))


def _index_select(key, label, options):
    return '<label>' + label + '<select name="' + key + '" data-index-filter="' + key + '">' + ''.join('<option value="' + esc(v) + '">' + esc(t) + '</option>' for v, t in options) + '</select></label>'


def render_publishers_index(catalogue_publishers, books, template, data=None):
    """Sellos con libros en el catálogo: los del directorio enlazan a su ficha de manuscritos.
    Mismos filtros que el índice de autores: el portal de novedades también se recorre por sello."""
    canonical = SITE + '/recomendaciones/editoriales/'
    anchor = data_anchor(books)
    by_slug = {p['slug']: p for p in catalogue_publishers}
    entries = {}
    for b in books:
        if b.get('editorial_catalogo_slug'):
            p = by_slug[b['editorial_catalogo_slug']]
            entries.setdefault(p['slug'], [p['nombre'], publisher_url(p), [], p['grupo']])[2].append(b)
        elif b.get('editorial_slug'):
            entries.setdefault(b['editorial_slug'], [b['editorial'], '/editoriales/' + b['editorial_slug'] + '/', [], ''])[2].append(b)
    ordered = sorted(entries.values(), key=lambda e: e[0].casefold())
    groups, owners, items = {}, {}, []
    for name, href, bs, owner in ordered:
        newest = _newest_first(bs)
        upcoming = sorted((b for b in bs if b.get('fecha_publicacion', '') > anchor), key=lambda b: b['fecha_publicacion'])
        latest = next((b for b in newest if b.get('fecha_publicacion', '') <= anchor), None)
        when = ('Próximo libro · ' + publication_date_label(upcoming[0])) if upcoming else ('Último libro · ' + publication_date_label(latest)) if latest and publication_date_label(latest) else ''
        kinds = sorted({book_group(categories(data, b)) for b in bs}) if data else []
        for kind in kinds:
            groups[kind] = groups.get(kind, 0) + 1
        owner_id = re.sub(r'\W+', '-', owner.casefold()).strip('-')
        if owner_id:
            owners.setdefault(owner_id, [owner, 0])[1] += 1
        dates = ' '.join(sorted({b['fecha_publicacion'] for b in bs if b.get('fecha_publicacion')}))
        attrs = ' data-groups="' + ' '.join(kinds) + '" data-owner="' + owner_id + '" data-books="' + str(len(bs)) + '"' + (' data-dates="' + dates + '"' if dates else '')
        items.append('<li' + attrs + '><a href="' + href + '">' + image(newest[0], True, '120px', 'catalogue-index__image', '') + '<span>' + esc(name) + '</span></a>'
                     + ('<p class="eyebrow catalogue-when">' + esc(when) + '</p>' if when else '')
                     + '<p>' + str(len(bs)) + (' libro' if len(bs) == 1 else ' libros') + ' en el catálogo' + (' · ' + esc(owner) if owner else '') + '</p>'
                     + '<p class="catalogue-index__bio">' + esc(', '.join(b['titulo'] for b in newest[:2])) + ('…' if len(bs) > 2 else '') + '</p></li>')
    summary = 'Editoriales de los libros recomendados: ' + str(len(ordered)) + ' sellos con sus libros.'
    kinds = [('', 'Todos los tipos')] + [(gid, label + ' (' + str(groups[gid]) + ')') for gid, label in group_options(groups)]
    owner_options = [('', 'Todos los grupos')] + [(oid, o[0] + ' (' + str(o[1]) + ')') for oid, o in sorted(owners.items(), key=lambda kv: kv[1][0].casefold())]
    upcoming = any(b.get('fecha_publicacion', '') > anchor for b in books)
    # Sin JS el formulario queda desactivado y la lista completa sigue a la vista (enlaces rastreables).
    filters = ('<form class="catalogue-filters catalogue-authors-filters" data-index-filters data-noun="sellos" role="search" aria-label="Filtrar editoriales"><fieldset disabled><legend>Encuentra editoriales</legend><div class="catalogue-filter-grid">'
               '<label class="catalogue-search">Buscar por sello o título<input type="search" name="q" data-index-filter="q" maxlength="120" autocomplete="off" placeholder="Nombre del sello o de un libro"></label>'
               + (_index_select('tipo', 'Tipo de libro', kinds) if groups else '') + (_index_select('grupo', 'Grupo editorial', owner_options) if owners else '')
               + _index_select('estado', 'Mostrar', PUBLISHER_STATES) + _index_select('orden', 'Ordenar por', PUBLISHER_SORTS)
               + '</div><div class="catalogue-filter-actions"><button type="submit">Buscar editoriales</button>' + ('<button type="button" class="catalogue-upcoming-link" data-index-shortcut>Sellos con próximos lanzamientos →</button>' if upcoming else '') + '<button type="reset">Restablecer</button></div></fieldset></form>')
    main = ('<main id="contenido" tabindex="-1" class="v1-main reading-catalogue catalogue-author-page catalogue-authors-index" data-family="recomendaciones"><nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol><li><a href="/">Inicio</a></li><li><a href="/recomendaciones/">Libros recomendados</a></li><li aria-current="page">Editoriales del catálogo</li></ol></nav>'
            '<header class="catalogue-author-hero"><p class="eyebrow">Libros recomendados</p><h1>Editoriales del catálogo</h1><p>' + esc(summary) + '</p></header>'
            + filters +
            '<section aria-labelledby="publishers-list"><div class="catalogue-results-head"><h2 id="publishers-list">Todos los sellos</h2><p role="status" aria-live="polite" data-index-count>' + str(len(ordered)) + ' sellos</p></div>'
            '<p class="catalogue-authors-empty" data-index-empty hidden>Ningún sello coincide con esos filtros. <button type="button" data-index-reset>Quitar filtros</button></p>'
            '<ul class="catalogue-author-books" data-index-list>' + ''.join(items) + '</ul></section>'
            '<div class="catalogue-end"><a class="text-action" href="/editoriales/">Directorio de editoriales que aceptan manuscritos</a> · <a class="text-action" href="/recomendaciones/">Explorar todos los libros</a></div></main>')
    schema = {'@context': 'https://schema.org', '@graph': [{'@type': 'CollectionPage', '@id': canonical, 'url': canonical, 'name': 'Editoriales del catálogo', 'dateModified': collection_modified({}, books)},
                                                  _breadcrumb_schema([('Inicio', '/'), ('Libros recomendados', '/recomendaciones/'), ('Editoriales del catálogo', '/recomendaciones/editoriales/')])]}
    page = render_detail_page(template, main, canonical, 'Editoriales de los libros recomendados | David Porto Díaz', summary, schema, None)
    page = page.replace('</head>', '<link rel="stylesheet" href="/assets/catalogue-authors.css?v=' + AUTHORS_ASSET_VERSION + '">\n</head>', 1)
    return page.replace('</body>', '<script defer src="/assets/catalogue-authors.js?v=' + AUTHORS_ASSET_VERSION + '"></script>\n</body>', 1)


def registry_entries(books):
    return [{"id": "reading-book-" + b["id"], "url": url(b), "label": b["titulo"], "shortLabel": b["titulo"], "type": "article", "territory": "recomendaciones", "parentId": "recommendations-hub", "hubId": "recommendations-hub", "discoverability": "secondary", "audience": ["reader"], "jobs": ["buscar-lecturas"], "sourceFile": url(b).lstrip('/') + 'index.html'} for b in books]


RETIRABLE = ('reading-book-', 'reading-author-', 'reading-publisher-')


def retired_entries(previous, current):
    """Fichas que existían y ya no se generan (libro retirado, autor o sello sin libros): siguen en el registro como
    «deprecated», sin página, fuera de índices y del sitemap. El retiro queda declarado y no parece un enlace perdido;
    si la ficha vuelve, su entrada viva la sustituye."""
    live = {e['id'] for e in current}
    return [{**e, 'status': 'deprecated', 'searchIndex': False, 'sitemap': False, 'sourceFile': ''}
            for e in previous if e['id'].startswith(RETIRABLE) and e['id'] not in live]


def render_map(original, books, authors=(), publishers=(), author_pages=1):
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
    continuation_links += ''.join(f'<li><a href="{authors_page_url(n)}">Autores: página {n}</a></li>' for n in range(2, author_pages + 1))
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
    AUTHOR_TEXTS.clear()
    AUTHOR_TEXTS.update(load_author_texts(root))
    index_categories(data)
    authors = author_records(root)
    template = (root / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
    outputs = {'recomendaciones/index.html': render_hub(data, books, template)}
    for number in range(2, max(1, math.ceil(len(books) / CATALOGUE_PAGE_SIZE)) + 1):
        outputs[catalogue_page_url(number).lstrip('/') + 'index.html'] = render_hub(data, books, template, number)
    for b in books:
        outputs[url(b).lstrip('/') + 'index.html'] = render_book(data, b, template)
    active_authors = [a for a in authors if any(a['nombre'] in b['autores'] for b in books)]
    anchor = data_anchor(books)
    for a in active_authors:
        outputs[author_url(a).lstrip('/') + 'index.html'] = render_author(a, data, books, template, active_authors, anchor)
    catalogue_publishers = publisher_records(root)
    author_pages = max(1, math.ceil(len(author_rows(active_authors, books, data, catalogue_publishers, data_anchor(books))) / CATALOGUE_PAGE_SIZE))
    for number in range(1, author_pages + 1):
        outputs[authors_page_url(number).lstrip('/') + 'index.html'] = render_authors_index(active_authors, books, template, data, number, catalogue_publishers)
    map_path = root / 'mapa-del-sitio/index.html'
    if map_path.exists():
        outputs['mapa-del-sitio/index.html'] = render_map(map_path.read_text(encoding='utf-8'), books, authors, catalogue_publishers, author_pages)
    active_publishers = [p for p in catalogue_publishers if any(b.get('editorial_catalogo_slug') == p['slug'] for b in books)]
    for p in active_publishers:
        outputs[publisher_url(p).lstrip('/') + 'index.html'] = render_publisher(p, data, books, template, {a['nombre'] for a in authors}, active_authors)
    outputs['recomendaciones/editoriales/index.html'] = render_publishers_index(catalogue_publishers, books, template, data)
    outputs[ICS_PATH] = render_release_ics(books)
    outputs[DEALS_PATH] = render_deals(books)
    outputs[LLMS_PATH] = render_llms_index(data, books, active_authors, active_publishers)
    existing = root / 'recomendaciones/libros'
    orphans = [p for p in existing.glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
    orphans += [p for p in (root / 'recomendaciones/pagina').glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
    orphans += [p for p in (root / 'recomendaciones/autores').glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
    orphans += [p for p in (root / 'recomendaciones/autores/pagina').glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
    orphans += [p for p in (root / 'recomendaciones/editoriales').glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
    require(not orphans, 'Hay fichas existentes fuera de los datos: revisar retirada/URL antes de eliminarlas')
    registry = json.loads((root / 'data/content-registry.json').read_text(encoding='utf-8'))
    previous = list(registry['entries'])
    registry['entries'] = [e for e in registry['entries'] if not e['id'].startswith(('reading-book-', 'reading-author-', 'reading-publisher-', 'reading-index-', 'reading-page-'))] + registry_entries(books)
    registry['entries'] += [{'id': 'reading-author-' + a['slug'], 'url': author_url(a), 'label': a['nombre'], 'shortLabel': a['nombre'], 'type': 'article', 'territory': 'recomendaciones', 'parentId': 'recommendations-hub', 'hubId': 'recommendations-hub', 'discoverability': 'secondary', 'audience': ['reader'], 'jobs': ['buscar-lecturas'], 'sourceFile': author_url(a).lstrip('/') + 'index.html'} for a in active_authors]
    registry['entries'] += [{'id': 'reading-publisher-' + p['slug'], 'url': publisher_url(p), 'label': p['nombre'], 'shortLabel': p['nombre'], 'type': 'article', 'territory': 'recomendaciones', 'parentId': 'recommendations-hub', 'hubId': 'recommendations-hub', 'discoverability': 'secondary', 'audience': ['reader'], 'jobs': ['buscar-lecturas'], 'sourceFile': publisher_url(p).lstrip('/') + 'index.html'} for p in active_publishers]
    registry['entries'] += [{'id': 'reading-index-' + key, 'url': '/recomendaciones/' + key + '/', 'label': label, 'shortLabel': label, 'type': 'article', 'territory': 'recomendaciones', 'parentId': 'recommendations-hub', 'hubId': 'recommendations-hub', 'discoverability': 'secondary', 'footerEligible': True, 'audience': ['reader'], 'jobs': ['buscar-lecturas'], 'sourceFile': 'recomendaciones/' + key + '/index.html'} for key, label in (('autores', 'Autores'), ('editoriales', 'Editoriales del catálogo'))]
    registry['entries'] += [{'id':f'reading-page-{n}','url':catalogue_page_url(n),'label':f'Libros recomendados: página {n}','shortLabel':f'Página {n}','type':'article','territory':'recomendaciones','parentId':'recommendations-hub','hubId':'recommendations-hub','discoverability':'secondary','searchIndex':False,'sourceFile':catalogue_page_url(n).lstrip('/')+'index.html'} for n in range(2, max(1, math.ceil(len(books) / CATALOGUE_PAGE_SIZE)) + 1)]
    registry['entries'] += [{'id':f'reading-page-autores-{n}','url':authors_page_url(n),'label':f'Autores: página {n}','shortLabel':f'Autores · página {n}','type':'article','territory':'recomendaciones','parentId':'recommendations-hub','hubId':'recommendations-hub','discoverability':'secondary','searchIndex':False,'sourceFile':authors_page_url(n).lstrip('/')+'index.html'} for n in range(2, author_pages + 1)]
    registry['entries'] += retired_entries(previous, registry['entries'])
    outputs['data/content-registry.json'] = json.dumps(registry, ensure_ascii=False, indent=2) + '\n'
    return books, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--data', type=Path)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--hoy', type=date.fromisoformat, help='día del despliegue (AAAA-MM-DD, Madrid); sin él, el de los datos')
    args = parser.parse_args()
    root = args.root.resolve()
    global HOY  # skipcq: PYL-W0603 - parámetro del proceso, se fija una vez al arrancar
    HOY = dia_del_despliegue(args.hoy, os.environ)
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
