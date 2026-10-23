"""Sellos que aparecen en las fichas oficiales pero no en el directorio de editoriales.

El directorio (data/editoriales.json) trata de recepción de manuscritos; un sello como Debate
o Taurus puede publicar libros sin estar ahí. Estos sellos se registran aparte, con su fuente,
en data/reading-publishers.json y tienen su propia ficha dentro de «Libros recomendados».
Sin modelos ni costes; el nombre sale de la ficha oficial del libro.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from reading_intake_core import normalize_text

SMALL_WORDS = {'de', 'del', 'la', 'las', 'el', 'los', 'y', 'e', 'en', 'para', 'a'}
GROUPS = {'www.penguinlibros.com': 'Penguin Random House Grupo Editorial', 'www.planetadelibros.com': 'Grupo Planeta'}
_VALID_NAME = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 &.,'’·-]{1,58}\Z")
_GENERIC = {'editorial', 'varios', 'sin editorial', 'desconocida', 'n/a'}


def display_name(raw: str) -> str:
    """«PENGUIN CLÁSICOS» → «Penguin Clásicos»; las siglas cortas (DK, IJC) se conservan."""
    words = ' '.join(str(raw).split()).split(' ')
    out = []
    for i, word in enumerate(words):
        if word.isupper() and len(word) <= 3 and word.isalpha() and word.lower() not in SMALL_WORDS:
            out.append(word)
        elif i and word.lower() in SMALL_WORDS:
            out.append(word.lower())
        else:
            out.append(word[:1].upper() + word[1:].lower())
    return ' '.join(out)


def slugify(name: str) -> str:
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', normalize_text(name))).strip('-')[:60]


class PublisherError(ValueError):
    pass


def catalogue_publisher(raw_name: str, store: dict, source_url: str, today: str, *,
                        directory_names: set[str], directory_slugs: set[str]) -> dict:
    """Devuelve (y registra si falta) el sello del catálogo para `raw_name`.

    `directory_names` son los nombres/alias normalizados de TODO el directorio: si el nombre ya
    está ahí no se duplica (el sello debe resolverse por alias, no por una ficha nueva).
    """
    name = display_name(raw_name)
    key = normalize_text(name)
    if not key or key in _GENERIC or not _VALID_NAME.fullmatch(name):
        raise PublisherError('Nombre de sello no válido para una ficha automática')
    if key in directory_names:
        raise PublisherError('El sello ya existe en el directorio: añadir un alias en la configuración')
    host = urlsplit(source_url).hostname
    if host not in GROUPS:
        raise PublisherError('Fuente de sello no revisada')
    slug = slugify(name)
    if not slug or slug in directory_slugs:
        raise PublisherError('Identificador de sello ambiguo con el directorio')
    for item in store['editoriales']:
        if item['slug'] == slug:
            if normalize_text(item['nombre']) != key:
                raise PublisherError('Dos sellos distintos comparten identificador')
            if source_url not in {s['url'] for s in item['fuentes']} and len(item['fuentes']) < 5:
                item['fuentes'].append({'titulo': 'Ficha oficial de un libro del sello', 'url': source_url})
            return item
    item = {'slug': slug, 'nombre': name, 'grupo': GROUPS[host],
            'fuentes': [{'titulo': 'Ficha oficial de un libro del sello', 'url': source_url}],
            'fecha_verificacion': today}
    store['editoriales'].append(item)
    store['editoriales'].sort(key=lambda p: p['slug'])
    return item
