"""Nota biográfica breve desde Wikipedia (es) para autores sin ficha biográfica editorial.

API REST pública de resumen de página; sin claves ni modelos. Se acepta un resultado solo si:
  - es un artículo normal (no desambiguación) cuyo título coincide con el nombre del autor;
  - su descripción corta nombra una ocupación literaria o afín (evita homónimos);
  - el extracto es lo bastante largo y se recorta por frases a un máximo de 600 caracteres.
Si el autor ya tiene su artículo enlazado en `identificadores.wikipedia` (sale de Wikidata, identidad ya comprobada),
se pide ese artículo y no se exigen ni título igual ni oficio: así entran «mangaka», seudónimos o títulos con
aclaración «(escritor)».
El texto se atribuye a Wikipedia con enlace al artículo (licencia CC BY-SA 4.0).

Un artículo rechazado a mano (homónimo) se apunta en `biografia_descartada` y no vuelve a entrar.

Uso manual (rellenado completo, sin la espera de 30 días): python scripts/reading_author_wikipedia.py --todos
"""
from __future__ import annotations

import json
import re
import time
from datetime import date
from urllib.error import HTTPError
from urllib.parse import quote, unquote
from urllib.request import Request, urlopen

from reading_intake_core import normalize_text

AGENT = 'DavidPortoReadingCatalogue/1.0 (+https://davidportodiaz.com)'
API = 'https://es.wikipedia.org/api/rest_v1/page/summary/'
OCCUPATION = re.compile(
    r'\b(escritor|escritora|novelista|autor|autora|poeta|poetisa|periodista|dramaturgo|dramaturga|guionista|'
    r'historiador|historiadora|ensayista|ilustrador|ilustradora|cocinero|cocinera|chef|nutricionista|'
    r'psiquiatra|psic[oó]log[oa]|neurocirujano|neurocirujana|divulgador|divulgadora|m[eé]dico|m[eé]dica|'
    r'traductor|traductora|cr[ií]tico|cr[ií]tica|presentador|presentadora|investigador|investigadora|'
    r'mangaka|historietista|dibujante|humorista|fil[oó]sof[oa]|soci[oó]log[oa]|economista|antrop[oó]log[oa]|'
    r'arque[oó]log[oa]|te[oó]log[oa]|bi[oó]log[oa]|cient[ií]fic[oa]|profesor|profesora|catedr[aá]tic[oa]|'
    r'acad[eé]mic[oa]|editor|editora|youtuber)\b', re.I)
WIKI_PAGE = re.compile(r'https://es\.wikipedia\.org/wiki/([^\s?#]+)')
MAX_CHARS = 600
MIN_CHARS = 60


def clean_extract(text: str) -> str:
    text = re.sub(r'\s*\[[0-9a-z ]{1,4}\]', '', ' '.join(str(text).split()))
    if len(text) <= MAX_CHARS:
        return text
    cut = text[:MAX_CHARS]
    sentence = max(cut.rfind('. '), cut.rfind('.” '), cut.rfind('.» '))
    return (cut[:sentence + 1] if sentence >= MIN_CHARS else cut.rsplit(' ', 1)[0] + '…').strip()


def linked_title(author: dict) -> str:
    """Título del artículo de es.wikipedia ya enlazado al autor (vía Wikidata), o ''."""
    m = WIKI_PAGE.fullmatch(str((author.get('identificadores') or {}).get('wikipedia', '')))
    return unquote(m.group(1)).replace('_', ' ') if m else ''


def select_wikipedia_bio(name: str, response: dict, *, verified: bool = False) -> dict | None:
    """Valida un resumen de Wikipedia para `name`; devuelve datos de biografía o None.

    `verified`: el artículo se pidió por el enlace de Wikidata del autor, así que la identidad ya está comprobada."""
    if not isinstance(response, dict) or response.get('type') != 'standard':
        return None
    if not verified:
        title = str(response.get('title', ''))
        if normalize_text(title) != normalize_text(name):
            return None
        if not OCCUPATION.search(str(response.get('description', ''))):
            return None
    page = ((response.get('content_urls') or {}).get('desktop') or {}).get('page', '')
    if not re.fullmatch(r'https://es\.wikipedia\.org/wiki/[^\s?#]+', page):
        return None
    extract = clean_extract(response.get('extract', ''))
    if len(extract) < MIN_CHARS:
        return None
    return {'biografia_breve': extract, 'biografia_fuente_url': page, 'biografia_fuente_nombre': 'Wikipedia'}


class WikipediaSummaries:
    """Cliente mínimo: una petición por nombre, pausa entre peticiones y parada ante errores."""

    def __init__(self, delay=1.0, budget=10, opener=urlopen):
        self.delay, self.budget, self.opener = delay, budget, opener
        self.requests, self.last, self.unavailable = 0, 0.0, False

    def __call__(self, name: str) -> dict | None:
        if self.unavailable or self.requests >= self.budget:
            return None
        pause = self.delay - (time.monotonic() - self.last)
        if pause > 0:
            time.sleep(pause)
        self.last = time.monotonic()
        self.requests += 1
        request = Request(API + quote(name.replace(' ', '_'), safe=''), headers={'User-Agent': AGENT, 'Accept': 'application/json'})
        try:
            with self.opener(request, timeout=15) as response:
                return json.loads(response.read(400_000).decode('utf-8'))
        except HTTPError as exc:
            if exc.code == 404:
                return None  # Sin artículo: caso normal, no detiene al resto.
            self.unavailable = True
            return None
        except (OSError, ValueError):
            self.unavailable = True
            return None


def fill_missing_bios(authors: dict, lookup, today: str, *, max_authors=7, force=False) -> int:
    """Rellena autores bibliográficos sin biografía; las biografías manuales no se tocan.

    Primero los que ya tienen artículo enlazado (acierto casi seguro); `max_authors=0` = sin tope."""
    changed = 0
    todo = sorted(authors['autores'], key=lambda a: not linked_title(a))
    for author in todo:
        if (max_authors and changed >= max_authors) or getattr(lookup, 'unavailable', False):
            break
        if author.get('tipo') != 'bibliografico' or author.get('biografia_breve'):
            continue
        last = author.get('biografia_ultimo_intento', '')
        if not force and last and (date.fromisoformat(today) - date.fromisoformat(last)).days < 30:
            continue  # Un autor sin artículo se vuelve a probar como mucho una vez al mes.
        linked = linked_title(author)
        found = select_wikipedia_bio(author['nombre'], lookup(linked or author['nombre']) or {}, verified=bool(linked))
        author['biografia_ultimo_intento'] = today
        if found and found['biografia_fuente_url'] in author.get('biografia_descartada', []):
            found = None  # Homónimo ya rechazado a mano: no se vuelve a poner.
        if found:
            author.update(found, biografia_fecha_revision=today)
            changed += 1
    return changed


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Rellena biografías breves desde Wikipedia en data/reading-authors.json')
    parser.add_argument('--todos', action='store_true', help='sin tope de autores ni espera de 30 días')
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / 'data/reading-authors.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    client = WikipediaSummaries(budget=10**6 if args.todos else 10)
    n = fill_missing_bios(data, client, date.today().isoformat(), max_authors=0 if args.todos else 7, force=args.todos)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')
    print(n, 'biografías nuevas;', client.requests, 'peticiones', '(Wikipedia dejó de responder)' if client.unavailable else '')
