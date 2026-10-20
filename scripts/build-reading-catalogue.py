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
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_shell import inject_shell_auto

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://davidportodiaz.com"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
TYPES = {"genero": "Género", "tematica": "Temática", "temporada": "Temporada", "edad": "Edad", "contenido": "Contenido", "epoca": "Época"}
BOOK_FIELDS = set("id slug titulo autores descripcion_breve estado portada_local portada_fuente_url portada_edicion_verificada autorizacion_o_base_uso portada_fecha_revision portada_ancho portada_alto fuente_bibliografica_url fecha_verificacion descripcion_original_confirmada url_amazon_afiliada isbn13 edicion editorial fecha_publicacion anio_publicacion numero_paginas fuente_publicacion_url idioma edad_recomendada fuente_edad_url avisos_contenido lectura_personal_confirmada evidencia_lectura autoria_propia resenas fragmento_url fecha_actualizacion audio_descripcion audio_voz".split())


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
    return isinstance(value, str) and bool(re.fullmatch(r"97[89]\d{10}", value)) and sum(int(n) * (1 if i % 2 == 0 else 3) for i, n in enumerate(value)) % 10 == 0


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
        if b["estado"] == "borrador":
            continue
        for key in ("descripcion_breve", "portada_local", "portada_fuente_url", "autorizacion_o_base_uso", "fuente_bibliografica_url", "fecha_verificacion", "portada_fecha_revision", "fecha_actualizacion", "edicion"):
            require(isinstance(b.get(key), str) and b[key].strip(), f"{name}: falta {key}")
        require(b.get("portada_edicion_verificada") is True and b.get("descripcion_original_confirmada") is True, f"{name}: falta confirmación de edición/descripción original")
        require(type(b.get("lectura_personal_confirmada", False)) is bool and type(b.get("autoria_propia", False)) is bool, f"{name}: confirmaciones deben ser booleanas")
        require(40 <= len(b["descripcion_breve"]) <= 1200, f"{name}: descripción debe tener 40–1200 caracteres")
        require(b['descripcion_breve'].strip().casefold() not in descriptions, f"{name}: descripción duplicada")
        descriptions.add(b['descripcion_breve'].strip().casefold())
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
        reviews = b.get("resenas", [])
        require(isinstance(reviews, list), f"{name}: reseñas debe ser lista")
        seen_reviews = set()
        for review in reviews:
            require(isinstance(review, dict) and set(review) == {"titulo", "url", "fecha_verificacion"}, f"{name}: reseña mal formada")
            require(isinstance(review["titulo"], str) and review["titulo"].strip() and https(review["url"]) and review["url"] not in seen_reviews, f"{name}: reseña sin título/URL o duplicada")
            day(review["fecha_verificacion"], name + ".reseña")
            seen_reviews.add(review["url"])
    seen = set()
    for rel in relations:
        require(isinstance(rel, dict) and set(rel) == {"libro_id", "categoria_id"}, "Relación mal formada")
        pair = (rel["libro_id"], rel["categoria_id"])
        require(pair[0] in book_ids and pair[1] in ids and pair not in seen, "Relación duplicada o referencia inexistente")
        seen.add(pair)
    for b in books:
        if b["estado"] != "borrador":
            require(any(r["libro_id"] == b["id"] and any(c["id"] == r["categoria_id"] and c["activa"] for c in cats) for r in relations), f"{b['id']}: sin categoría activa")
    return [b for b in books if b["estado"] == "publicado"]


def url(b):
    return f"/recomendaciones/libros/{b['slug']}/"


def categories(data, b):
    ids = {r["categoria_id"] for r in data["libro_categorias"] if r["libro_id"] == b["id"]}
    return sorted((c for c in data["categorias"] if c["id"] in ids and c["activa"]), key=lambda c: (c["orden"], c["id"]))


def tags(cats):
    return '<ul class="catalogue-tags">' + ''.join(f'<li><a href="/recomendaciones/#{esc(c["tipo"])}={esc(c["id"])}">{esc(c["nombre"])}</a></li>' for c in cats) + '</ul>'


def image(b, lazy=False):
    loading = 'loading="lazy"' if lazy else 'fetchpriority="high"'
    return f'<img class="catalogue-book-cover" src="{esc(b["portada_local"])}" alt="Portada de {esc(b["titulo"])} — {esc(b["edicion"])}" width="{b["portada_ancho"]}" height="{b["portada_alto"]}" {loading} decoding="async">'


