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
BOOK_FIELDS = set("id slug titulo autores descripcion_breve estado portada_local portada_fuente_url portada_edicion_verificada autorizacion_o_base_uso portada_fecha_revision portada_ancho portada_alto fuente_bibliografica_url fecha_verificacion descripcion_original_confirmada url_amazon_afiliada isbn13 edicion editorial fecha_publicacion anio_publicacion numero_paginas fuente_publicacion_url idioma edad_recomendada fuente_edad_url avisos_contenido lectura_personal_confirmada evidencia_lectura autoria_propia resenas fragmento_url fecha_actualizacion audio_descripcion audio_voz formatos_compra fragmento_texto fragmento_uso_autorizado fragmento_base_uso audio_fragmento".split())
FORMATS = {"tapa-blanda": "Tapa blanda", "tapa-dura": "Tapa dura", "ebook": "eBook", "audiolibro": "Audiolibro"}
BOOK_FIELDS.update({'editorial_slug', 'formato_edicion', 'amazon_busqueda_isbn', 'fecha_publicacion_parcial'})


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
        if b.get('editorial_slug'):
            require(SLUG.fullmatch(b['editorial_slug']) and (root / 'editoriales' / b['editorial_slug'] / 'index.html').is_file(), f'{name}: editorial inexistente')
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
        formats = b.get('formatos_compra', [])
        require(isinstance(formats, list), f'{name}: formatos_compra debe ser una lista')
        seen_formats = set()
        for option in formats:
            require(isinstance(option, dict) and set(option) == {'formato', 'url', 'fuente_url', 'fecha_verificacion'}, f'{name}: formato de compra inválido')
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


def image(b, lazy=False, sizes='(max-width: 600px) 35vw, 260px'):
    loading = 'loading="lazy"' if lazy else 'fetchpriority="high"'
    preview = b['portada_local'].replace('.webp', '-320.webp')
    responsive = f' srcset="{esc(preview)} 320w, {esc(b["portada_local"])} {b["portada_ancho"]}w" sizes="{esc(sizes)}"' if b['portada_local'].startswith('/assets/reading-covers/isbn-') else ''
    return f'<img class="catalogue-book-cover" src="{esc(b["portada_local"])}"{responsive} alt="Portada de {esc(b["titulo"])} — {esc(b["edicion"])}" width="{b["portada_ancho"]}" height="{b["portada_alto"]}" {loading} decoding="async">'


def novelty(b, fallback):
    return '<span data-release-label="' + esc(b.get('fecha_publicacion', '')) + '" data-release-fallback="' + esc(fallback) + '">' + esc(fallback) + '</span>'


def book_title(b):
    base = b['titulo'] + ' · ' + ', '.join(b['autores'])
    full = base + ' | Libros recomendados'
    if len(full) <= 75:
        return full
    if len(base) <= 75:
        return base
    suffix = ' · ' + (b.get('isbn13') or hashlib.sha256(b['id'].encode()).hexdigest()[:8])
    return b['titulo'][:74-len(suffix)].rsplit(' ', 1)[0] + '…' + suffix


def author_records(root=ROOT):
    path = root / 'data/reading-authors.json'
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding='utf-8'))
    require(set(payload) == {'schema_version', 'autores'} and payload['schema_version'] == 1, 'Contrato de autores inválido')
    names, slugs = set(), set()
    for a in payload['autores']:
        required = {'slug', 'nombre', 'descripcion', 'fuentes', 'fecha_verificacion'}
        require(set(a) == required | ({'tipo'} if a.get('tipo') == 'bibliografico' else {'nacimiento'}), 'Campos de autor inválidos')
        require(SLUG.fullmatch(a['slug']) and a['slug'] not in slugs and a['nombre'] not in names, 'Autor duplicado o slug inválido')
        require(isinstance(a['descripcion'], str) and len(a['descripcion']) >= 60, 'Autor sin descripción')
        if a.get('nacimiento'):
            day(a['nacimiento'], 'nacimiento')
        day(a['fecha_verificacion'], 'autor verificado')
        require(a['fuentes'] and all(set(s) == {'titulo', 'url'} and s['titulo'] and https(s['url']) for s in a['fuentes']), 'Autor sin fuentes')
        names.add(a['nombre']); slugs.add(a['slug'])
    return payload['autores']


