#!/usr/bin/env python3
"""Reviewed publisher metadata -> isolated validation -> existing catalogue.

No paid API, LLM, personal session or Amazon scraping. The caller builds and
checks the site, submits a generated-only PR and respects main's normal gates.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import io
import json
import re
import shutil
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from PIL import Image, ImageOps
from reading_editorial_sources import CachedHTTP, SourceError, penguin_edition, product_links, publisher_author_bio
from reading_intake_core import affiliate_destination, clean_title, normalize_text, publisher_slug
from reading_intake_fetch import read_json, write_if_changed
from reading_intake_publishers import resolve_publishers
from reading_taxonomy import extra_categories
from reading_catalogue_publishers import catalogue_publisher, PublisherError
from reading_generic_source import generic_edition, generic_links, reviewed_hosts
from reading_planeta_source import COVER_HOSTS as PLANETA_COVER_HOSTS, planeta_edition, planeta_links
from urllib.parse import urlsplit
from reading_author_wikipedia import WikipediaSummaries, fill_missing_bios

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('catalogue_builder', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

GENRES = {
    'poesia': ('poesia','Poesía'),
    'libros de poesia': ('poesia','Poesía'),
    'ensayo': ('ensayo','Ensayo'),
    'filosofia': ('filosofia','Filosofía'),
    'historia': ('historia','Historia'),
    'psicologia': ('psicologia','Psicología'),
    'divulgacion cientifica': ('divulgacion-cientifica','Divulgación científica'),
    'nutricion belleza y fitness': ('nutricion-y-bienestar','Nutrición y bienestar'),
    'comic y novela grafica': ('comic-y-novela-grafica','Cómic y novela gráfica'),
    'libros infantiles': ('infantil','Infantil'),
    'clasicos': ('clasicos','Clásicos'),
    'grandes clasicos': ('clasicos','Clásicos'),
    'literatura contemporanea': ('narrativa', 'Narrativa contemporánea'),
    'novela negra misterio y thriller': ('misterio-y-thriller', 'Misterio y thriller'),
    'libros de fantasia': ('fantasia', 'Fantasía'),
    'fantasia': ('fantasia', 'Fantasía'),
    'ciencia ficcion': ('ciencia-ficcion', 'Ciencia ficción'),
    'libros de ciencia ficcion': ('ciencia-ficcion', 'Ciencia ficción'),
    'novela romantica': ('romance', 'Romance'),
    'libros de amor': ('romance', 'Romance'),
    'romance': ('romance', 'Romance'),
    'novela historica': ('novela-historica', 'Novela histórica'),
    'libros de aventura': ('aventuras', 'Aventuras'),
    'terror': ('terror', 'Terror'),
    'libros de terror': ('terror', 'Terror'),
    'relatos': ('relatos', 'Relatos'),
    'novela juvenil': ('narrativa-juvenil', 'Narrativa juvenil'),
    'literatura juvenil': ('narrativa-juvenil', 'Narrativa juvenil'),
    'libros juveniles': ('narrativa-juvenil', 'Narrativa juvenil'),
    'aventuras': ('aventuras', 'Aventuras'),
    'biografias y memorias': ('biografias-y-memorias', 'Biografías y memorias'),
    'autoayuda': ('desarrollo-personal', 'Desarrollo personal'),
    'familia y crianza': ('familia-y-crianza', 'Familia y crianza'),
    'cocina': ('cocina', 'Cocina'),
}


def slug(value):
    return normalize_text(value).replace(' ', '-')[:75].strip('-')


def work_key(title, authors):
    # Remove edition labels only, never volume numbers or meaningful subtitles.
    title = re.sub(r'\([^)]*(?:edici[oó]n|tapa dura|tapa blanda|cantos)[^)]*\)', '', title, flags=re.I)
    return normalize_text(title), tuple(sorted(normalize_text(a) for a in authors))


def classify(record, catalogue):
    found = []
    cats = {c['id']: c for c in catalogue['categorias']}
    for subject in record['materias']:
        key = normalize_text(subject)
        band = re.fullmatch(r'(?:de \d+ a \d+ anos|a partir de \d+ anos)', key)
        if band:
            # La «materia» de los libros infantiles de Penguin es su franja de edad.
            mapped = ('infantil', 'Infantil y juvenil')
            age_id, age_name = 'edad-' + key.replace(' ', '-'), ' '.join(str(subject).split())
            if age_id not in cats:
                catalogue['categorias'].append({'id': age_id, 'slug': age_id, 'nombre': age_name, 'tipo': 'edad',
                                                'descripcion': 'Edad orientativa de la editorial: ' + age_name + '.',
                                                'orden': 150 + len(cats), 'activa': True})
                cats[age_id] = catalogue['categorias'][-1]
            found.append(age_id)
        else:
            mapped = GENRES.get(key)
        if not mapped:
            # Preserve the source's actual subject even when it is new to the
            # catalogue. Age is never used as a substitute for a subject.
            name = ' '.join(str(subject).split())
            if not name or normalize_text(name) in {'adultos', 'juvenil', 'libros', 'inicio'}:
                continue
            topic_slug=slug(name)
            if len(normalize_text(name).replace(' ','-'))>75:
                topic_slug=topic_slug[:65]+'-'+hashlib.sha256(normalize_text(name).encode()).hexdigest()[:8]
            mapped = ('tema-' + topic_slug, name)
        ident, name = mapped
        if ident not in cats:
            c = {'id': ident, 'slug': ident, 'nombre': name, 'tipo': 'tematica' if ident.startswith('tema-') else 'genero',
                 'descripcion': 'Clasificación editorial: ' + name + '.',
                 'orden': 150 + len(cats), 'activa': True}
            catalogue['categorias'].append(c)
            cats[ident] = c
        found.append(ident)
    for ident, name, kind in extra_categories(record):
        if ident not in cats:
            c = {'id': ident, 'slug': ident, 'nombre': name, 'tipo': kind,
                 'descripcion': 'Clasificación editorial: ' + name + '.',
                 'orden': 150 + len(cats), 'activa': True}
            catalogue['categorias'].append(c)
            cats[ident] = c
        found.append(ident)
    if not found:
        raise SourceError('Materia editorial no clasificada; queda pendiente')
    age = normalize_text(record.get('edad_recomendada', ''))
    if age == 'adultos':
        found.append('adultos')
    elif 'juvenil' in age or age in ('a partir de 12 anos', 'a partir de 14 anos', 'a partir de 16 anos'):
        found.append('juvenil')
    if not found:
        raise SourceError('Materia editorial no clasificada; queda pendiente')
    return list(dict.fromkeys(found))


def make_book(record, publisher, tag, today, cover, dimensions):
    ident = record['isbn13']
    description = f'{clean_title(record["titulo"])}, de {", ".join(record["autores"])}. '
    description += f'Edición de {publisher["name"]} en castellano, en {record["encuadernacion"].lower()}.'
    if record.get('numero_paginas'):
        description += f' Consta de {record["numero_paginas"]} páginas.'
    subject = ', '.join(record['materias'])
    if subject:
        description += f' La editorial la incluye en {subject.lower()}.'
    published = record['fecha_publicacion_edicion']
    description += f' Publicación editorial: {published}.'
    book = {
        'id': 'isbn-' + ident, 'slug': slug(clean_title(record['titulo'])) + '-' + ident,
        'titulo': clean_title(record['titulo']), 'autores': record['autores'], 'estado': 'publicado',
        'descripcion_breve': description, 'descripcion_original_confirmada': True,
        'isbn13': ident, 'editorial': publisher['name'],
        **({'editorial_catalogo_slug': publisher['slug']} if publisher.get('catalogo') else {'editorial_slug': publisher['slug']}),
        'idioma': 'es', 'formato_edicion': record['formato_edicion'],
        'edicion': record['encuadernacion'] + ' · ' + publisher['name'],
        'portada_local': cover, 'portada_ancho': dimensions[0], 'portada_alto': dimensions[1],
        'portada_fuente_url': record['portada_fuente_url'], 'portada_edicion_verificada': True,
        'autorizacion_o_base_uso': record['cover_use_basis'], 'portada_fecha_revision': today,
        'fuente_bibliografica_url': record['fuente_bibliografica_url'],
        'fuente_publicacion_url': record['fuente_bibliografica_url'],
        'fecha_verificacion': today, 'fecha_actualizacion': today,
        'anio_publicacion': int(published[:4]),
        'amazon_busqueda_isbn': affiliate_destination(ident, tag)['url'],
        'resenas': [{'titulo': 'Buscar reseñas en Goodreads', 'url': 'https://www.goodreads.com/search?' + urlencode({'q': ident}), 'fecha_verificacion': today}],
    }
    if record['precision_fecha'] == 'dia':
        book['fecha_publicacion'] = published
    elif record['precision_fecha'] == 'mes':
        book['fecha_publicacion_parcial'] = published
    if record.get('numero_paginas'):
        book['numero_paginas'] = record['numero_paginas']
    if record.get('pvp_centimos'):
        book.update(pvp_centimos=record['pvp_centimos'], pvp_fecha_verificacion=today)
    if record.get('edad_recomendada'):
        book['edad_recomendada'] = record['edad_recomendada']
        book['fuente_edad_url'] = record['fuente_bibliografica_url']
    if record.get('sinopsis_breve'):
        book.update(sinopsis_breve=record['sinopsis_breve'],
                    sinopsis_fuente_url=record['fuente_bibliografica_url'],
                    sinopsis_tipo='extracto_editorial')
    return book


def cover_bytes(raw):
    with Image.open(io.BytesIO(raw)) as image:
        if image.width < 320 or image.height < 400 or image.width * image.height > 30_000_000 or not .4 < image.width / image.height < .9:
            raise SourceError('Cubierta ausente, pequeña o proporción incompatible')
        image = ImageOps.exif_transpose(image).convert('RGB')
        image.thumbnail((800, 1300))
        out = io.BytesIO()
        image.save(out, 'WEBP', quality=82, method=6)
        dimensions = image.size
        small = image.copy()
        small.thumbnail((320, 600))
        preview = io.BytesIO()
        small.save(preview, 'WEBP', quality=80, method=6)
        return out.getvalue(), preview.getvalue(), dimensions


def update_authors(payload, catalogue, new_books, today):
    known = {a['nombre']: a for a in payload['autores']}
    used = {a['slug'] for a in payload['autores']}
    for book in new_books:
        for name in book['autores']:
            if name in known and known[name].get('tipo') != 'bibliografico':
                continue  # Manual biography and birth date are pinned.
            authors_books = [b for b in catalogue['libros'] if name in b['autores'] and b['estado'] == 'publicado']
            old = known.get(name)
            key = old['slug'] if old else slug(name)
            if key in used and not old:
                key += '-' + hashlib.sha256(name.encode()).hexdigest()[:8]
            titles = '; '.join(b['titulo'] for b in authors_books[:4])
            record = {'slug': key, 'nombre': name, 'tipo': 'bibliografico',
                      'descripcion': f'Libros de {name} incluidos en este catálogo: {titles}. Consulta sus ediciones, fechas de publicación y fichas editoriales en los enlaces de cada libro.',
                      'fuentes': [{'titulo': b['titulo'] + ' · ficha editorial', 'url': b['fuente_bibliografica_url']} for b in authors_books[:8]],
                      'fecha_verificacion': today}
            if old:
                old.update(record)
            else:
                payload['autores'].append(record)
            known[name] = old if old else record
            used.add(key)


def enrich_author_bios(authors, state, http, today, max_profiles=7):
    """Cover five new authors plus two refreshes within the shared HTTP budget."""
    sources = {}
    for item in state.get('items', {}).values():
        for name, source in (item.get('datos') or {}).get('fuentes_autores', {}).items():
            if re.fullmatch(r'https://www\.penguinlibros\.com/es/\d+-[a-z0-9-]+', source):
                sources[name] = source
    changed, attempted = 0, 0
    for author in sorted(authors['autores'], key=lambda a: (
            a.get('biografia_fecha_revision', ''),
            hashlib.sha256((today + a['nombre']).encode()).hexdigest())):
        source = sources.get(author['nombre'], '')
        if author.get('tipo') != 'bibliografico' or not re.fullmatch(r'https://www\.penguinlibros\.com/es/\d+-[a-z0-9-]+', source):
            continue
        reviewed = author.get('biografia_fecha_revision')
        if reviewed and (date.fromisoformat(today) - date.fromisoformat(reviewed)).days < 30:
            continue
        if attempted >= max_profiles or http.requests >= http.budget:
            break
        attempted += 1
        try:
            document = http.get(source, ttl=30 * 86400).decode('utf-8', errors='replace')
            biography = publisher_author_bio(document, source, author['nombre'])
            author.update(biografia_breve=biography, biografia_fuente_url=source,
                          biografia_fecha_revision=today)
            changed += 1
        except (OSError, ValueError, TimeoutError):
            continue  # A missing optional biography never blocks the books.
    return changed


def author_identity_conflicts(record,state):
    """A shared display name must not silently join two editorial profiles."""
    profile=re.compile(r'https://www\.penguinlibros\.com/es/\d+-[a-z0-9-]+\Z')
    known={}
    for item in state.get('items',{}).values():
        if item.get('estado_ingesta')!='publicado':
            continue
        for name,source in (item.get('datos') or {}).get('fuentes_autores',{}).items():
            if profile.fullmatch(source):
                known.setdefault(name,set()).add(source)
    return [name for name,source in record.get('fuentes_autores',{}).items()
            if profile.fullmatch(source) and name in known and source not in known[name]]


REVIEWED_PROVIDERS = {'penguin': ['www.penguinlibros.com'], 'planeta': ['www.planetadelibros.com']}


def provider_of(url, providers):
    host = urlsplit(url).hostname
    return next((s for s in providers if host in s['hosts']), None)


def reviewed_source(source):
    """Un conector solo se ejecuta con los hosts que están revisados en el código."""
    if source['provider'] == 'generic':
        reviewed_hosts(source)
        return True
    return REVIEWED_PROVIDERS.get(source['provider']) == source['hosts']


def discover_links(source, document, index):
    if source['provider'] == 'generic':
        return generic_links(source, document, index)
    return planeta_links(document, index) if source['provider'] == 'planeta' else product_links(document, index)


def read_edition(source, document, url):
    if source['provider'] == 'generic':
        return generic_edition(source, document, url)
    return planeta_edition(document, url) if source['provider'] == 'planeta' else penguin_edition(document, url)


def ingest(config, root, cache, *, max_new=None, max_requests=None, apply=False, today=None):
    today = today or datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    day = date.fromisoformat(today)
    if config.get('schema_version') != 1 or not config.get('enabled'):
        raise SourceError('La ingesta editorial no está habilitada')
    providers = [p for p in config['sources'] if p.get('enabled')]
    if not all(reviewed_source(p) for p in providers):
        raise SourceError('Conector editorial no revisado')
    fetch_hosts = [h for p in providers for h in p['hosts']] + (list(PLANETA_COVER_HOSTS) if any(p['provider'] == 'planeta' for p in providers) else []) + [h for p in providers if p['provider'] == 'generic' for h in p['cover_hosts']]
    http = CachedHTTP(cache / 'http', fetch_hosts, budget=max_requests or config['max_requests'], delay=config['request_delay_seconds'])
    catalogue = read_json(root / 'data/reading-catalogue.json')
    authors = read_json(root / 'data/reading-authors.json')
    registry = read_json(root / 'data/editoriales.json')
    catalogue_publishers = read_json(root / 'data/reading-publishers.json', {'schema_version': 1, 'editoriales': []})
    directory_names = {normalize_text(n) for p in registry.get('publishers', []) for n in (p.get('name', ''), re.sub(r'^(?:Editorial|Ediciones)\s+', '', p.get('name', ''), flags=re.I))}
    for override in config.get('publisher_aliases', []):
        directory_names |= {normalize_text(a) for a in override.get('aliases', [])}
    directory_slugs = {p.get('slug') for p in registry.get('publishers', [])}
    allowed = resolve_publishers(registry, config.get('publisher_aliases', []))
    publishers = {p['slug']: p for p in allowed}
    existing = {b.get('isbn13') for b in catalogue['libros']}
    by_isbn = {b.get('isbn13'): b for b in catalogue['libros']}
    known_urls = {b['fuente_bibliografica_url']: b['isbn13'] for b in catalogue['libros'] if b.get('fuente_bibliografica_url')}
    works = {work_key(b['titulo'], b['autores']) for b in catalogue['libros']}
    state = read_json(root / 'data/reading-intake-state.json', {'schema_version': 1, 'items': {}})
    cached_state = read_json(cache / 'state.json', {'schema_version': 1, 'items': {}})
    # Pending attempts survive in Actions cache; only published content is Git authority.
    for key, value in cached_state['items'].items():
        if key not in state['items']:
            state['items'][key] = value
    stats = {'discovered': 0, 'examined': 0, 'accepted': 0, 'updated': 0, 'already_published': 0, 'pending': 0, 'publishers': {}, 'errors': []}
    queue = {}
    # Revisit at most two older automatic entries per run; manual books stay pinned.
    for book in sorted(catalogue['libros'], key=lambda b: b.get('fecha_verificacion', '')):
        if book['id'].startswith('isbn-') and (day - date.fromisoformat(book['fecha_verificacion'])).days >= 7:
            source = provider_of(book['fuente_bibliografica_url'], providers)
            if source and len(queue) < 2:
                queue[book['fuente_bibliografica_url']] = source
    refresh_urls = set(queue)
    for source in providers:
        for index in source['index_urls']:
            try:
                document = http.get(index, ttl=12 * 3600).decode('utf-8')
                for url in discover_links(source, document, index):
                    queue.setdefault(url, source)
            except (OSError, ValueError, TimeoutError) as exc:
                stats['errors'].append({'source': source['id'], 'error': str(exc)[:180]})
    stats['discovered'] = len(queue)
    if not queue:
        # Leave book data untouched; independent providers still refresh daily.
        stats.update(status='editorial_unavailable', requests=http.requests, cache_hits=http.hits)
        return {'schema_version':1, 'generated_at':datetime.now(ZoneInfo('Europe/Madrid')).isoformat(),
                'mode':'applied' if apply else 'dry-run', 'stats':stats,
                'new_books':[], 'updated_books':[], 'state':state}
    new_books = []
    updated_books = []
    assets = {}
    limit = max_new or config['max_new_books']
    with tempfile.TemporaryDirectory(prefix='reading-intake-') as directory:
        validation_root = Path(directory)
        for publisher in allowed:
            target = validation_root / 'editoriales' / publisher['slug'] / 'index.html'
            if (root / 'editoriales' / publisher['slug'] / 'index.html').is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch()
        for folder in ('reading-covers', 'reading-audio'):
            source_dir = root / 'assets' / folder
            if source_dir.exists():
                shutil.copytree(source_dir, validation_root / 'assets' / folder)
        # Primero las revisiones; después, por turnos entre fuentes (el índice de una editorial grande
        # no deja sin sitio a las pequeñas) y, dentro de cada fuente, en un orden fijo por día.
        by_source = {}
        for url, source in sorted(queue.items(), key=lambda item: hashlib.sha256((today + item[0]).encode()).hexdigest()):
            by_source.setdefault(source['id'], []).append((url, source))
        rank = {url: position for entries in by_source.values() for position, (url, _) in enumerate(entries)}
        ordered = sorted(queue.items(), key=lambda item: (
            item[0] not in refresh_urls, rank[item[0]],
            hashlib.sha256((today + item[0]).encode()).hexdigest()))
        for url, source in ordered:
            if len(new_books) >= limit or http.requests >= http.budget:
                break
            # Penguin lleva el ISBN en la URL; Planeta no: se conoce por una ficha ya publicada o se lee de la propia ficha.
            isbn = url.rsplit('-', 1)[-1].rstrip('/') if source['provider'] == 'penguin' else known_urls.get(url)
            old_book = by_isbn.get(isbn)
            refresh = bool(old_book and url in refresh_urls)
            if isbn in existing and not refresh:
                stats['already_published'] += 1
                continue
            key = 'isbn13:' + isbn if isbn else 'url:' + url
            previous = state['items'].get(key, {})
            if previous.get('retry_after', '') > today:
                continue
            stats['examined'] += 1
            if stats['examined'] % 10 == 0:
                print(f'Ingesta: {stats["examined"]} candidatos revisados; {len(new_books)} aceptados', file=sys.stderr, flush=True)
            record = None
            try:
                record = read_edition(source, http.get(url, ttl=7 * 86400).decode('utf-8', errors='replace'), url)
                if not isbn:
                    isbn = record['isbn13']
                    known_urls[url] = isbn
                    key = 'isbn13:' + isbn
                    previous = state['items'].get(key, {})
                    old_book = by_isbn.get(isbn)
                    refresh = bool(old_book and url in refresh_urls)
                    if isbn in existing and not refresh:
                        stats['already_published'] += 1
                        stats['examined'] -= 1
                        continue
                if not record.get('sinopsis_breve'):
                    raise SourceError('Sinopsis editorial ausente; se conserva la ficha anterior o queda pendiente')
                if author_identity_conflicts(record,state):
                    raise SourceError('Autor homónimo o perfil editorial distinto; requiere desambiguación')
                record['cover_use_basis'] = source['cover_use_basis']
                canonical_publisher = publisher_slug(record['editorial'], allowed)
                catalogue_only = None
                if not canonical_publisher:
                    # Sello fuera del directorio de manuscritos: ficha propia del catálogo, con fuente.
                    try:
                        catalogue_only = catalogue_publisher(record['editorial'], catalogue_publishers, url, today,
                                                             directory_names=directory_names, directory_slugs=directory_slugs)
                    except PublisherError as exc:
                        raise SourceError('Sello no presente en el registro editorial de la web: ' + str(exc))
                    canonical_publisher = catalogue_only['slug']
                    publishers = {**publishers, canonical_publisher: {'name': catalogue_only['nombre'], 'slug': canonical_publisher, 'catalogo': True}}
                record['editorial_slug'] = canonical_publisher
                # Source dates are edition dates. Unknown precision never becomes a day.
                if record['precision_fecha'] == 'dia':
                    delta = (day - date.fromisoformat(record['fecha_publicacion_edicion'])).days
                    if delta > config['lookback_days'] or delta < -config['preorder_days']:
                        raise SourceError('Edición fuera de la ventana de selección configurada')
                if normalize_text(record['titulo']).startswith(('estuche ', 'pack ', 'caja ')):
                    raise SourceError('Estuche o pack: requiere relación de obras comprobada')
                work = work_key(record['titulo'], record['autores'])
                if work in works and (not refresh or work != work_key(old_book['titulo'], old_book['autores'])):
                    raise SourceError('Otra edición de una obra ya incluida; no se duplica la URL')
                # Isolate taxonomy changes and validate the entire proposed catalogue.
                trial = copy.deepcopy(catalogue)
                categories = classify(record, trial)
                if refresh:
                    if record['autores'] != old_book['autores'] or record['portada_fuente_url'] != old_book['portada_fuente_url']:
                        raise SourceError('Cambio de autoría o cubierta: requiere revisión editorial')
                    image = (root / old_book['portada_local'].lstrip('/')).read_bytes()
                    preview_path = root / old_book['portada_local'].lstrip('/').replace('.webp', '-320.webp')
                    small = preview_path.read_bytes()
                    dimensions = (old_book['portada_ancho'], old_book['portada_alto'])
                else:
                    image, small, dimensions = cover_bytes(http.get(record['portada_fuente_url'], ttl=30 * 86400))
                path = '/assets/reading-covers/isbn-' + isbn + '.webp'
                mini = path.replace('.webp', '-320.webp')
                (validation_root / 'data').mkdir(parents=True, exist_ok=True)
                (validation_root / 'data/reading-publishers.json').write_text(json.dumps(catalogue_publishers), encoding='utf-8')
                for relative, content in ((path, image), (mini, small)):
                    dest = validation_root / relative.lstrip('/')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(content)
                book = make_book(record, publishers[canonical_publisher], config['amazon_partner_tag'], today, path, dimensions)
                if refresh:
                    book['id'], book['slug'] = old_book['id'], old_book['slug']
                    for field in ('resenas', 'formatos_compra', 'url_amazon_afiliada', 'fragmento_url', 'fragmento_texto', 'fragmento_uso_autorizado', 'fragmento_base_uso', 'audio_fragmento', 'avisos_contenido', 'lectura_personal_confirmada', 'evidencia_lectura', 'autoria_propia', 'categorias_excluidas'):
                        if field in old_book:
                            book[field] = old_book[field]
                    changed = any(book.get(k) != old_book.get(k) for k in set(book) - {'fecha_verificacion', 'portada_fecha_revision', 'fecha_actualizacion'})
                    if not changed:
                        book['fecha_actualizacion'] = old_book['fecha_actualizacion']
                    if book['descripcion_breve'] == old_book['descripcion_breve']:
                        for field in ('audio_descripcion', 'audio_voz'):
                            if field in old_book:
                                book[field] = old_book[field]
                    trial['libros'] = [book if b['id'] == old_book['id'] else b for b in trial['libros']]
                    # Refresh is additive: preserve editorial tags assigned on
                    # the website rather than rebuilding them from the source.
                    categories = list(dict.fromkeys([
                        *(r['categoria_id'] for r in trial['libro_categorias'] if r['libro_id'] == book['id']),
                        *categories,
                    ]))
                    categories = [c for c in categories if c not in old_book.get('categorias_excluidas', [])]
                    if old_book.get('sinopsis_tipo') == 'resumen_propio':
                        for field in ('sinopsis_breve', 'sinopsis_fuente_url', 'sinopsis_tipo'):
                            book[field] = old_book[field]
                    trial['libro_categorias'] = [r for r in trial['libro_categorias'] if r['libro_id'] != book['id']]
                else:
                    trial['libros'].append(book)
                trial['libro_categorias'] += [{'libro_id': book['id'], 'categoria_id': c} for c in categories]
                builder.validate(trial, validation_root)
                catalogue = trial
                assets[path] = image
                assets[mini] = small
                (updated_books if refresh else new_books).append(book)
                existing.add(isbn)
                works.add(work)
                state['items'][key] = {'isbn13': isbn, 'estado_ingesta': 'publicado', 'primera_deteccion': previous.get('primera_deteccion', today), 'publicado_en': previous.get('publicado_en', today), 'libro_id': book['id'], 'datos': record}
                stats['publishers'][canonical_publisher] = stats['publishers'].get(canonical_publisher, 0) + 1
            except (OSError, ValueError, KeyError, TypeError, TimeoutError) as exc:
                reason = str(exc)[:220]
                if refresh:
                    state['items'][key] = {**previous, 'retry_after': (day + timedelta(days=3)).isoformat(), 'ultima_revision_error': reason}
                else:
                    state['items'][key] = {'isbn13': isbn, 'estado_ingesta': 'pendiente_datos', 'primera_deteccion': previous.get('primera_deteccion', today), 'retry_after': (day + timedelta(days=3)).isoformat(), 'motivo': reason, 'fuente': url, **({'datos': record} if record else {})}
                stats['pending'] += 1
        update_authors(authors, catalogue, new_books + updated_books, today)
        stats['author_profiles_updated'] = enrich_author_bios(authors, state, http, today)
        wiki = config.get('author_wikipedia', {})
        if wiki.get('enabled'):
            # Alternativa abierta para autores sin ficha biográfica editorial (p. ej. clásicos).
            stats['author_profiles_updated'] += fill_missing_bios(authors, WikipediaSummaries(budget=int(wiki.get('requests_per_run', 10))), today)
        builder.validate(catalogue, validation_root)
    stats['accepted'] = len(new_books)
    stats['updated'] = len(updated_books)
    stats['requests'], stats['cache_hits'] = http.requests, http.hits
    write_if_changed(cache / 'state.json', state)
    if apply and (new_books or updated_books or stats['author_profiles_updated']):
        write_if_changed(root / 'data/reading-publishers.json', catalogue_publishers)
        for relative, content in assets.items():
            target = root / relative.lstrip('/')
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != content:
                raise SourceError('La cubierta existente está fijada; no se sobrescribe')
            target.write_bytes(content)
        if config.get('generate_audio'):
            from reading_audio import narrate
            for book in new_books:
                try:
                    narrate(book, root)
                except Exception as exc:
                    stats['errors'].append({'book': book['id'], 'optional_audio': type(exc).__name__})
                    break  # An unavailable optional provider is tried only once per batch.
        builder.validate(catalogue, root)
        write_if_changed(root / 'data/reading-catalogue.json', catalogue)
        write_if_changed(root / 'data/reading-authors.json', authors)
        write_if_changed(root / 'data/reading-intake-state.json', state)
    return {'schema_version': 1, 'generated_at': datetime.now(ZoneInfo('Europe/Madrid')).isoformat(), 'mode': 'applied' if apply else 'dry-run', 'stats': stats, 'updated_books': [b['id'] for b in updated_books], 'new_books': [{'id': b['id'], 'isbn13': b['isbn13'], 'titulo': b['titulo'], 'editorial': b['editorial'], 'url': builder.url(b)} for b in new_books], 'state': state}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--live', action='store_true')
    p.add_argument('--apply', action='store_true')
    p.add_argument('--config', type=Path, default=ROOT / 'data/reading-intake-config.json')
    p.add_argument('--cache', type=Path, default=ROOT / '.ci/reading-editorial-cache')
    p.add_argument('--report', type=Path, default=ROOT / '.ci/reading-intake/publisher-report.json')
    p.add_argument('--max-new', type=int)
    p.add_argument('--max-requests', type=int)
    args = p.parse_args()
    if not args.live:
        p.error('La red requiere --live; las pruebas utilizan fixtures offline')
    if args.max_new is not None and not 1 <= args.max_new <= 25:
        p.error('--max-new debe estar entre 1 y 25')
    if args.max_requests is not None and not 1 <= args.max_requests <= 160:
        p.error('--max-requests debe estar entre 1 y 160')
    try:
        report = ingest(read_json(args.config), ROOT, args.cache, max_new=args.max_new, max_requests=args.max_requests, apply=args.apply)
        write_if_changed(args.report, report)
        print(json.dumps(report['stats'], ensure_ascii=True))
        return 0
    except (OSError, ValueError, KeyError, TimeoutError) as exc:
        print('Ingesta detenida sin publicación: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
