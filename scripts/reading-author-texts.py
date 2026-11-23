#!/usr/bin/env python3
"""Fichas de autor con texto propio para SEO: ChatGPT web en razonamiento alto y con búsqueda en internet.

Una consulta por autor (un chat nuevo), con hasta REPAIR_TURNS correcciones en el mismo chat si el validador
rechaza algo. Cada respuesta válida se guarda en `.local/reading-author-texts/out/<slug>.json`; la publicación
de textos de `scripts/reading-texts.py publish` la copia a `data/reading-author-texts/` (revalidada) y el
constructor la pinta en la ficha: por dónde empezar, obras en orden de publicación, sagas, biografía,
autores parecidos con motivo, preguntas frecuentes y fuentes.

A diferencia de los textos de libros (Instant, solo con las evidencias de la ficha), aquí se pide High y que
busque en internet: el valor está en datos que no tenemos (año original, sagas, trayectoria), y las fuentes
se publican con la fecha de revisión.

Uso:
  python scripts/reading-author-texts.py pending
  python scripts/reading-author-texts.py prompt --slug stephen-king
  python scripts/reading-author-texts.py run [--max 50] [--hours 24] [--publish-every 25]
  python scripts/reading-author-texts.py validate .local/reading-author-texts/out/*.json
"""
import argparse
import hashlib
import importlib.util
import json
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.local/reading-author-texts/out'
STATE = ROOT / '.local/reading-author-texts/state.json'
PROMPT = ROOT / 'scripts/templates/reading-author-texts-prompt.md'
PUBLISHED = 'data/reading-author-texts'
VERSION = 1
MAX_ATTEMPTS = 3
REPAIR_TURNS = 2
REFRESH_DAYS = 180  # el último libro y los próximos salen del catálogo; el texto se revisa dos veces al año
MAX_BOOKS_IN_PROMPT = 40
CANDIDATES = 8
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


def load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rt = load_module('reading_texts_for_authors', 'scripts/reading-texts.py')
catalogue = rt.catalogue
read_json, write_json = rt.read_json, rt.write_json


def fold(text):
    t = unicodedata.normalize('NFKD', str(text or '')).encode('ascii', 'ignore').decode().casefold()
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()


def words(text):
    return len(re.findall(r'\w+', str(text or '')))


# ---------------------------------------------------------------- qué autores y con qué datos

def context(root=ROOT):
    data = read_json(root / 'data/reading-catalogue.json')
    catalogue.index_categories(data)
    books = [b for b in data['libros'] if b['estado'] == 'publicado']
    authors = [a for a in read_json(root / 'data/reading-authors.json')['autores'] if a.get('slug')]
    return data, books, authors


def author_books(a, books):
    return catalogue._newest_first([b for b in books if a['nombre'] in b['autores']])


def payload(a, data, books, authors):
    """Lo que sabe la web del autor: sus ediciones en España y los candidatos a «parecidos» (mismo cálculo que la ficha)."""
    mine = author_books(a, books)
    seen, rows = set(), []
    for b in mine:
        k = catalogue.edition_key(b['titulo'])
        if k in seen:
            continue
        seen.add(k)
        title = re.sub(r'\s*\([^)]*\)', '', b['titulo']).strip() or b['titulo']  # sin «(edición cantos tintados)» y similares
        rows.append({k2: v for k2, v in (('titulo', title), ('editorial', b.get('editorial')),
                                          ('edicion', (b.get('fecha_publicacion') or '')[:4] or None)) if v})
    similar = catalogue.similar_authors(a, data, books, authors, limit=CANDIDATES)
    p = {'slug': a['slug'], 'nombre': a['nombre'], 'libros_en_la_web': rows[:MAX_BOOKS_IN_PROMPT],
         'candidatos_parecidos': [o['nombre'] for o in similar]}
    for k in ('nacimiento', 'fallecimiento', 'wikidata'):
        if a.get(k):
            p[k] = a[k]
    if a.get('identificadores', {}).get('wikipedia'):
        p['wikipedia'] = a['identificadores']['wikipedia']
    return p