def author_url(a):
    return '/recomendaciones/autores/' + a['slug'] + '/'


def author_links(b, authors=None):
    authors = author_records() if authors is None else authors
    links = []
    for name in b['autores']:
        a = next((a for a in authors if a['nombre'] == name), None)
        links.append(f'<a href="{author_url(a)}" target="_blank" rel="noopener" aria-label="{esc(name)}: información y libros (otra pestaña)">{esc(name)} <span aria-hidden="true">↗</span></a>' if a else esc(name))
    return ', '.join(links)


def purchase_formats(b):
    return b.get('formatos_compra', [])


def render_filters(data):
    def select(key, label, options, extra=''):
        return f'<label>{label}<select name="{key}" data-filter="{key}" {extra}>' + ''.join(f'<option value="{esc(v)}"' + (f' id="{key}={esc(v)}"' if key in TYPES and v else '') + f'>{esc(t)}</option>' for v,t in options) + '</select></label>'
    controls = '<label class="catalogue-search">Buscar por título, autor o ISBN<input type="search" name="q" data-filter="q" maxlength="200" autocomplete="off" placeholder="¿Qué te apetece leer?"></label>'
    for kind, label in TYPES.items():
        choices = sorted((c for c in data['categorias'] if c['tipo'] == kind and c['activa']), key=lambda c: (c['orden'], c['id']))
        controls += select(kind, label, [('', 'Todas las opciones')] + [(c['id'], c['nombre']) for c in choices])
    controls += select('formato', 'Formato', [('', 'Todos los formatos')] + list(FORMATS.items()))
    controls += select('novedad', 'Novedades', [('', 'Cualquier fecha'), ('15', 'Novedad · menos de 15 días'), ('30', 'Últimos 30 días'), ('90', 'Últimos 90 días'), ('180', 'Últimos 180 días'), ('proximamente', 'Próximos 30 días')])
    advanced = '<div class="catalogue-filter-grid">'
    for key,label in [('desde', 'Publicado desde'), ('hasta', 'Publicado hasta')]:
        advanced += f'<label>{label}<input type="date" name="{key}" data-filter="{key}" min="1000-01-01" max="2100-12-31"></label>'
    for key,label in [('precio_min', 'Precio mínimo (€)'), ('precio_max', 'Precio máximo (€)')]:
        advanced += f'<label>{label}<input type="number" min="0" max="100000" step="0.01" inputmode="decimal" name="{key}" data-filter="{key}" data-market-control="offers" disabled></label>'
    advanced += select('descuento', 'Ofertas', [('', 'Todos los precios'), ('1', 'Con descuento'), ('10', '10 % o más'), ('25', '25 % o más'), ('50', '50 % o más')], 'data-market-control="offers" disabled')
    advanced += select('valoracion', 'Valoración de Goodreads', [('', 'Todas las valoraciones'), ('3', '3 estrellas o más'), ('4', '4 estrellas o más'), ('4.5', '4,5 estrellas o más')], 'data-market-control="ratings" disabled')
    advanced += '</div><p class="catalogue-data-note" data-market-note>Precios, ofertas y valoraciones: se mostrarán cuando haya datos contrastados y vigentes.</p>'
    return '<form class="catalogue-filters" data-catalogue-filters><fieldset disabled><legend>Encuentra tu próxima lectura</legend><div class="catalogue-filter-grid">' + controls + '</div><details class="catalogue-details catalogue-more-filters"><summary>Fechas, precios y valoraciones</summary>' + advanced + '</details><div class="catalogue-filter-actions"><button type="submit">Buscar libros</button><button type="reset" disabled>Restablecer</button></div></fieldset></form>'


