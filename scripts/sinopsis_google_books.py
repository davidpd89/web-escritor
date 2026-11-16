"""Sinopsis de respaldo desde Google Books por ISBN (P1-11).

La ficha editorial sigue siendo la primera fuente (`fill_full_synopses`). Para las fichas publicadas que siguen
sin sinopsis, se pide a Google Books el volumen con ese ISBN-13 exacto y en español, y su descripción se guarda
como extracto editorial con procedencia https. Las más cercanas a hoy primero (novedades antes que fondo).

Cada ISBN sin resultado útil no se vuelve a pedir en REINTENTO_DIAS: el registro vive en el estado de la ingesta
(`sinopsis_google`, ISBN -> fecha de reintento) y se poda solo, así no crece con el catálogo.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from reading_editorial_sources import editorial_excerpt, editorial_synopsis

API = 'https://www.googleapis.com/books/v1/volumes'
REINTENTO_DIAS = 30
UA = 'DavidPortoReadingCatalogue/1.0 (davidportodiaz.com)'


def consulta_google(clave, timeout=18):
    """Devuelve una función isbn -> JSON de Google Books; None si Google falla (cuota, red)."""
    def consulta(isbn):
        params = {'q': f'isbn:{isbn}', 'maxResults': 5, 'printType': 'books'}
        if clave:
            params['key'] = clave
        req = Request(API + '?' + urlencode(params), headers={'Accept': 'application/json', 'User-Agent': UA})
        try:
            with urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            return None
    return consulta


def volumen_del_isbn(respuesta, isbn):
    """El primer volumen en español cuyo ISBN-13 coincide exactamente (nunca otro libro del mismo autor)."""
    for item in (respuesta or {}).get('items') or []:
        info = item.get('volumeInfo') or {}
        ids = {i.get('identifier') for i in info.get('industryIdentifiers') or [] if i.get('type') == 'ISBN_13'}
        if isbn in ids and info.get('language') == 'es' and item.get('id'):
            return item['id'], info.get('description') or ''
    return None


def sinopsis_de(texto):
    """(breve, completa) válidas para el builder, o None; mismos limpiadores que la ficha editorial."""
    completa = editorial_synopsis(texto) if texto else ''
    completa = completa if isinstance(completa, str) else '\n\n'.join(completa or [])
    if not 60 <= len(completa) <= 4500:
        return None
    breve = editorial_excerpt(texto)
    if not 30 <= len(breve) <= 700:
        return None
    return breve, completa


def cercania(book, hoy):
    try:
        return abs((date.fromisoformat(book.get('fecha_publicacion', '')) - hoy).days)
    except ValueError:
        return 10 ** 6


def rellenar(catalogo, consulta, intentos, hoy, max_libros=40):
    """Pone sinopsis a las fichas publicadas que no tienen; devuelve cuántas. `intentos` se modifica en sitio."""
    hoy_iso = hoy.isoformat()
    for isbn in [i for i, hasta in intentos.items() if hasta <= hoy_iso]:
        del intentos[isbn]
    candidatos = sorted((b for b in catalogo['libros']
                         if b.get('estado') == 'publicado' and not b.get('sinopsis_breve') and not b.get('sinopsis_completa')
                         and b.get('sinopsis_tipo') != 'resumen_propio'
                         and re.fullmatch(r'97[89]\d{10}', b.get('isbn13') or '')
                         and b['isbn13'] not in intentos),
                        key=lambda b: (cercania(b, hoy), b['isbn13']))
    puestas = pedidas = 0
    for book in candidatos:
        if pedidas >= max_libros:
            break
        pedidas += 1
        respuesta = consulta(book['isbn13'])
        if respuesta is None:
            break  # Google caído o sin cuota: lo que quede, la próxima noche (sin marcar como intentado).
        hallado = volumen_del_isbn(respuesta, book['isbn13'])
        textos = sinopsis_de(hallado[1]) if hallado else None
        if not textos:
            intentos[book['isbn13']] = (hoy + timedelta(days=REINTENTO_DIAS)).isoformat()
            continue
        book['sinopsis_breve'], completa = textos
        book['sinopsis_completa'] = completa
        book['sinopsis_tipo'] = 'extracto_editorial'
        book['sinopsis_fuente_url'] = f'https://books.google.com/books?id={hallado[0]}'
        puestas += 1
    return puestas