def source_hash(p):
    """Solo la identidad del autor: los libros nuevos no obligan a reescribir (la ficha los toma del catálogo)."""
    stable = {k: p.get(k) for k in ('slug', 'nombre', 'nacimiento', 'fallecimiento', 'wikidata')}
    stable['version'] = VERSION
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def eligible(a, books):
    return a['nombre'] not in catalogue.COLLECTIVE_AUTHORS and bool(author_books(a, books))


def pending(data, books, authors, state=None, out=OUT, today=None):
    """Autores sin texto vigente, primero los que más libros tienen en la web (más búsquedas y más clics a Amazon)."""
    state = state or {}
    today = today or datetime.now(ZoneInfo('Europe/Madrid')).date()
    rows = []
    for a in authors:
        if not eligible(a, books):
            continue
        p = payload(a, data, books, authors)
        h = source_hash(p)
        saved = read_json(out / (a['slug'] + '.json'))
        if saved and saved.get('fuente_hash') == h:
            revised = saved.get('fecha_revision', '')[:10]
            if revised and (today - datetime.fromisoformat(revised).date()) < timedelta(days=REFRESH_DAYS):
                continue
        entry = state.get(a['slug'], {})
        if entry.get('hash') == h and entry.get('intentos', 0) >= MAX_ATTEMPTS:
            continue
        rows.append((len(author_books(a, books)), bool(a.get('wikidata')), a['slug'], a))
    # Sin Wikidata suelen ser marcas o sellos (Disney, DK): van al final; si GPT no los identifica, no se publican.
    return [r[-1] for r in sorted(rows, key=lambda r: (not r[1], -r[0], r[2]))]


