#!/usr/bin/env python3
"""Completa las fichas de autor con Wikidata y Wikimedia Commons: vida, Q-id, ID de autor de Amazon y foto libre.

Solo añade datos verificables y nunca pisa lo que ya hay:
- Identidad: el autor se casa con un humano de Wikidata cuyo nombre (etiqueta o alias) coincide sin tildes ni
  mayúsculas. Entre varios homónimos gana el único con oficio de escritura (escritor, novelista, ilustrador...);
  si quedan dos o ninguno, el autor se deja como estaba y se apunta como ambiguo. Mejor sin datos que con los de otro.
- Vida: P569/P570 con precisión de día (AAAA-MM-DD) o de año (AAAA); el resto se descarta.
- Amazon: P4862 (Amazon author ID) alimenta la página de autor de Amazon con el tag de afiliado.
- Foto: P18 solo con licencia libre (CC0, CC BY, CC BY-SA, dominio público); se reduce a 320 px en WebP y se guarda
  en el almacén externo de portadas (`READING_COVERS_STORE_DIR`) con su crédito y licencia. Sin almacén no hay foto:
  las imágenes no engordan este repositorio.

Uso: python scripts/enrich-reading-authors.py [--limite N] [--solo slug,slug] [--sin-fotos] [--subir]
"""
from __future__ import annotations

import argparse
import html
import io
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_cover_store as cover_store  # noqa: E402

AUTHORS = ROOT / 'data/reading-authors.json'
REPORT = ROOT / 'data/reading-authors-wikidata.json'
WD = 'https://www.wikidata.org/w/api.php'
COMMONS = 'https://commons.wikimedia.org/w/api.php'
UA = 'catalogo-lecturas-bot/1.0 (generador estatico; contacto en la web)'
COLLECTIVE = {'Varios autores', 'Anónimo'}
PAUSE = 1.0
# Oficios de escritura y libro ilustrado: deshacen empates entre homónimos.
WRITING = {
    'Q36180', 'Q482980', 'Q6625963', 'Q49757', 'Q4853732', 'Q11774202', 'Q12144794', 'Q15949613', 'Q15980158',
    'Q10297252', 'Q18844224', 'Q18814623', 'Q214917', 'Q28389', 'Q8178443', 'Q1930187', 'Q1607826', 'Q333634',
    'Q644687', 'Q715301', 'Q3658608', 'Q201788', 'Q4964182',
}  # escritor, autor, novelista, poeta, infantil, ensayista, prosista, cuentos, no ficción, policiaca, ciencia
# ficción, autobiógrafo, dramaturgo, guionista, libretista, periodista, editor, traductor, ilustrador, historietista,
# caricaturista, historiador, filósofo
FREE = re.compile(r'^(cc0|cc[ -]by(?:[ -]sa)?(?: [0-9.]+)?|public domain|pd(?:-.*)?|dominio público)', re.I)
PHOTO_WIDTH = 320


def norm(text: str) -> str:
    text = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