def render_filters(data):
    controls = '<label>Buscar por título o autor<input type="search" name="q" data-filter="q" maxlength="200" autocomplete="off"></label>'
    for kind, label in TYPES.items():
        choices = sorted((c for c in data["categorias"] if c["tipo"] == kind and c["activa"]), key=lambda c: (c["orden"], c["id"]))
        controls += f'<label>{label}<select name="{kind}" data-filter="{kind}"><option value="">Todas las opciones</option>' + ''.join(f'<option value="{esc(c["id"])}">{esc(c["nombre"])}</option>' for c in choices) + '</select></label>'
    controls += '<label>Publicación<select name="novedad" data-filter="novedad"><option value="">Todas las fechas</option><option value="180">Últimos lanzamientos · 180 días</option></select></label>'
    return '<form class="catalogue-filters" data-catalogue-filters><fieldset disabled><legend>Encuentra tu próxima lectura</legend><div class="catalogue-filter-grid">' + controls + '</div><button type="submit">Buscar libros</button></fieldset><div class="catalogue-toolbar"><p>Combina los filtros para afinar la selección.</p><button type="reset" disabled>Limpiar filtros</button></div></form>'


def render_hub(data, books, template):
    cards = []
    for i, b in enumerate(books):
        cats = categories(data, b)
        cards.append(f'<li class="catalogue-card" data-catalogue-book data-categories="{esc(" ".join(c["id"] for c in cats))}" data-search="{esc(b["titulo"] + " " + " ".join(b["autores"]))}" data-published="{esc(b.get("fecha_publicacion", ""))}"><a href="{url(b)}" aria-label="Ver ficha de {esc(b["titulo"])}">{image(b, i > 1)}</a><div><h3><a href="{url(b)}">{esc(b["titulo"])}</a></h3><p>{esc(", ".join(b["autores"]))}</p><p>{esc(b["descripcion_breve"])}</p>{tags(cats)}<a class="text-action" href="{url(b)}">Ver ficha del libro</a></div></li>')
    counts = {}
    for b in books:
        for c in categories(data, b):
            counts[c['id']] = counts.get(c['id'], 0) + 1
    menu = '<nav aria-label="Categorías de los libros"><ul class="catalogue-tags">' + ''.join(f'<li id="{esc(c["tipo"])}={esc(c["id"])}"><a href="/recomendaciones/#{esc(c["tipo"])}={esc(c["id"])}">{esc(c["nombre"])} ({counts[c["id"]]})</a></li>' for c in sorted(data['categorias'], key=lambda c: (c['orden'], c['id'])) if c['activa'] and c['id'] in counts) + '</ul></nav>'
    menu += '<h2 class="sr-only">Resultados del catálogo</h2>'
    catalogue = '<section class="catalogue-section" id="catalogo" aria-label="Buscar libros recomendados">' + render_filters(data) + menu + f'<p role="status" aria-live="polite" data-catalogue-count>{len(books)} libros</p><ul class="catalogue-grid">' + ''.join(cards) + '</ul><div class="catalogue-empty" data-catalogue-empty' + (' hidden' if books else '') + '><h2>' + ('No hay libros con estos filtros' if books else 'Estamos preparando la selección') + '</h2><p>Prueba otras categorías o explora las guías del Cuaderno.</p><a class="text-action" href="/cuaderno/#lecturas">Explorar las guías de lectura</a></div><noscript><p>Puedes consultar todas las fichas y guías sin JavaScript. Los filtros requieren activarlo.</p></noscript></section>'
    page = template.replace('{{catalogue}}', catalogue)
    if books:
        # The existing guide ItemList remains intact; the catalogue has its own list.
        schema = {"@context": "https://schema.org", "@type": "ItemList", "@id": SITE + "/recomendaciones/#catalogo", "name": "Libros recomendados", "numberOfItems": len(books), "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": {"@type": "Book", "@id": SITE + url(b) + "#book", "name": b['titulo'], "url": SITE + url(b), "image": SITE + b['portada_local']}} for i, b in enumerate(books)]}
        page = page.replace('</head>', '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c') + '</script>\n</head>')
    return inject_shell_auto(page)


