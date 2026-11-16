"""Sinopsis de respaldo desde Google Books por ISBN (P1-11).

La ficha editorial sigue siendo la primera fuente (`fill_full_synopses`). Para las fichas publicadas que siguen
sin sinopsis, se pide a Google Books el volumen con ese ISBN-13 exacto y en español, y su descripción se guarda
como extracto editorial con procedencia https. Las más cercanas a hoy primero (novedades antes que fondo).

Cada ISBN sin resultado útil se vuelve a pedir pasados `reintento_dias` (2 por defecto: la misma noche ya pasa a
la fuente siguiente, así que esperar más solo deja la ficha vacía). El registro vive en el estado de la ingesta
(`sinopsis_ttl`/`sinopsis_google`, ISBN -> fecha de reintento) y se poda solo. `fallos` (ISBN -> veces sin
resultado) señala los que ninguna fuente automática da: pasan a la lista de pendientes para buscarlos a mano.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import fecha_cercana
from reading_editorial_sources import editorial_excerpt, editorial_synopsis

API = 'https://www.googleapis.com/books/v1/volumes'
REINTENTO_DIAS = 2
UA = 'DavidPortoReadingCatalogue/1.0 (davidportodiaz.com)'


def consulta_google(clave, timeout=18):
    """Devuelve una función isbn -> JSON de Google Books; None si Google falla (cuota, red)."""
    def consulta(isbn):
        params = {'q': f'isbn:{isbn}', 'maxResults': 5, 'printType': 'books'}
        if clave:
            params['key'] = clave
        req = Request(API + '?' + urlencode(params), headers={'Accept': 'application/json', 'User-Agent': UA})
        try:
            with urlopen(req, timeout=timeout) as resp:  # skipcq: BAN-B310 - URL fija https (API)
                return json.load(resp)
        except (OSError, ValueError):  # HTTPError, URLError y TimeoutError son OSError
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
    """Fechas cercanas primero (scripts/fecha_cercana.py): la misma regla que las altas."""
    return fecha_cercana.de_libro(book, hoy)


def de_google(respuesta, isbn):
    hallado = volumen_del_isbn(respuesta, isbn)
    return (f'https://books.google.com/books?id={hallado[0]}', hallado[1]) if hallado else None


def rellenar(catalogo, consulta, intentos, hoy, max_libros=120, extraer=de_google, reintento_dias=REINTENTO_DIAS,
             fallos=None):
    """Pone sinopsis a las fichas publicadas que no tienen; devuelve cuántas. `intentos` se modifica en sitio.

    `consulta(isbn)` devuelve None si la fuente está caída (se para sin marcar); `extraer(respuesta, isbn)` da
    (url de procedencia, texto) solo si la respuesta es de ese ISBN exacto.
    """
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
        try:
            hallado = extraer(respuesta, book['isbn13'])
            textos = sinopsis_de(hallado[1]) if hallado else None
        except Exception:  # noqa: BLE001 - una ficha rara no tumba el lote: ese libro, a reintentar
            hallado = textos = None
        if not textos:
            intentos[book['isbn13']] = (hoy + timedelta(days=reintento_dias)).isoformat()
            if fallos is not None:
                fallos[book['isbn13']] = fallos.get(book['isbn13'], 0) + 1
            continue
        book['sinopsis_breve'], completa = textos
        book['sinopsis_completa'] = completa
        book['sinopsis_tipo'] = 'extracto_editorial'
        book['sinopsis_fuente_url'] = hallado[0]
        if fallos is not None:
            fallos.pop(book['isbn13'], None)
        puestas += 1
    return puestas


PLAZO_MANUAL = 20  # días sin sinopsis antes de pasar a mano o a GPT (el compromiso es que ninguna llegue a 30)
VENCIDA = 30


def pendientes(catalogo, fallos, minimo=2, desde=None, hoy=None, plazo=PLAZO_MANUAL):
    """ISBN publicados sin sinopsis a buscar a mano (o con GPT): los que Google ya falló `minimo` veces y, con
    `desde` (ISBN -> primer día visto sin sinopsis, se anota aquí), los que llevan `plazo` días o más, aunque las
    fuentes automáticas sigan intentándolo. Los más antiguos primero. Poda `fallos` y `desde` de los que ya tienen
    sinopsis o dejaron de estar publicados."""
    vacios = {b['isbn13'] for b in catalogo['libros'] if b.get('estado') == 'publicado' and b.get('isbn13')
              and not b.get('sinopsis_breve') and not b.get('sinopsis_completa') and b.get('sinopsis_tipo') != 'resumen_propio'}
    for registro in (fallos, desde if desde is not None else {}):
        for isbn in [i for i in registro if i not in vacios]:
            del registro[isbn]
    lista = {i for i, n in fallos.items() if n >= minimo}
    if desde is not None and hoy is not None:
        for isbn in vacios:
            desde.setdefault(isbn, hoy.isoformat())
        lista |= {i for i in vacios if dias_sin(desde, i, hoy) >= plazo}
    return sorted(lista, key=lambda i: (-dias_sin(desde or {}, i, hoy), i))


def dias_sin(desde, isbn, hoy):
    """Días que lleva el ISBN sin sinopsis según `desde` (0 si no consta o la fecha no se lee)."""
    try:
        return (hoy - date.fromisoformat(desde[isbn])).days
    except (KeyError, TypeError, ValueError):
        return 0


def vencidas(desde, hoy, limite=VENCIDA):
    """Cuántos ISBN llevan `limite` días o más sin sinopsis (debe ser 0: lo vigila el informe de cada carga)."""
    return sum(dias_sin(desde, i, hoy) >= limite for i in desde)