def render_hub(data, books, template):
    cards = []
    for i,b in enumerate(books):
        cats = categories(data,b)
        formats = ' '.join(sorted(set([o['formato'] for o in purchase_formats(b)] + ([b['formato_edicion']] if b.get('formato_edicion') else []))))
        published = b.get('fecha_publicacion', '')
        year = b.get('anio_publicacion', '')
        attrs = f'data-catalogue-book data-book-id="{esc(b["id"])}" data-categories="{esc(" ".join(c["id"] for c in cats))}" data-search="{esc(b["titulo"] + " " + " ".join(b["autores"]) + " " + b.get("isbn13", ""))}" data-title="{esc(b["titulo"])}" data-author="{esc(", ".join(b["autores"]))}" data-formats="{formats}" data-published="{esc(published)}" data-published-month="{esc(b.get("fecha_publicacion_parcial", ""))}" data-year="{esc(year)}"'
        cards.append(f'<li class="catalogue-card" {attrs}><a class="catalogue-card__cover" href="{url(b)}" aria-label="Ver ficha de {esc(b["titulo"])}">{image(b,i>1)}</a><div><p class="eyebrow">{novelty(b, " · ".join(c["nombre"] for c in cats if c["tipo"]=="genero"))}</p><h3><a href="{url(b)}">{esc(b["titulo"])}</a></h3><p class="catalogue-author">{author_links(b)}</p><p class="catalogue-card__description">{esc(b["descripcion_breve"])}</p><p class="catalogue-card__meta">' + ' · '.join(esc(v) for v in [str(published or b.get('fecha_publicacion_parcial') or year) if published or b.get('fecha_publicacion_parcial') or year else '', b.get('edad_recomendada','')] if v) + f'</p><div class="catalogue-rating" data-rating-book="{esc(b["id"])}"></div><p data-price-book="{esc(b["id"])}" class="catalogue-price" hidden></p><a class="text-action" href="{url(b)}">Ver ficha del libro</a></div></li>')
    sort = '<label>Ordenar por<select name="orden" data-filter="orden" form="catalogue-search-form" disabled><option value="editorial">Selección editorial</option><option value="titulo">Título · A–Z</option><option value="titulo_desc">Título · Z–A</option><option value="autor">Autor · A–Z</option><option value="fecha_desc">Publicación · más reciente</option><option value="fecha_asc">Publicación · más antigua</option><option value="precio_asc" data-sort-market="offers" disabled>Precio · menor a mayor</option><option value="precio_desc" data-sort-market="offers" disabled>Precio · mayor a menor</option><option value="valoracion_desc" data-sort-market="ratings" disabled>Valoración · mayor a menor</option></select></label>'
    filters = render_filters(data).replace('<form class=', '<form id="catalogue-search-form" class=',1)
    catalogue = '<section class="catalogue-section" id="catalogo" aria-label="Buscar libros recomendados">' + filters + '<div class="catalogue-results-head"><h2>El catálogo</h2>' + sort + f'<p role="status" aria-live="polite" data-catalogue-count>{len(books)} ' + ('libro' if len(books)==1 else 'libros') + '</p></div><ul class="catalogue-grid">' + ''.join(cards) + '</ul><div class="catalogue-empty" data-catalogue-empty' + (' hidden' if books else '') + '><h2>' + ('No hay libros con estos filtros' if books else 'Estamos preparando la selección') + '</h2><p>Prueba con otros filtros o restablece la búsqueda.</p><a class="text-action" href="/cuaderno/#lecturas">Explorar las guías de lectura</a></div><noscript><p>Puedes consultar todas las fichas sin JavaScript. Los filtros requieren activarlo.</p></noscript></section>'
    page=template.replace('{{catalogue}}',catalogue)
    if books:
        schema={'@context':'https://schema.org','@type':'ItemList','@id':SITE+'/recomendaciones/#catalogo','name':'Libros recomendados','numberOfItems':len(books),'itemListElement':[{'@type':'ListItem','position':i+1,'item':{'@type':'Book','@id':SITE+url(b)+'#book','name':b['titulo'],'url':SITE+url(b),'image':SITE+b['portada_local']}} for i,b in enumerate(books)]}
        page=page.replace('</head>','<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')+'</script>\n</head>')
    return inject_shell_auto(page)


