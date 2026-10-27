#!/usr/bin/env python3
"""Precios de tiendas editoriales, NUNCA de Amazon; adaptadores sin scraping Amazon.

No se publica automáticamente hasta que el piloto confirme markup, robots y
condiciones de uso del proveedor. Código de solo lectura por defecto.
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

from reading_editorial_sources import CachedHTTP, ProductHTML, PRODUCT_PATH, SourceError, penguin_edition
from reading_ratings_refresh import isbn13, title_matches, author_matches
from reading_intake_fetch import read_json, write_if_changed

ROOT = Path(__file__).resolve().parents[1]
HOST = 'www.penguinlibros.com'


def cents(value):
    """Only unambiguous numeric EUR amounts or exact Spanish printed amounts."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, (int, float, Decimal)):
            number = Decimal(str(value))
        elif isinstance(value, str):
            clean = value.replace('\u00a0', ' ').strip()
            if re.fullmatch(r'\d{1,6},\d{2}(?:\s*€)?', clean):
                number = Decimal(clean.replace('€', '').strip().replace(',', '.'))
            elif re.fullmatch(r'\d{1,6}\.\d{2}', clean):
                number = Decimal(clean)
            else:
                return None
        else:
            return None
        raw = number * 100
        return int(raw) if raw.is_finite() and raw == raw.to_integral_value() and 0 < raw < 100000000 else None
    except InvalidOperation:
        return None


def penguin_offer(book, page, now, *, valid_hours=24):
    """The selected product node must match verified edition, canonical and ISBN.

    price_amount is the expected PrestaShop data-product key: NOT YET verified
    from live HTML for the pilot. Missing key => no price rather than guessing.
    """
    url = book.get('fuente_bibliografica_url', '')
    parts = urlsplit(url)
    wanted = isbn13(book.get('isbn13'))
    path = PRODUCT_PATH.fullmatch(parts.path)
    if parts.scheme != 'https' or parts.hostname != HOST or parts.query or parts.fragment or not path or path.group(1) != wanted:
        return None
    document = page.decode('utf-8') if isinstance(page, bytes) else page
    edition = penguin_edition(document, url)
    if (edition['isbn13'] != wanted
        or not title_matches(edition['titulo'], book['titulo'])
        or not all(any(author_matches(a, b) for a in edition['autores']) for b in book['autores'])
        or edition['formato_edicion'] != book.get('formato_edicion')):
        return None
    parser = ProductHTML()
    parser.feed(document)
    matches = [p for p in parser.products if str(p.get('reference')) == wanted]
    if len(matches) != 1:
        return None
    product = matches[0]
    price = cents(product.get('price_amount'))
    if price is None:
        price = cents(product.get('price'))  # same validated edition node; never scan page-wide text
    if price is None:
        return None
    reference = cents(product.get('regular_price_amount'))
    stamp = now.astimezone(timezone.utc)
    offer = {
        'libro_id': book['id'], 'isbn13': wanted, 'fuente': 'penguin_libros',
        'formato': edition['formato_edicion'], 'moneda': 'EUR',
        'precio_centimos': price, 'url': url,
        'actualizado_en': stamp.isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'caduca_en': (stamp + timedelta(hours=valid_hours)).isoformat(timespec='seconds').replace('+00:00', 'Z')
    }
    if reference and reference > price:
        offer['precio_referencia_centimos'] = reference
    return offer


def google_ebook_offer(book, response, now):
    """Optional Google Play Books price for EXACT matching Spanish eBook ISBN."""
    wanted = isbn13(book.get('isbn13'))
    if book.get('formato_edicion') != 'ebook' or not wanted:
        return None
    for volume in response.get('items', []):
        if not isinstance(volume, dict):
            continue
        info, sale = volume.get('volumeInfo') or {}, volume.get('saleInfo') or {}
        ids = {isbn13(i.get('identifier')) for i in info.get('industryIdentifiers', [])
               if isinstance(i, dict) and i.get('type') in {'ISBN_13', 'ISBN_10'}}
        if wanted not in ids or not title_matches(str(info.get('title') or ''), book['titulo']):
            continue
        if not any(author_matches(str(a), b) for a in info.get('authors', [])
                   for b in book.get('autores', [])):
            continue
        if sale.get('country') != 'ES' or sale.get('saleability') != 'FOR_SALE' or sale.get('isEbook') is not True:
            continue
        price = sale.get('retailPrice') or {}
        if price.get('currencyCode') != 'EUR':
            continue
        amount = cents(price.get('amount'))
        link = sale.get('buyLink', '')
        parsed = urlsplit(link)
        if not amount or parsed.scheme != 'https' or parsed.hostname not in {'books.google.com', 'play.google.com'} or parsed.username or parsed.password:
            continue
        stamp = now.astimezone(timezone.utc)
        return {'libro_id': book['id'], 'isbn13': wanted, 'fuente': 'google_play_libros',
                'formato': 'ebook', 'moneda': 'EUR', 'precio_centimos': amount, 'url': link,
                'actualizado_en': stamp.isoformat(timespec='seconds').replace('+00:00', 'Z'),
                'caduca_en': (stamp + timedelta(hours=24)).isoformat(timespec='seconds').replace('+00:00', 'Z')}
    return None