def build_prompt(p):
    return PROMPT.read_text(encoding='utf-8').replace('{{AUTOR}}', json.dumps(p, ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- validación

TEXT_FIELDS = ('intro', 'biografia')
NO_MARKUP = re.compile(r'https?://|www\.|\*\*|\[[^\]]*\]\(|^#|<[a-z/]', re.I | re.M)
BAD_SOURCE = re.compile(r'chatgpt\.com|openai\.com|amazon\.|bing\.com/search|google\.[a-z.]+/search', re.I)
SHOP_QUESTION = re.compile(r'compr|amazon|precio|descarg|pdf|gratis', re.I)


def _text_errors(label, text, minimum, maximum):
    errors = []
    n = words(text)
    if not minimum <= n <= maximum:
        errors.append(f'{label}: {n} palabras (de {minimum} a {maximum})')
    if NO_MARKUP.search(text):
        errors.append(f'{label}: sin enlaces, Markdown ni HTML')
    if rt.OPINION.search(text):
        errors.append(f'{label}: valoración o adjetivo de promoción («{rt.OPINION.search(text).group(0)}»)')
    if rt.META.search(text):
        errors.append(f'{label}: habla de las fuentes o de datos ausentes')
    if rt.AI_TELLS.search(text):
        errors.append(f'{label}: muletilla («{rt.AI_TELLS.search(text).group(0)}»)')
    return errors


def clean_text(value):
    return re.sub(r'[ \t]+', ' ', str(value or '').replace('\r', '')).strip()


def validate(p, t, year=None):
    """(texto limpio, errores). Lo dudoso que se puede quitar sin perder la ficha se quita; lo que la deja
    coja (intro, biografía, fuentes) es error y se pide corregir."""
    year = year or datetime.now(ZoneInfo('Europe/Madrid')).year
    if not isinstance(t, dict):
        return None, ['la respuesta no es un objeto JSON']
    if t.get('slug') != p['slug']:
        return None, [f'slug distinto: debe ser {p["slug"]}']
    if t.get('identificado') is False:
        return {'slug': p['slug'], 'identificado': False}, []
    errors, out = [], {'slug': p['slug'], 'identificado': True}
    for field, lo, hi in (('intro', 40, 110), ('biografia', 100, 320)):
        text = clean_text(t.get(field))
        errors += _text_errors(field, text, lo, hi)
        out[field] = text
    surname = fold(p['nombre']).split()[-1] if fold(p['nombre']) else ''
    if surname and surname not in fold(out['intro']):
        errors.append('intro: debe nombrar al autor')
    start = [x for x in t.get('por_donde_empezar') or [] if isinstance(x, dict) and clean_text(x.get('titulo')) and clean_text(x.get('motivo'))]
    out['por_donde_empezar'] = [{'titulo': clean_text(x['titulo']), 'motivo': clean_text(x['motivo'])} for x in start[:3]]
    if not out['por_donde_empezar']:
        errors.append('por_donde_empezar: de 2 a 3 obras con su motivo')
    for x in out['por_donde_empezar']:
        errors += _text_errors('por_donde_empezar «' + x['titulo'] + '»', x['motivo'], 5, 70)
    works, keys = [], set()
    for x in t.get('obras') or []:
        if not isinstance(x, dict) or not clean_text(x.get('titulo')):
            continue
        try:
            anio = int(x.get('anio'))
        except (TypeError, ValueError):
            continue
        k = fold(x['titulo'])
        if not 1000 <= anio <= year + 2 or k in keys:
            continue
        keys.add(k)
        w = {'titulo': clean_text(x['titulo']), 'anio': anio}
        original = clean_text(x.get('titulo_original'))
        if original and fold(original) != k:
            w['titulo_original'] = original
        if clean_text(x.get('saga')) and str(x.get('saga')).lower() != 'null':
            w['saga'] = clean_text(x['saga'])
        works.append(w)
    out['obras'] = sorted(works, key=lambda w: (w['anio'], fold(w['titulo'])))[:40]
    if not out['obras']:
        errors.append('obras: al menos una obra con su año de primera publicación')
    out['sagas'] = [{'nombre': clean_text(s['nombre']), 'libros': [clean_text(b) for b in s['libros'] if clean_text(b)]}
                    for s in t.get('sagas') or [] if isinstance(s, dict) and clean_text(s.get('nombre')) and isinstance(s.get('libros'), list)
                    and len([b for b in s['libros'] if clean_text(b)]) >= 2][:8]
    allowed = {fold(n): n for n in p.get('candidatos_parecidos', [])}
    out['parecidos'] = [{'nombre': allowed[fold(x['nombre'])], 'motivo': clean_text(x['motivo'])} for x in t.get('parecidos') or []
                        if isinstance(x, dict) and fold(x.get('nombre')) in allowed and clean_text(x.get('motivo'))
                        and not _text_errors('', clean_text(x['motivo']), 4, 60)][:4]
    faq = []
    for x in t.get('faq') or []:
        if not isinstance(x, dict):
            continue
        q, r = clean_text(x.get('pregunta')), clean_text(x.get('respuesta'))
        if q.endswith('?') and r and not SHOP_QUESTION.search(q) and not _text_errors('', r, 4, 90):
            faq.append({'pregunta': q if q.startswith('¿') else '¿' + q, 'respuesta': r})
    out['faq'] = faq[:5]
    if len(out['faq']) < 2:
        errors.append('faq: de 3 a 5 preguntas concretas sobre este autor, respuesta de 1 a 3 frases sin valoraciones')
    sources, urls = [], set()
    for x in t.get('fuentes') or []:
        u = clean_text(x.get('url')) if isinstance(x, dict) else ''
        if re.fullmatch(r'https://[^\s<>"]+', u) and not BAD_SOURCE.search(u) and u not in urls:
            urls.add(u)
            sources.append({'titulo': clean_text(x.get('titulo')) or re.sub(r'^https://(www\.)?', '', u).split('/')[0], 'url': u})
    out['fuentes'] = sources[:6]
    if len(out['fuentes']) < 2:
        errors.append('fuentes: al menos dos páginas consultadas con URL https completa')
    return out, errors


def publishable(p, record):
    """Lo que se publica: solo un texto identificado que pasa el validador vigente."""
    if not record or not record.get('identificado'):
        return None
    text, errors = validate(p, record)
    return None if errors else text


# ---------------------------------------------------------------- consulta

def high_power(pg, _level=None):
    """Selector de ChatGPT al máximo (High): aquí importa la búsqueda y el razonamiento, no la rapidez."""
    try:
        button = pg.locator('button[aria-label*="modelo" i], button[aria-label*="model" i]').first
        button.wait_for(state='visible', timeout=20000)
        if re.search(r'High|Alto|Pro', button.inner_text() or ''):
            return True
        button.click()
        pg.wait_for_timeout(1200)
        slider = pg.locator('[role="slider"], input[type="range"]').first
        if slider.count():
            slider.focus()
            for _ in range(4):
                pg.keyboard.press('ArrowRight')
                pg.wait_for_timeout(600)
        pg.keyboard.press('Escape')
        pg.wait_for_timeout(500)
        return bool(re.search(r'High|Alto|Pro', button.inner_text() or ''))
    except Exception:  # noqa: BLE001 - sin selector se escribe con el nivel que haya
        return False


def extract(answer):
    fenced = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', answer or '', re.S)
    tail = (answer or '')[(answer or '').find('{'):(answer or '').rfind('}') + 1]
    for chunk in fenced[::-1] + [tail]:
        try:
            value = json.loads(chunk)
        except ValueError:
            continue
        if isinstance(value, dict) and 'slug' in value:
            return value
    return None


def converse(p, port, wait_min, send=None):
    """Respuesta del autor tras hasta REPAIR_TURNS correcciones: (texto, errores) del último turno válido."""
    send = send or rt.chat
    rt.instant_power = high_power  # rt.chat llama a instant_power al abrir la pestaña: aquí va en High
    result = {'text': None, 'errors': ['sin respuesta']}

    def follow_up(answer, n):
        t = extract(answer)
        if t is None:
            result['errors'] = ['respuesta sin JSON']
            return None if n > REPAIR_TURNS else 'Devuelve otra vez la respuesta completa en un único bloque ```json con el objeto pedido.'
        text, errors = validate(p, t)
        if text is not None and (not errors or result['text'] is None or len(errors) <= len(result['errors'])):
            result.update(text=text, errors=errors)
        if not errors or n > REPAIR_TURNS:
            return None
        print(f'  turno {n + 1}: corrección ({len(errors)})', flush=True)
        return ('Algunos campos no pasan el control. Corrígelos con las mismas reglas y vuelve a enviar el objeto COMPLETO '
                'en un único bloque ```json:\n' + '\n'.join('- ' + e for e in errors))

    send(build_prompt(p), port, wait_min, follow_up)
    return result['text'], result['errors']


def save(p, text, errors, state, out=OUT):
    entry = state.get(p['slug'], {})
    h = source_hash(p)
    base = entry if entry.get('hash') == h else {'hash': h, 'intentos': 0}
    if text is not None and not errors:
        write_json(out / (p['slug'] + '.json'), {**text, 'fuente_hash': h, 'version': VERSION, 'origen': 'chatgpt-web-high',
                                                  'fecha_revision': datetime.now(ZoneInfo('Europe/Madrid')).strftime('%Y-%m-%d')})
        state[p['slug']] = {'hash': h, 'intentos': 0}
        return True
    state[p['slug']] = {**base, 'intentos': base.get('intentos', 0) + 1, 'errores': errors[:8]}
    return False


def loop(args):
    state = read_json(STATE, {})
    deadline, done, since, publishing = time.time() + args.hours * 3600, 0, 0, None
    while time.time() < deadline and done < args.max:
        data, books, authors = context()
        todo = [a for a in pending(data, books, authors, state) if not args.slug or a['slug'] in args.slug][:1]
        if not todo:
            print('Sin pendientes', flush=True)
            break
        p = payload(todo[0], data, books, authors)
        print(f'{p["slug"]} ({len(p["libros_en_la_web"])} obras en la web)', flush=True)
        try:
            text, errors = converse(p, args.port, args.wait_min)
        except Exception as exc:  # noqa: BLE001 - un fallo del navegador no gasta intentos del autor
            wait = rt.idle_seconds(exc)
            print(f'  {type(exc).__name__}: {exc}; espera {wait // 60:.0f} min', flush=True)
            if type(exc).__name__ == 'ChatGPTLoginRequired':
                return 2
            time.sleep(wait)
            continue
        ok = save(p, text, errors, state)
        write_json(STATE, state)
        done += 1
        since += ok
        print('  guardado' + (' (no identificado: no se publica)' if ok and not text.get('identificado') else '') if ok else '  rechazado: ' + '; '.join(errors), flush=True)
        # Una sola publicación a la vez: comparten el árbol .local/reading-texts/main, que cada una limpia al empezar.
        if publishing is not None and publishing.poll() is not None:
            publishing = None
        if args.publish_every and since >= args.publish_every and publishing is None:
            publishing = rt.start_publish()
            since = 0
    return 0


# ---------------------------------------------------------------- publicación (la llama reading-texts.py publish)

def copy_valid(tree, out=OUT):
    """Copia a `tree/data/reading-author-texts` los textos que pasan el validador con los datos de `tree`."""
    if not out.exists():
        return 0
    data, books, authors = context(tree)
    by_slug = {a['slug']: a for a in authors if eligible(a, books)}
    target = tree / PUBLISHED
    copied = 0
    for path in sorted(out.glob('*.json')):
        a = by_slug.get(path.stem)
        record = read_json(path)
        text = publishable(payload(a, data, books, authors), record) if a else None
        if text:
            target.mkdir(parents=True, exist_ok=True)
            write_json(target / path.name, {**text, 'fecha_revision': record['fecha_revision'], 'origen': record.get('origen')})
            copied += 1
    return copied


def main(argv=None):
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('pending')
    pr = sub.add_parser('prompt')
    pr.add_argument('--slug', required=True)
    va = sub.add_parser('validate')
    va.add_argument('files', nargs='+', type=Path)
    ru = sub.add_parser('run')
    ru.add_argument('--port', type=int, default=9240)
    ru.add_argument('--max', type=int, default=10 ** 6)
    ru.add_argument('--hours', type=float, default=24)
    ru.add_argument('--wait-min', type=int, default=25)
    ru.add_argument('--slug', nargs='*', help='solo estos autores')
    ru.add_argument('--publish-every', type=int, default=0, help='0 = solo guardar en .local')
    args = parser.parse_args(argv)
    if args.cmd == 'run':
        return loop(args)
    data, books, authors = context()
    by_slug = {a['slug']: a for a in authors}
    if args.cmd == 'pending':
        rows = pending(data, books, authors, read_json(STATE, {}))
        print(f'{len(rows)} pendientes')
        for a in rows[:20]:
            print(a['slug'], len(author_books(a, books)))
    elif args.cmd == 'prompt':
        print(build_prompt(payload(by_slug[args.slug], data, books, authors)))
    elif args.cmd == 'validate':
        bad = 0
        for path in args.files:
            record = read_json(path)
            a = by_slug.get(record.get('slug'))
            _, errors = validate(payload(a, data, books, authors), record) if a else (None, ['autor desconocido'])
            bad += bool(errors)
            print(path.stem, 'OK' if not errors else '; '.join(errors))
        return 1 if bad else 0
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