def render_book(data,b,template):
    canonical=SITE+url(b)
    title=book_title(b)
    description=b['descripcion_breve']
    cats=categories(data,b)
    rows=[('Edición',b['edicion']),('Editorial',b.get('editorial')),('Publicación',b.get('fecha_publicacion') or b.get('fecha_publicacion_parcial') or b.get('anio_publicacion')),('ISBN-13',b.get('isbn13')),('Idioma',b.get('idioma')),('Páginas',b.get('numero_paginas')),('Edad orientativa',b.get('edad_recomendada'))]
    details='<details class="catalogue-details"><summary>Datos de esta edición</summary><dl>'+''.join(f'<dt>{esc(k)}</dt><dd>' + (f'<a href="/editoriales/{esc(b["editorial_slug"])}/">{esc(v)}</a>' if k == 'Editorial' and b.get('editorial_slug') else esc(v)) + '</dd>' for k,v in rows if v)+'</dl></details>'
    fragment=''
    if b.get('fragmento_url'):
        fragment='<details class="catalogue-details catalogue-fragment"><summary>Leer un fragmento gratuito</summary>'
        if b.get('fragmento_texto') and b.get('fragmento_uso_autorizado') is True:
            fragment+=''.join('<p>'+esc(p)+'</p>' for p in b['fragmento_texto'].split('\n\n') if p.strip())
        if b.get('audio_fragmento'):
            fragment+='<p>Escuchar el fragmento</p><audio controls preload="none" aria-label="Escuchar el fragmento de '+esc(b['titulo'])+'"><source src="'+esc(b['audio_fragmento'])+'" type="audio/mpeg"></audio>'
        fragment+='<a class="text-action" href="'+esc(b['fragmento_url'])+'" target="_blank" rel="noopener noreferrer">Abrir el primer capítulo en la fuente oficial</a></details>'
    extra=''
    if b.get('resenas'):
        extra+='<details class="catalogue-details"><summary>'+('Buscar reseñas' if all(r['url'].startswith('https://www.goodreads.com/search?') for r in b['resenas']) else 'Reseñas externas ('+str(len(b['resenas']))+')')+'</summary><ul>'+''.join(f'<li><a href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">{esc(r["titulo"])}</a></li>' for r in b['resenas'])+'</ul></details>'
    extra+='<details class="catalogue-details"><summary>Fuentes de la edición y la portada</summary><ul>'+f'<li><a href="{esc(b["fuente_bibliografica_url"])}" target="_blank" rel="noopener noreferrer">Ficha editorial</a></li><li><a href="{esc(b["portada_fuente_url"])}" target="_blank" rel="noopener noreferrer">Portada: {esc(b.get("editorial") or "fuente editorial")}</a></li>'
    for key,label in [('fuente_publicacion_url','Fecha de publicación'),('fuente_edad_url','Orientación de edad')]:
        if b.get(key):
            extra+=f'<li><a href="{esc(b[key])}" target="_blank" rel="noopener noreferrer">{label}</a></li>'
    extra+='</ul></details>'
    options=purchase_formats(b)
    buy=''
    if options:
        buy='<details class="catalogue-details catalogue-buy"><summary>Comprar en Amazon <span>Elegir formato</span></summary><ul>'+''.join(f'<li><a class="catalogue-buy-link" data-purchase-format="{o["formato"]}" href="{esc(o["url"])}" target="_blank" rel="sponsored nofollow noopener noreferrer">{FORMATS[o["formato"]]} <span aria-hidden="true">↗</span></a></li>' for o in options)+'</ul></details>'
    elif b.get('url_amazon_afiliada'):
        buy=f'<a class="catalogue-buy-link" href="{esc(b["url_amazon_afiliada"])}" target="_blank" rel="sponsored nofollow noopener noreferrer">Ver en Amazon <span aria-hidden="true">↗</span></a>'
    elif b.get('amazon_busqueda_isbn'):
        buy=f'<a class="catalogue-buy-link" href="{esc(b["amazon_busqueda_isbn"])}" target="_blank" rel="sponsored nofollow noopener noreferrer">Buscar este ISBN en Amazon <span aria-hidden="true">↗</span></a>'
    cover=image(b, sizes='(max-width: 600px) 65vw, 400px')
    if b.get('url_amazon_afiliada'):
        cover='<a href="'+esc(b['url_amazon_afiliada'])+'" aria-label="Ver '+esc(b['titulo'])+' en Amazon" target="_blank" rel="sponsored nofollow noopener noreferrer">'+cover+'</a>'
    speech='<div class="catalogue-speech" hidden><button type="button" data-catalogue-speak>Escuchar descripción</button> <button type="button" data-catalogue-stop disabled>Detener lectura</button><p role="status" data-catalogue-speech-status></p></div>'
    if b['id'].startswith('isbn-'):
        speech=''
    if b.get('audio_descripcion'):
        speech='<div class="catalogue-audio"><p>Escuchar la descripción</p><audio controls preload="none" aria-label="Escuchar la descripción de '+esc(b['titulo'])+'"><source src="'+esc(b['audio_descripcion'])+'" type="audio/mpeg"></audio></div>'
    main='<main id="contenido" tabindex="-1" class="v1-main reading-catalogue" data-family="recomendaciones" data-reading-catalogue><nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol><li><a href="/">Inicio</a></li><li><a href="/cuaderno/">Cuaderno</a></li><li><a href="/recomendaciones/">Libros recomendados</a></li><li aria-current="page">'+esc(b['titulo'])+'</li></ol></nav><article class="catalogue-book-layout"><div class="catalogue-cover-panel">'+cover+'</div><div><header class="catalogue-book-heading"><p class="eyebrow">'+novelty(b, "Libros recomendados")+'</p><h1>'+esc(b['titulo'])+'</h1><p class="catalogue-author">'+author_links(b)+'</p><div class="catalogue-rating" data-rating-book="'+esc(b['id'])+'"></div></header><p data-catalogue-description>'+esc(description)+'</p>'+speech+fragment+tags(cats)
    if b.get('autoria_propia'):
        main+='<p>Obra de David Porto Díaz.</p>'
    if b.get('avisos_contenido'):
        main+='<p><strong>Sobre el contenido:</strong> '+esc(b['avisos_contenido'])+'</p>'
    main+='<p data-price-book="'+esc(b['id'])+'" class="catalogue-price" hidden></p>'+buy+details+extra+'</div></article><div class="catalogue-end"><a class="text-action" href="/recomendaciones/">Volver al catálogo</a></div></main>'
    authors=author_records()
    schema={'@context':'https://schema.org','@graph':[{'@type':'Book','@id':canonical+'#book','url':canonical,'name':b['titulo'],'author':[{'@type':'Person','name':name,**({'@id':SITE+author_url(a)+'#person','url':SITE+author_url(a)} if (a:=next((a for a in authors if a['nombre']==name),None)) else {})} for name in b['autores']],'description':description,'image':SITE+b['portada_local'],'bookEdition':b['edicion'],**({'publisher':{'@type':'Organization','name':b['editorial'],**({'url':SITE+'/editoriales/'+b['editorial_slug']+'/'} if b.get('editorial_slug') else {})}} if b.get('editorial') else {}),**({'inLanguage':b['idioma']} if b.get('idioma') else {}),**({'numberOfPages':b['numero_paginas']} if b.get('numero_paginas') else {}),**({'bookFormat':'https://schema.org/'+{'tapa-dura':'Hardcover','tapa-blanda':'Paperback','ebook':'EBook','audiolibro':'AudiobookFormat'}[b['formato_edicion']]} if b.get('formato_edicion') else {}),**({'isbn':b['isbn13']} if b.get('isbn13') else {}),**({'datePublished':b['fecha_publicacion']} if b.get('fecha_publicacion') else {})},{'@type':'WebPage','@id':canonical+'#page','url':canonical,'name':title,'dateModified':b['fecha_actualizacion'],'mainEntity':{'@id':canonical+'#book'}},{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':label,'item':SITE+href} for i,(label,href) in enumerate([('Inicio','/'),('Cuaderno','/cuaderno/'),('Libros recomendados','/recomendaciones/'),(b['titulo'],url(b))])]}]}
    return render_detail_page(template,main,canonical,title,description,schema,b)


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
    for key,value in values.items():
        page=re.sub(r'(<meta (?:name|property)="'+re.escape(key)+r'" content=")[^"]*',lambda m:m[1]+esc(value),page)
    page=page.replace('href="'+SITE+'/recomendaciones/"','href="'+canonical+'"')
    page=re.sub(r'<script type="application/ld\+json">[\s\S]*?</script>',lambda _:'<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')+'</script>',page,count=1)
    return inject_shell_auto(page)


def render_author(a,data,books,template):
    selected=[b for b in books if a['nombre'] in b['autores']]
    canonical=SITE+author_url(a)
    main='<main id="contenido" tabindex="-1" class="v1-main reading-catalogue catalogue-author-page" data-family="recomendaciones"><nav class="book-breadcrumb" aria-label="Ruta de navegación"><ol><li><a href="/">Inicio</a></li><li><a href="/cuaderno/">Cuaderno</a></li><li><a href="/recomendaciones/">Libros recomendados</a></li><li aria-current="page">'+esc(a['nombre'])+'</li></ol></nav><header class="catalogue-author-hero"><p class="eyebrow">Autores · Cuaderno</p><h1>'+esc(a['nombre'])+'</h1><p>'+esc(a['descripcion'])+'</p></header><section aria-labelledby="author-books"><h2 id="author-books">Libros de '+esc(a['nombre'])+' en el catálogo</h2><ul class="catalogue-author-books">'+''.join('<li><a href="'+url(b)+'">'+image(b,True)+'<span>'+esc(b['titulo'])+'</span></a><p>'+esc(b['descripcion_breve'])+'</p></li>' for b in selected)+'</ul></section><details class="catalogue-details"><summary>Sobre estas fuentes</summary><ul>'+''.join('<li><a href="'+esc(s['url'])+'" target="_blank" rel="noopener noreferrer">'+esc(s['titulo'])+'</a></li>' for s in a['fuentes'])+'</ul><p>'+("Relación bibliográfica a partir de las fichas editoriales enlazadas." if a.get("tipo") == "bibliografico" else "Síntesis biográfica propia a partir de las fuentes enlazadas.")+'</p></details><div class="catalogue-end"><a class="text-action" href="/recomendaciones/">Explorar todos los libros</a></div></main>'
    schema={'@context':'https://schema.org','@graph':[{'@type':'Person','@id':canonical+'#person','name':a['nombre'],'url':canonical,**({'birthDate':a['nacimiento']} if a.get('nacimiento') else {}),'description':a['descripcion'],**({'sameAs':[s['url'] for s in a['fuentes']]} if a.get('tipo') != 'bibliografico' else {})},{'@type':'CollectionPage','@id':canonical,'url':canonical,'name':a['nombre']+' · '+('Libros y ediciones' if a.get('tipo') == 'bibliografico' else 'Biografía y libros'),'mainEntity':{'@id':canonical+'#person'},'hasPart':[{'@id':SITE+url(b)+'#book'} for b in selected]},{'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':label,'item':SITE+href} for i,(label,href) in enumerate([('Inicio','/'),('Cuaderno','/cuaderno/'),('Libros recomendados','/recomendaciones/'),(a['nombre'],author_url(a))])]}]}
    return render_detail_page(template,main,canonical,a['nombre']+' · '+('Libros y ediciones' if a.get('tipo') == 'bibliografico' else 'Biografía y libros')+' | David Porto Díaz',a['descripcion'],schema,selected[0] if selected else None)


