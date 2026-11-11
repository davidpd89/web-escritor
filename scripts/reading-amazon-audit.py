#!/usr/bin/env python3
"""Auditoría continua de Amazon, libro a libro, desde este equipo.

  run       bucle: audita la ficha de Amazon de cada libro publicado (el más antiguo primero), guarda el registro
            en .local y publica a las horas de --publish-at en segundo plano
  publish   aplica el registro a un árbol limpio de origin/main: formatos que faltan, portadas reales y
            data/reading-amazon-audit.json; pruebas locales y PR con el flujo protegido del barrido

Sin cupo de libros: el ritmo lo marca la pausa entre fichas y, si Amazon pide captcha, una espera creciente.
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_amazon_market import audit_book, apply_audit, cover_kind, fetch_amazon_image, fetch_amazon_page, replace_cover  # noqa: E402

LOCAL = ROOT / '.local/reading-amazon-audit'
RECORD = LOCAL / 'audit.json'
PUBLISHED = 'data/reading-amazon-audit.json'
AUDIT_AFTER = timedelta(days=7)  # un libro auditado bien se repasa cada semana
RETRY_AFTER = timedelta(days=1)  # sin ASIN todavía (la API lo busca cada noche), sin ficha o error: al día siguiente
PAUSE = 15  # segundos entre fichas, además de los 2 de fetch_amazon_page
MADRID = ZoneInfo('Europe/Madrid')
# Portadas reales por publicación (~65 kB cada una con su miniatura): unas 50 MB por PR; el resto, en la siguiente.
COVERS_PER_PUBLISH = 800


def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def git(*args, cwd=ROOT, capture=False):
    if capture:
        return subprocess.check_output(['git', *args], cwd=cwd, text=True, encoding='utf-8')
    subprocess.run(['git', *args], cwd=cwd, check=True)


def due(data, records, now):
    """Libros publicados por auditar, los que llevan más tiempo sin mirar primero."""
    def last(b):
        r = records.get(b['id'])
        if not r:
            return ''
        wait = AUDIT_AFTER if r.get('estado') in ('ok', 'otra_obra') else RETRY_AFTER
        return None if r['fecha'] > (now - wait).date().isoformat() else r['fecha']  # auditado hace poco: aún no
    books = [(last(b), b) for b in data['libros'] if b.get('estado') == 'publicado']
    return [b for when, b in sorted(((w, b) for w, b in books if w is not None), key=lambda x: x[0])]


def loop(args):
    records = read_json(RECORD, {})
    deadline = time.time() + args.hours * 3600
    backoff, publishing, last, data, loaded = 0, None, '', None, 0
    while time.time() < deadline:
        now = datetime.now(MADRID)
        if publishing is not None and publishing.poll() is not None:
            print(f'Publicación terminada ({publishing.returncode})', flush=True)
            publishing = None
        if publishing is None and now.hour in args.publish_at and now.strftime('%Y-%m-%d %H') != last and records:
            publishing, last = start_publish(), now.strftime('%Y-%m-%d %H')
            print('Publicación lanzada en segundo plano', flush=True)
        if data is None or time.time() - loaded > 1800:  # libros nuevos de la ingesta
            try:
                git('fetch', '-q', 'origin', 'main')
                data, loaded = json.loads(git('show', 'origin/main:data/reading-catalogue.json', capture=True)), time.time()
            except (subprocess.CalledProcessError, ValueError) as exc:
                print(f'Catálogo sin refrescar: {exc}', flush=True)
                if data is None:
                    time.sleep(300)
                    continue
        books = due(data, records, now)
        if not books:
            time.sleep(600)
            continue
        book = books[0]
        record = audit_book(book, fetch_amazon_page, now.date().isoformat())
        if record is None:
            backoff = min(max(backoff * 2, 300), 3600)
            print(f'Amazon pide captcha: espera {backoff // 60} min', flush=True)
            time.sleep(backoff)
            continue
        backoff = 0
        records[book['id']] = record
        write_json(RECORD, records)
        print(f"{book['id']}: {record['estado']} amazon={','.join(record['amazon']) or '-'} faltan={','.join(record['faltan']) or '-'}", flush=True)
        time.sleep(PAUSE)
    if publishing is not None:
        publishing.wait()


def start_publish():
    LOCAL.mkdir(parents=True, exist_ok=True)
    log = open(LOCAL / 'publish.log', 'a', encoding='utf-8')
    log.write(f'--- {datetime.now(MADRID):%Y-%m-%d %H:%M} publicación\n')
    log.flush()
    return subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()), 'publish'], cwd=ROOT, stdout=log, stderr=log,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def days_from(book, today):
    """Distancia en días entre la fecha de publicación (completa, solo mes o solo año) y hoy; sin fecha, al final."""
    value = (book.get('fecha_publicacion') or '')[:10]
    if len(value) in (4, 7):
        value += '-01-01'[len(value) - 4:]
    try:
        return abs((date.fromisoformat(value) - today).days)
    except ValueError:
        return 10 ** 6


RATING_DAYS = 30  # como las de Goodreads: el bucle vuelve a auditar cada libro antes de que caduque


def stamp(moment):
    return moment.isoformat(timespec='seconds').replace('+00:00', 'Z')


def apply_ratings(tree, published, tag):
    """Estrellas de la ficha de Amazon que la auditoría ya descargó: una valoración «amazon» por libro, fechada el
    día de la auditoría. Las de otras fuentes no se tocan. Devuelve cuántos libros tienen nota de Amazon."""
    found = {}
    for book, record in published:
        rating, asin = record.get('valoracion'), record.get('asin')
        if record.get('estado') != 'ok' or not isinstance(rating, dict) or not asin:
            continue
        start = datetime.fromisoformat(record['fecha']).replace(tzinfo=timezone.utc)
        found[book['id']] = {'libro_id': book['id'], 'puntuacion': rating['puntuacion'],
                             'numero_valoraciones': rating['numero_valoraciones'], 'fuente': 'amazon',
                             'url': f'https://www.amazon.es/dp/{asin}?tag={tag}#customerReviews',
                             'actualizado_en': stamp(start), 'caduca_en': stamp(start + timedelta(days=RATING_DAYS))}
    if not found:
        return 0
    from reading_ratings_refresh import write_changed
    path = tree / 'assets/reading-market.json'
    market = read_json(path, {'schema_version': 1, 'offers': [], 'ratings': []})
    kept = [r for r in market.get('ratings', []) if not (r.get('fuente') == 'amazon' and r.get('libro_id') in found)]
    market['ratings'] = kept + [found[k] for k in sorted(found)]
    write_changed(path, market)
    return len(found)


def apply_records(tree, records, tag, fetch_bytes=fetch_amazon_image, convert=None, today=None, covers=COVERS_PER_PUBLISH):
    """Lleva el registro al catálogo del árbol: formatos que faltan y portada real donde la nuestra es generada.
    La portada se decide por el libro tal como está en main, no por lo que decía el registro al auditarlo: antes
    de reconocer las tipográficas de la ingesta de Amazon, 1449 quedaron registradas como «editorial».
    Con más portadas que el tope, primero las de los libros que salen o salieron más cerca de hoy."""
    if convert is None:
        from reading_intake_pipeline import amazon_cover_bytes as convert
    today = today or datetime.now(MADRID).date()
    data = read_json(tree / 'data/reading-catalogue.json')
    stats = {'formats_added': 0, 'covers_replaced': 0}
    published = [(book, records[book['id']]) for book in data['libros']
                 if book.get('estado') == 'publicado' and records.get(book['id'])]
    for book, record in published:
        stats['formats_added'] += apply_audit(book, record, tag)
    pending = [(book, record) for book, record in published
               if cover_kind(book) == 'generada' and record.get('portada_amazon') and book.get('portada_local')]
    for book, record in sorted(pending, key=lambda pair: days_from(pair[0], today)):
        if stats['covers_replaced'] >= covers:
            break
        try:
            image, small, size = convert(fetch_bytes(record['portada_amazon']))
        except Exception:  # marcador, imagen pequeña o proporción rara: se queda la tipográfica
            continue
        if replace_cover(book, tree, image, small, size, record['portada_amazon'], record['fecha']):
            stats['covers_replaced'] += 1
    stats['ratings'] = apply_ratings(tree, published, tag)
    public = {}
    for book, record in published:
        shown = [o['formato'] for o in book.get('formatos_compra', [])]
        public[book['id']] = {**record, 'mostrados': shown, 'faltan': [f for f in record['amazon'] if f not in shown],
                              'portada': cover_kind(book)}
    write_json(tree / 'data/reading-catalogue.json', data)
    write_json(tree / PUBLISHED, {'nota': 'Registro por libro de la ficha de Amazon frente a lo que muestra la web; '
                                          'lo escribe scripts/reading-amazon-audit.py.',
                                  'libros': dict(sorted(public.items()))})
    return stats


def load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def publish():
    records = read_json(RECORD, {})
    if not records:
        print('Sin registro que publicar')
        return False
    publisher = load_module('publish_reading_refresh', 'scripts/publish-reading-refresh.py')
    tree = publisher.clean_main_tree(ROOT, LOCAL / 'main')
    config = read_json(tree / 'data/reading-intake-config.json')
    stats = apply_records(tree, records, config['amazon_partner_tag'])
    print('Auditoría aplicada: ' + json.dumps(stats), flush=True)
    run = lambda *cmd: subprocess.run([sys.executable, *cmd], cwd=tree, check=True)
    scripts = ('build-reading-catalogue.py', 'build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py')
    for script in scripts:
        run('scripts/' + script)
    for script in scripts:
        run('scripts/' + script, '--check')
    run('scripts/check-reading-data.py')  # el código lo prueba el Required merge gate; aquí, solo los datos
    paths = [line[3:] for line in git('status', '--porcelain', '--untracked-files=all', cwd=tree, capture=True).splitlines()]
    if not paths:
        print('La auditoría ya está en main')
        return False
    outside = [p for p in paths if not publisher.allowed_path(p)]
    if outside:
        raise ValueError('Cambios fuera de los artefactos permitidos: ' + str(outside))
    branch = 'automation/reading-catalogue-amazon-' + datetime.now(MADRID).strftime('%Y-%m-%d-%H%M%S')
    title = f"Amazon: {stats['formats_added']} formatos y {stats['covers_replaced']} portadas; registro de {len(records)} fichas"
    git('switch', '-q', '-c', branch, cwd=tree)
    subprocess.run(['git', 'add', '--pathspec-from-file=-', '--pathspec-file-nul'], cwd=tree, check=True,
                   input='\0'.join(paths).encode('utf-8'))
    git('commit', '-q', '-m', title, cwd=tree)
    git('push', '-q', 'origin', 'HEAD:refs/heads/' + branch, cwd=tree)
    body = LOCAL / 'pr-body.md'
    body.write_text('Auditoría continua de la ficha de Amazon de cada libro publicado (scripts/reading-amazon-audit.py): '
                    'añade los formatos que Amazon vende y la web no mostraba, cambia las portadas generadas por la real '
                    f'y actualiza {PUBLISHED}. Los precios los pone el barrido nocturno de la API.\n', encoding='utf-8')
    for old in json.loads(publisher.publication.gh('pr', 'list', '--state', 'open', '--json', 'number,headRefName')):
        if old['headRefName'].startswith('automation/reading-catalogue-amazon-'):
            publisher.publication.gh('pr', 'close', str(old['number']), '--comment', 'Sustituida por una auditoría más reciente.')
    publisher.publication.gh('pr', 'create', '--base', 'main', '--head', branch, '--title', title, '--body-file', str(body))
    git('switch', '-q', '--detach', cwd=tree)
    publisher.run(branch)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    ru = sub.add_parser('run')
    ru.add_argument('--hours', type=float, default=23.5)
    ru.add_argument('--publish-at', type=int, nargs='*', default=[18], help='horas de Madrid a las que publicar')
    sub.add_parser('publish')
    args = parser.parse_args(argv)
    if args.cmd == 'run':
        loop(args)
    else:
        # La autorreparación vigila esta publicación como un workflow más (scripts/estado_local.py).
        import estado_local
        with estado_local.vigilado('publicacion-amazon', LOCAL / 'publish.log',
                                   [sys.executable, '-u', str(Path(__file__).resolve()), 'publish'], ROOT):
            publish()


if __name__ == '__main__':
    main()
