#!/usr/bin/env python3
"""Da a cada autor el ID de su página de autor en Amazon.es, leído de la ficha de uno de sus libros.

La búsqueda por nombre (`p_27:nombre`) mezcla homónimos y coautores («Juana Cárdenas» para «Juan Cárdenas»). La ficha
de un libro enlaza a su autor por ID (`/Nombre/e/B001JOGIL6`); se toma ese ID solo si el nombre del enlace coincide,
sin tildes ni mayúsculas, con el del autor. Sin coincidencia no se escribe nada y el autor sigue con la búsqueda.

Uso: python scripts/enrich-amazon-author-ids.py [--limite N] [--pausa 1.5]
Es reanudable: salta a quien ya tiene `amazon_autor_id` o `amazon_autor_id_probado` (fecha de la última prueba).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORS = ROOT / 'data' / 'reading-authors.json'
CATALOGUE = ROOT / 'data' / 'reading-catalogue.json'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
HEADERS = {'User-Agent': UA, 'Accept-Language': 'es-ES,es;q=0.9', 'Accept': 'text/html,application/xhtml+xml', 'Accept-Encoding': 'identity'}
LINK = re.compile(r'href="/([^"/]+)/e/(B[0-9A-Z]{9})[/?"]')


def norm(text: str) -> str:
    text = unicodedata.normalize('NFKD', text)
    return re.sub(r'[^a-z0-9]+', ' ', ''.join(c for c in text if not unicodedata.combining(c)).lower()).strip()


def isbn10(isbn13: str) -> str | None:
    if not re.fullmatch(r'978\d{10}', isbn13 or ''):
        return None
    core = isbn13[3:12]
    check = sum((10 - i) * int(c) for i, c in enumerate(core)) % 11
    check = (11 - check) % 11
    return core + ('X' if check == 10 else str(check))


def author_id(page: str, name: str) -> str | None:
    wanted = norm(name)
    for slug, ident in LINK.findall(page):
        if norm(urllib.parse.unquote(slug)) == wanted:
            return ident
    return None


class Blocked(Exception):
    pass


def get(url: str) -> str:
    """curl y no urllib: amazon.es sirve a urllib una página de «seguir comprando» (huella TLS)."""
    out = subprocess.run(['curl', '-s', '--max-time', '30', '-A', UA, '-H', 'Accept-Language: es-ES,es;q=0.9', url], capture_output=True, check=True)
    page = out.stdout.decode('utf-8', 'replace')
    if len(page) < 20000 and 'seguir comprando' in page or not page:
        raise Blocked(url)  # página de bloqueo: no es «el autor no tiene ID»
    return page


def fetch(isbn13: str) -> str:
    """Ficha del libro: /dp/ISBN-10 en 978; los 979 no tienen ISBN-10, se llega por la búsqueda del ISBN."""
    ten = isbn10(isbn13)
    if ten:
        return get('https://www.amazon.es/dp/' + ten)
    found = re.search(r'data-asin="(B[0-9A-Z]{9}|\d{9}[0-9X])"', get('https://www.amazon.es/s?i=stripbooks&k=' + isbn13))
    return get('https://www.amazon.es/dp/' + found.group(1)) if found else ''


def save(data: dict) -> None:
    AUTHORS.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limite', type=int, default=0)
    parser.add_argument('--pausa', type=float, default=1.5)
    args = parser.parse_args()
    data = json.loads(AUTHORS.read_text(encoding='utf-8'))
    books = json.loads(CATALOGUE.read_text(encoding='utf-8'))
    books = books['libros'] if isinstance(books, dict) else books
    by_author: dict[str, list[str]] = {}
    for b in books:
        if re.fullmatch(r'97[89]\d{10}', b.get('isbn13') or ''):
            for name in b.get('autores', []):
                by_author.setdefault(name, []).append(b['isbn13'])
    today = date.today().isoformat()
    todo = [a for a in data['autores'] if not a.get('amazon_autor_id') and a.get('amazon_autor_id_probado') is None and by_author.get(a['nombre'])]
    if args.limite:
        todo = todo[:args.limite]
    found = tried = 0
    for a in todo:
        tried += 1
        ident = None
        try:
            for isbn in by_author[a['nombre']][:2]:
                ident = author_id(fetch(isbn), a['nombre'])
                time.sleep(args.pausa)
                if ident:
                    break
        except Exception as exc:  # bloqueo, 5xx o corte: no se marca como probado; se espera y se sigue
            print('error', a['nombre'], exc, flush=True)
            time.sleep(60 if isinstance(exc, Blocked) else 10)
            continue
        if ident:
            a['amazon_autor_id'] = ident
            found += 1
        else:
            a['amazon_autor_id_probado'] = today
        if tried % 25 == 0:
            save(data)
            print(f'{tried}/{len(todo)} con ID: {found}', flush=True)
    save(data)
    print(f'Hecho: {tried} probados, {found} con ID.')


if __name__ == '__main__':
    main()