def registry_entries(books):
    return [{"id": "reading-book-" + b["id"], "url": url(b), "label": b["titulo"], "shortLabel": b["titulo"], "type": "article", "territory": "cuaderno", "parentId": "recommendations-hub", "hubId": "notebook-hub", "discoverability": "secondary", "audience": ["reader"], "jobs": ["buscar-lecturas"], "sourceFile": url(b).lstrip('/') + 'index.html'} for b in books]


def render_map(original, books, authors=()):
    start, end = '<!-- reading-catalogue-map:start -->', '<!-- reading-catalogue-map:end -->'
    original = re.sub(re.escape(start) + r'[\s\S]*?' + re.escape(end) + r'\n?', '', original)
    if not books:
        return original
    links = ''.join(f'<li><a href="{url(b)}">{esc(b["titulo"])} — {esc(", ".join(b["autores"]))}</a></li>' for b in books)
    author_links = ''.join(f'<li><a href="{author_url(a)}">{esc(a["nombre"])}</a></li>' for a in authors if any(a['nombre'] in b['autores'] for b in books))
    block = start + '<section class="directory-section"><h2>Libros recomendados</h2><p><a href="/recomendaciones/">Explorar el catálogo de lectura</a></p><details class="directory-reading-books"><summary>Ver las fichas de lectura</summary><ul class="directory-list">' + links + '</ul></details></section>' + end + '\n'
    if author_links:
        block = block.replace('</section>', '<details class="directory-reading-books"><summary>Ver autores del catálogo</summary><ul class="directory-list">' + author_links + '</ul></details></section>')
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
        authors = author_records(root)
        template = (root / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
        outputs = {'recomendaciones/index.html': render_hub(data, books, template)}
        map_path = root / 'mapa-del-sitio/index.html'
        if map_path.exists():
            outputs['mapa-del-sitio/index.html'] = render_map(map_path.read_text(encoding='utf-8'), books, authors)
        for b in books:
            outputs[url(b).lstrip('/') + 'index.html'] = render_book(data, b, template)
        active_authors = [a for a in authors if any(a['nombre'] in b['autores'] for b in books)]
        for a in active_authors:
            outputs[author_url(a).lstrip('/') + 'index.html'] = render_author(a, data, books, template)
        existing = root / 'recomendaciones/libros'
        orphans = [p for p in existing.glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
        orphans += [p for p in (root / 'recomendaciones/autores').glob('*/index.html') if p.relative_to(root).as_posix() not in outputs]
        require(not orphans, 'Hay fichas existentes fuera de los datos: revisar retirada/URL antes de eliminarlas')
        registry = json.loads((root / 'data/content-registry.json').read_text(encoding='utf-8'))
        registry['entries'] = [e for e in registry['entries'] if not e['id'].startswith(('reading-book-', 'reading-author-'))] + registry_entries(books)
        registry['entries'] += [{'id': 'reading-author-' + a['slug'], 'url': author_url(a), 'label': a['nombre'], 'shortLabel': a['nombre'], 'type': 'article', 'territory': 'cuaderno', 'parentId': 'recommendations-hub', 'hubId': 'notebook-hub', 'discoverability': 'secondary', 'audience': ['reader'], 'jobs': ['buscar-lecturas'], 'sourceFile': author_url(a).lstrip('/') + 'index.html'} for a in active_authors]
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