def render_book(data, b, template):
    canonical = SITE + url(b)
    title = b["titulo"] + " · " + ", ".join(b["autores"]) + " | Libros recomendados"
    description = b["descripcion_breve"]
    cats = categories(data, b)
    rows = [("Edición", b["edicion"]), ("Editorial", b.get("editorial")), ("Publicación", b.get("fecha_publicacion") or b.get('anio_publicacion')), ("ISBN-13", b.get("isbn13")), ("Idioma", b.get("idioma")), ("Páginas", b.get('numero_paginas')), ("Edad orientativa", b.get("edad_recomendada"))]
    details = '<details class="catalogue-details"><summary>Datos de esta edición</summary><dl>' + ''.join(f'<dt>{esc(k)}</dt><dd>{esc(v)}</dd>' for k, v in rows if v) + '</dl></details>'
    amazon = ''
    if b.get("url_amazon_afiliada"):
        amazon = '<p class="affiliate-disclosure">Como afiliado de Amazon, obtengo ingresos por las compras adscritas que cumplen los requisitos aplicables.</p>' + f'<a class="primary-action" href="{esc(b["url_amazon_afiliada"])}" target="_blank" rel="sponsored nofollow noopener noreferrer">Ver en Amazon <span>· enlace de afiliado</span></a>'
    extra = '<details class="catalogue-details"><summary>Fuentes de la edición y la portada</summary><ul>' + f'<li><a href="{esc(b["fuente_bibliografica_url"])}" rel="noopener noreferrer" target="_blank">Fuente bibliográfica de esta edición</a></li><li><a href="{esc(b["portada_fuente_url"])}" rel="noopener noreferrer" target="_blank">Portada: {esc(b.get("editorial") or "fuente editorial")}</a></li>'
    for key, label in (("fuente_publicacion_url", "Fecha de publicación"), ("fuente_edad_url", "Orientación de edad")):
        if b.get(key):
            extra += f'<li><a href="{esc(b[key])}" target="_blank" rel="noopener noreferrer">{label}</a></li>'
    extra += '</ul></details>'
    if b.get('resenas'):
        extra += '<details class="catalogue-details"><summary>Reseñas externas (' + str(len(b['resenas'])) + ')</summary><ul>' + ''.join(f'<li><a href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">Reseña externa: {esc(r["titulo"])}</a></li>' for r in b['resenas']) + '</ul></details>'
    if b.get('fragmento_url'):
        extra += '<details class="catalogue-details"><summary>Leer un fragmento gratuito</summary><p>La muestra se abre en la web de la editorial.</p><a class="text-action" href="' + esc(b['fragmento_url']) + '" target="_blank" rel="noopener noreferrer">Abrir el primer capítulo en la fuente oficial</a></details>'
    main = '<main id="contenido" tabindex="-1" class="v1-main reading-catalogue" data-family="recomendaciones" data-reading-catalogue><nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol><li><a href="/">Inicio</a></li><li><a href="/cuaderno/">Cuaderno</a></li><li><a href="/recomendaciones/">Libros recomendados</a></li><li aria-current="page">' + esc(b["titulo"]) + '</li></ol></nav><article class="catalogue-book-layout"><div>' + image(b) + '</div><div><p class="eyebrow">Libros recomendados</p><h1>' + esc(b["titulo"]) + '</h1><p>' + esc(", ".join(b["autores"])) + '</p>'
    if b.get("autoria_propia"):
        main += '<p>Obra del autor de esta web, David Porto Díaz.</p>'
    speech = '<div class="catalogue-speech" hidden><button type="button" data-catalogue-speak>Escuchar descripción</button> <button type="button" data-catalogue-stop disabled>Detener lectura</button><p role="status" data-catalogue-speech-status></p></div>'
    if b.get('audio_descripcion'):
        speech = '<div class="catalogue-audio"><p>Escuchar la descripción' + (' · ' + esc(b['audio_voz']) if b.get('audio_voz') else '') + '</p><audio controls preload="none" aria-label="Escuchar la descripción de ' + esc(b['titulo']) + '"><source src="' + esc(b['audio_descripcion']) + '" type="audio/mpeg"></audio></div>'
    main += '<p data-catalogue-description>' + esc(description) + '</p>' + speech + tags(cats)
    if b.get("avisos_contenido"):
        main += '<p><strong>Sobre el contenido:</strong> ' + esc(b["avisos_contenido"]) + '</p>'
    main += amazon + details + extra + f'<p>Datos de la edición revisados el <time datetime="{esc(b["fecha_verificacion"])}">{esc(b["fecha_verificacion"])}</time>. Esta comprobación no implica una lectura personal.</p><p><a href="/recomendaciones/politica-de-recomendaciones/">Criterio editorial y correcciones</a></p><a class="text-action" href="/recomendaciones/">Volver al catálogo</a></div></article></main>'
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "Book", "@id": canonical + "#book", "url": canonical, "name": b["titulo"], "author": [{"@type": "Person", "name": a} for a in b["autores"]], "description": description, "image": SITE + b["portada_local"], "bookEdition": b["edicion"], **({"isbn": b["isbn13"]} if b.get("isbn13") else {}), **({"datePublished": b["fecha_publicacion"]} if b.get("fecha_publicacion") else {})},
        {"@type": "WebPage", "@id": canonical + "#page", "url": canonical, "name": title, "dateModified": b["fecha_actualizacion"], "mainEntity": {"@id": canonical + "#book"}},
        {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": label, "item": SITE + href} for i, (label, href) in enumerate([("Inicio", "/"), ("Cuaderno", "/cuaderno/"), ("Libros recomendados", "/recomendaciones/"), (b["titulo"], url(b))])]}]}
    page = template.replace('{{catalogue}}', '')
    page = re.sub(r'<main\b[\s\S]*?</main>', lambda _: main, page, count=1)
    page = re.sub(r'<title>.*?</title>', lambda _: '<title>' + esc(title) + '</title>', page, count=1)
    meta_description = description if len(description) <= 160 else description[:157].rsplit(' ', 1)[0].rstrip('.,;:') + '…'
    for key, value in (("description", meta_description), ("og:title", title), ("og:description", meta_description), ("og:url", canonical), ("og:image", SITE + b["portada_local"]), ("og:image:alt", "Portada de " + b["titulo"]), ("og:image:width", b["portada_ancho"]), ("og:image:height", b["portada_alto"]), ("twitter:title", title), ("twitter:description", meta_description), ("twitter:image", SITE + b["portada_local"]), ("twitter:image:alt", "Portada de " + b["titulo"])):
        page = re.sub(r'(<meta (?:name|property)="' + re.escape(key) + r'" content=")[^"]*', lambda m: m[1] + esc(value), page)
    page = page.replace('href="https://davidportodiaz.com/recomendaciones/"', 'href="' + canonical + '"')
    page = re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>', lambda _: '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace('<', '\\u003c') + '</script>', page, count=1)
    return inject_shell_auto(page)