def get_json(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode({**params, 'format': 'json', 'formatversion': 2})
    for attempt in range(4):
        try:
            req = urllib.request.Request(f'{url}?{query}', headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except Exception as exc:  # red o 429: espera lo que pida el servidor (o creciente) y reintenta
            if attempt == 3:
                raise
            wait = getattr(exc, 'headers', None) and exc.headers.get('Retry-After')
            time.sleep(min(int(wait), 120) if wait and str(wait).isdigit() else 10 * (attempt + 1))
    return {}


def get_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def search(name: str) -> list[str]:
    ids = []
    for lang in ('es', 'en'):
        data = get_json(WD, {'action': 'wbsearchentities', 'search': name, 'language': lang, 'uselang': lang,
                             'type': 'item', 'limit': 10})
        ids += [hit['id'] for hit in data.get('search', []) if hit['id'] not in ids]
        time.sleep(PAUSE)
    return ids


def entities(ids: list[str]) -> dict:
    out = {}
    for i in range(0, len(ids), 50):
        data = get_json(WD, {'action': 'wbgetentities', 'ids': '|'.join(ids[i:i + 50]),
                             'props': 'labels|aliases|claims|sitelinks', 'languages': 'es|en|ca|gl|eu|fr|it|de|pt'})
        out.update(data.get('entities', {}))
        time.sleep(PAUSE)
    return out


def values(entity: dict, prop: str) -> list:
    return [c['mainsnak'].get('datavalue', {}).get('value') for c in entity.get('claims', {}).get(prop, [])
            if c.get('rank') != 'deprecated' and c['mainsnak'].get('snaktype') == 'value']


def names_of(entity: dict) -> set[str]:
    found = {v['value'] for v in entity.get('labels', {}).values()}
    found |= {a['value'] for group in entity.get('aliases', {}).values() for a in group}
    return {norm(n) for n in found}


def is_human(entity: dict) -> bool:
    return any(isinstance(v, dict) and v.get('id') == 'Q5' for v in values(entity, 'P31'))


def writes(entity: dict) -> bool:
    return any(isinstance(v, dict) and v.get('id') in WRITING for v in values(entity, 'P106'))


def choose(name: str, found: dict) -> tuple[str | None, str]:
    """Q-id del autor o None con el motivo (sin candidatos / ambiguo)."""
    wanted = norm(name)
    people = [e for e in found.values() if is_human(e) and wanted in names_of(e)]
    if not people:
        return None, 'sin candidato'
    writers = [e for e in people if writes(e)]
    if len(writers) == 1:
        return writers[0]['id'], 'escritor'
    if not writers:
        return None, f'sin oficio de escritura ({len(people)})'
    # Homónimos escritores: gana el claramente más conocido (el doble de Wikipedias que el siguiente, y al menos 10).
    ranked = sorted(writers, key=lambda e: len(e.get('sitelinks', {})), reverse=True)
    top, second = (len(e.get('sitelinks', {})) for e in ranked[:2])
    if top >= 10 and top >= 2 * second:
        return ranked[0]['id'], 'escritor más conocido'
    return None, f'ambiguo ({len(writers)})'


def life(entity: dict, prop: str) -> str | None:
    for v in values(entity, prop):
        if not isinstance(v, dict) or not str(v.get('time', '')).startswith('+'):
            continue  # fechas antes de Cristo o sin valor
        stamp, precision = v['time'][1:], v.get('precision', 0)
        year = stamp[:4]
        if precision >= 11 and stamp[5:10] != '00-00':
            return stamp[:10]
        if precision >= 9:
            return year
    return None


def amazon_id(entity: dict) -> str | None:
    for v in values(entity, 'P4862'):
        if isinstance(v, str) and re.fullmatch(r'[A-Z0-9]{10}', v):
            return v
    return None


IDENTIFIERS = {'P214': ('viaf', 'https://viaf.org/viaf/{}'), 'P213': ('isni', 'https://isni.org/isni/{}'),
               'P950': ('bne', 'https://datos.bne.es/resource/{}'), 'P2963': ('goodreads', 'https://www.goodreads.com/author/show/{}')}


def identifiers(entity: dict) -> dict:
    """Fichas de autoridad del mismo autor (sameAs): Wikipedia en español, VIAF, ISNI, BNE, Goodreads y web oficial."""
    out = {}
    title = entity.get('sitelinks', {}).get('eswiki', {}).get('title')
    if title:
        out['wikipedia'] = 'https://es.wikipedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'))
    for prop, (name, pattern) in IDENTIFIERS.items():
        found = [v for v in values(entity, prop) if isinstance(v, str) and re.fullmatch(r'[0-9A-Za-z_.-]{1,40}', v.replace(' ', ''))]
        if found:
            out[name] = pattern.format(urllib.parse.quote(found[0].replace(' ', '')))
    web = [v for v in values(entity, 'P856') if isinstance(v, str) and re.match(r'https://[^\s<>]+$', v)]  # la ficha solo enlaza https
    if web:
        out['web'] = web[0]
    return out


def strip_html(text: str) -> str:
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', text or ''))).strip()