def refresh_google_ebooks(catalogue, previous, query, now, *, budget=10):
    """Optional ebook offers from official Google Books saleInfo, strictly ES.

    Query is injected so tests remain completely offline. Rate/provider errors
    halt the provider and never change the timestamp of older results.
    """
    if not 0 <= budget <= 40:
        raise ValueError('Presupuesto Google fuera de 0..40')
    current = {(o.get('libro_id'), o.get('fuente')): o for o in previous.get('offers', [])
               if isinstance(o, dict)}
    books = [b for b in catalogue.get('libros', [])
             if b.get('estado') == 'publicado' and b.get('formato_edicion') == 'ebook'
             and isbn13(b.get('isbn13'))]
    books.sort(key=lambda b: (current.get((b['id'], 'google_play_libros'), {}).get('actualizado_en', ''), b['id']))
    stats = {'candidatos': len(books), 'consultados': 0, 'actualizados': 0,
             'sin_oferta': 0, 'errores': []}
    for book in books[:budget]:
        stats['consultados'] += 1
        try:
            response = query(book['isbn13'])
            offer = google_ebook_offer(book, response, now)
            if offer:
                current[(book['id'], 'google_play_libros')] = offer
                stats['actualizados'] += 1
            else:
                current.pop((book['id'], 'google_play_libros'), None)
                stats['sin_oferta'] += 1
        except (RuntimeError, ValueError, OSError, TimeoutError, TypeError) as exc:
            stats['errores'].append({'libro_id': book['id'], 'tipo': type(exc).__name__})
            break
    cutoff = now.astimezone(timezone.utc) - timedelta(days=1)
    offers = [o for o in current.values() if (t := parse_time(o.get('caduca_en'))) is not None and t > cutoff]
    return {'schema_version': 1, 'offers': sorted(offers, key=lambda o: (o['libro_id'], o['fuente']))}, stats


def parse_time(raw):
    try:
        t = datetime.fromisoformat(str(raw).replace('Z', '+00:00'))
        return t.astimezone(timezone.utc) if t.tzinfo else None
    except (TypeError, ValueError):
        return None


def refresh_penguin(catalogue, previous, get_page, now, *, budget=30):
    """Earliest-checked first. Missing price removes stale listing, not the book."""
    if not 0 <= budget <= 80:
        raise ValueError('Presupuesto fuera de 0..80')
    books = [b for b in catalogue.get('libros', [])
             if b.get('estado') == 'publicado'
             and b.get('fuente_bibliografica_url', '').startswith('https://' + HOST + '/es/')
             and isbn13(b.get('isbn13'))]
    current = {(o.get('libro_id'), o.get('fuente')): o for o in previous.get('offers', [])
               if isinstance(o, dict)}
    books.sort(key=lambda b: (current.get((b['id'], 'penguin_libros'), {}).get('actualizado_en', ''), b['id']))
    stats = {'candidatos': len(books), 'consultados': 0, 'actualizados': 0,
             'sin_precio_validado': 0, 'errores': []}
    for book in books[:budget]:
        stats['consultados'] += 1
        try:
            page = get_page(book['fuente_bibliografica_url'])
            offer = penguin_offer(book, page, now)
            if offer:
                current[(book['id'], offer['fuente'])] = offer
                stats['actualizados'] += 1
            else:
                stats['sin_precio_validado'] += 1
                current.pop((book['id'], 'penguin_libros'), None)
        except (SourceError, ValueError, OSError, TimeoutError) as exc:
            stats['errores'].append({'libro_id': book['id'], 'tipo': type(exc).__name__})
            # Do not invent a new verification date after a refused request.
            if isinstance(exc, (SourceError, TimeoutError)):
                break
    cutoff = now.astimezone(timezone.utc) - timedelta(days=1)
    offers = [o for o in current.values() if (t := parse_time(o.get('caduca_en'))) is not None and t > cutoff]
    return {'schema_version': 1, 'offers': sorted(offers, key=lambda o: (o['libro_id'], o['fuente']))}, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-pilot', action='store_true', help='Leer páginas remotas sin publicar')
    parser.add_argument('--apply', action='store_true', help='Escribir salida pública solo tras piloto')
    parser.add_argument('--budget', type=int, default=30)
    args = parser.parse_args()
    if not args.live_pilot:
        parser.error('La red exige --live-pilot')
    config = read_json(ROOT / 'data/reading-intake-config.json')
    dataset = read_json(ROOT / 'data/reading-catalogue.json')
    out = ROOT / 'assets/reading-free-prices.json'
    before = read_json(out, {'schema_version': 1, 'offers': []})
    http = CachedHTTP(ROOT / '.ci/reading-editorial-cache/http', [HOST],
                      budget=args.budget + 2, delay=config['request_delay_seconds'])
    data, stats = refresh_penguin(dataset, before, lambda url: http.get(url, ttl=0),  # Fresh HTTP response; never stamp old cached price as newly checked
                                  datetime.now(timezone.utc), budget=args.budget)
    print(json.dumps({'stats': stats, 'solicitudes_http': http.requests,
                      'precios_validos': len(data['offers']), 'escritura': bool(args.apply)}, ensure_ascii=False))
    if args.apply:
        write_if_changed(out, data)


if __name__ == '__main__':
    main()