def registry_entries(books):
    return [{"id": "reading-book-" + b["id"], "url": url(b), "label": b["titulo"], "shortLabel": b["titulo"], "type": "article", "territory": "cuaderno", "parentId": "recommendations-hub", "hubId": "notebook-hub", "discoverability": "secondary", "audience": ["reader"], "jobs": ["buscar-lecturas"], "sourceFile": url(b).lstrip('/') + 'index.html'} for b in books]


def render_map(original, books):
    start, end = '<!-- reading-catalogue-map:start -->', '<!-- reading-catalogue-map:end -->'
    original = re.sub(re.escape(start) + r'[\s\S]*?' + re.escape(end) + r'\n?', '', original)
    if not books:
        return original
    links = ''.join(f'<li><a href="{url(b)}">{esc(b["titulo"])} — {esc(", ".join(b["autores"]))}</a></li>' for b in books)
    block = start + '<section class="directory-section"><h2>Libros recomendados</h2><p><a href="/recomendaciones/">Explorar el catálogo de lectura</a></p><details class="directory-reading-books"><summary>Ver las fichas de lectura</summary><ul class="directory-list">' + links + '</ul></details></section>' + end + '\n'
    require('</main>' in original, 'Mapa del sitio sin main')
    return original.replace('</main>', block + '</main>', 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--data', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        data = json.loads((args.data or root / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = validate(data, root)
        template = (root / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
        outputs = {'recomendaciones/index.html': render_hub(data, books, template)}
        map_path = root / 'mapa-del-sitio/index.html'
        if map_path.exists():
            outputs['mapa-del-sitio/index.html'] = render_map(map_path.read_text(encoding='utf-8'), books)
        for b in books:
            outputs[url(b).lstrip('/') + 'index.html'] = render_book(data, b, template)
        existing = root / 'recomendaciones/libros'
        orphans = [p for p in existing.glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
        require(not orphans, 'Hay fichas existentes fuera de los datos: revisar retirada/URL antes de eliminarlas')
        registry = json.loads((root / 'data/content-registry.json').read_text(encoding='utf-8'))
        registry['entries'] = [e for e in registry['entries'] if not e['id'].startswith('reading-book-')] + registry_entries(books)
        outputs['data/content-registry.json'] = json.dumps(registry, ensure_ascii=False, indent=2) + '\n'
        drift = []
        for rel, text in outputs.items():
            target = root / rel
            if not target.exists() or target.read_text(encoding='utf-8') != text:
                drift.append(rel)
                if not args.check:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(text, encoding='utf-8', newline='\n')
        require(not args.check or not drift, 'Catálogo desactualizado: ' + ', '.join(drift))
        print(f'Catálogo OK: {len(books)} libros publicados; {len(drift)} archivos {"pendientes" if args.check else "actualizados"}.')
        return 0
    except (ValidationError, ValueError, KeyError, TypeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