def photo(entity: dict, slug: str, root: Path) -> dict | None:
    files = [v for v in values(entity, 'P18') if isinstance(v, str)]
    if not files:
        return None
    title = 'File:' + files[0]
    data = get_json(COMMONS, {'action': 'query', 'titles': title, 'prop': 'imageinfo',
                              'iiprop': 'url|extmetadata', 'iiurlwidth': PHOTO_WIDTH})
    time.sleep(PAUSE)
    pages = data.get('query', {}).get('pages', [])
    info = (pages[0].get('imageinfo') or [None])[0] if pages else None
    if not info or not info.get('thumburl'):
        return None
    meta = info.get('extmetadata', {})
    licence = strip_html(meta.get('LicenseShortName', {}).get('value', ''))
    artist = strip_html(meta.get('Artist', {}).get('value', '')) or 'Autor desconocido'
    if not FREE.match(licence):
        return None
    from PIL import Image
    image = Image.open(io.BytesIO(get_bytes(info['thumburl'])))
    image = image.convert('RGB')
    if image.width > PHOTO_WIDTH:
        image = image.resize((PHOTO_WIDTH, round(image.height * PHOTO_WIDTH / image.width)), Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, 'WEBP', quality=80, method=6)
    content = buffer.getvalue()
    path = cover_store.fresh_name(f'{cover_store.LOGICAL_PREFIX}autor-{slug}.webp', content)
    cover_store.put(root, path, content)
    result = {'url': path, 'ancho': image.width, 'alto': image.height, 'autor': artist[:120], 'licencia': licence[:60],
              'fuente_url': info.get('descriptionurl') or f'https://commons.wikimedia.org/wiki/{urllib.parse.quote(title)}'}
    licence_url = meta.get('LicenseUrl', {}).get('value', '')
    if licence_url.startswith('http'):
        result['licencia_url'] = 'https://' + licence_url.split('://', 1)[1]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--limite', type=int, default=0, help='máximo de autores a consultar en esta pasada')
    parser.add_argument('--solo', default='', help='slugs separados por comas')
    parser.add_argument('--sin-fotos', action='store_true')
    parser.add_argument('--subir', action='store_true', help='sube al almacén las fotos nuevas al terminar')
    args = parser.parse_args()
    payload = json.loads(AUTHORS.read_text(encoding='utf-8'))
    report = json.loads(REPORT.read_text(encoding='utf-8')) if REPORT.is_file() else {}
    only = {s for s in args.solo.split(',') if s}
    photos = not args.sin_fotos and cover_store.store_dir() is not None
    if not args.sin_fotos and not photos:
        print(f'Aviso: sin {cover_store.STORE_DIR_ENV} no se guardan fotos (solo datos).')
    pending = [a for a in payload['autores'] if a['nombre'] not in COLLECTIVE and (a['slug'] in only if only else a['slug'] not in report or (report[a['slug']].get('qid') and 'ids' not in report[a['slug']]))]
    if args.limite:
        pending = pending[:args.limite]
    stats = {'casados': 0, 'fotos': 0, 'amazon': 0, 'vida': 0, 'sin casar': 0}
    for n, author in enumerate(pending, 1):
        try:
            found = entities(search(author['nombre']))
            qid, why = choose(author['nombre'], found)
            report[author['slug']] = {'qid': qid, 'motivo': why}
            if not qid:
                stats['sin casar'] += 1
                continue
            entity = found[qid]
            stats['casados'] += 1
            ids = identifiers(entity)
            report[author['slug']]['ids'] = sorted(ids)
            for name, link in ids.items():
                author.setdefault('identificadores', {}).setdefault(name, link)
            author.setdefault('wikidata', qid)
            born, died = life(entity, 'P569'), life(entity, 'P570')
            if born and not author.get('nacimiento'):
                author['nacimiento'] = born
            if died and not author.get('fallecimiento') and (not author.get('nacimiento') or author['nacimiento'][:4] <= died[:4]):
                author['fallecimiento'] = died
            stats['vida'] += bool(born)
            if (amazon := amazon_id(entity)) and not author.get('amazon_autor_id'):
                author['amazon_autor_id'] = amazon
                stats['amazon'] += 1
            if photos and not author.get('foto') and (found_photo := photo(entity, author['slug'], ROOT)):
                author['foto'] = found_photo
                stats['fotos'] += 1
        except Exception as exc:  # un autor raro no tumba la pasada; se reintenta en la siguiente
            report.pop(author['slug'], None)
            print(f'  {author["slug"]}: error {type(exc).__name__}: {exc}')
        finally:  # también tras el `continue` de un autor sin casar: el punto de control nunca se salta
            if n % 25 == 0 or n == len(pending):
                AUTHORS.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='')
                REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='')
                print(f'{n}/{len(pending)} {stats}', flush=True)
    if args.subir and photos:
        print('Fotos subidas al almacén:', cover_store.flush('Fotos de autores (Wikimedia Commons)', ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
