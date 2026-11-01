#!/usr/bin/env python3
"""Orientación propia por ficha: libro -> ChatGPT web (CDP) -> validación -> data/reading-texts -> main protegido.

  pending   lista los libros publicados sin texto vigente
  prompt    imprime la consulta de un lote (--ids o los primeros pendientes)
  validate  valida ficheros de salida contra los datos actuales
  run       bucle: consulta por lotes, valida, guarda y publica cada --publish-every textos
  publish   lleva los textos guardados a main con la misma cadena que el barrido

Los textos se guardan primero en .local/reading-texts/out (ignorado por git), para que el bucle
pueda cambiar de commit sin perder nada; publish los copia a data/reading-texts en un árbol de main.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.local/reading-texts/out'
STATE = ROOT / '.local/reading-texts/state.json'
PROMPT = ROOT / 'scripts/templates/reading-texts-prompt.md'
RRSS_TOOLS = Path(os.environ.get('RRSS_TOOLS', r'C:\GIT\RRSS_DavidPorto\tools'))
VERSION = 2
MAX_ATTEMPTS = 2
MAX_BLOCKS = 3
COPY_WORDS = 8
ABSTENTIONS = {'SIN_APORTE_INCREMENTAL', 'DATOS_INSUFICIENTES', 'SERIE_NO_VERIFICADA', 'FUENTES_CONFLICTIVAS'}
# Afirmaciones que el modelo no puede sostener con los datos de entrada salvo que la sinopsis las traiga.
CLAIMS = re.compile(r'premi|galard|best ?seller|superventas|millones de|ejemplares vendidos|adaptaci|netflix|película|serie de televisi|'
                    r'la crítica|aclamad|traducid[oa] a|obra maestra|he leído|me encant|nuestra opinión|mi opinión|lo recomiendo', re.I)
# Valoraciones: la ficha orienta con hechos, no opina.
OPINION = re.compile(r'\britmo|trepidante|adictiv|apasionant|imprescindible|magistral|brillante|cautivador|emocionante|fascinante|inolvidable|'
                     r'absorbente|conmovedor|impresionante|maravillos|increíble|engancha|no te (puedes|puedas) perder|perfect[oa] para|'
                     r'ideal para|recomendamos|te encantar|una joya|bien escrit|prosa (cuidada|exquisita)', re.I)
FAMILIES = (  # Precedencia: lo infantil y lo práctico se reconocen antes que la no ficción y la narrativa.
    ('infantil', {'infantil', 'edad-de-0-a-3-anos', 'edad-a-partir-de-4-anos', 'edad-a-partir-de-7-anos'}),
    ('practico', {'cocina', 'desarrollo-personal', 'familia-y-crianza', 'nutricion-y-bienestar'}),
    ('no_ficcion', {'ensayo', 'historia', 'biografias-y-memorias', 'divulgacion-cientifica', 'filosofia'}),
)
EDITION = re.compile(r'traduc|prólogo|epílogo|introducción de|edición (especial|ilustrada|conmemorativa|limitada|revisada|anotada|definitiva|aniversario)|'
                     r'ilustrad[oa] por|ilustraciones de|cantos|notas de|apéndice|texto íntegro|edición bilingüe', re.I)
INTERACTIVE = re.compile(r'solapa|rueda|cartón|pegatina|texturas|pop-up|desplegable|sonido|actividades|colorear|juego|busca y encuentra|troquel', re.I)
CONTENTS = re.compile(r'recetas|ejercicios|índice|secciones|apartados|capítulos|pasos|técnicas|menús|planes', re.I)
MODULES = {  # módulo: (familias, necesidad del lector, condición sobre las evidencias)
    'edad_y_sensibilidad': ({'narrativa'}, 'saber si encaja por edad y contenido sensible',
                            lambda e: e.get('avisos_contenido') or e.get('edad_recomendada', 'Adultos') != 'Adultos'),
    'encaje_documentado': ({'narrativa'}, 'saber qué tipo de lectura propone según su género y premisa',
                           lambda e: len(e['sinopsis_editorial']) >= 400 and e['categorias']),
    'esta_edicion': ({'narrativa', 'no_ficcion', 'practico', 'infantil'}, 'distinguir esta edición de otras',
                     lambda e: EDITION.search(' '.join((e['sinopsis_editorial'], e.get('titulo', ''), e.get('edicion', ''))))),
    'temas_y_enfoque': ({'no_ficcion'}, 'saber qué cuestiones trata y desde qué enfoque',
                        lambda e: len(e['sinopsis_editorial']) >= 300),
    'contenido_y_uso': ({'practico'}, 'saber qué incluye y para qué sirve',
                        lambda e: CONTENTS.search(e['sinopsis_editorial'])),
    'como_se_utiliza': ({'infantil'}, 'saber cómo se usa o se juega con el libro',
                        lambda e: INTERACTIVE.search(e['sinopsis_editorial'])),
    'edad_y_formato': ({'infantil'}, 'saber si encaja por edad, formato y extensión',
                       lambda e: e.get('edad_recomendada')),
}
BASIC = {'titulo', 'autores', 'editorial', 'edicion', 'fecha_publicacion', 'numero_paginas', 'formato_edicion', 'idioma', 'isbn13'}


def load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalogue = load_module('reading_catalogue', 'scripts/build-reading-catalogue.py')


def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def published(data):
    return [b for b in data['libros'] if b['estado'] == 'publicado']


def source_text(b):
    return '\n\n'.join(x for x in (b.get('sinopsis_completa'), b.get('sinopsis_breve'), b.get('descripcion_breve')) if x)


def family(cat_ids, synopsis):
    """Familia editorial por reglas; sin sinopsis útil no hay nada que orientar."""
    if len(synopsis) < 200:
        return 'residual'
    return next((name for name, ids in FAMILIES if cat_ids & ids), 'narrativa')


def payload(data, b):
    """Lo único que ve el modelo: evidencias de la edición con clave y los módulos que admite el libro."""
    cats = catalogue.categories(data, b)
    fields = ('titulo', 'autores', 'editorial', 'edicion', 'fecha_publicacion', 'numero_paginas', 'edad_recomendada', 'formato_edicion',
              'idioma', 'isbn13', 'avisos_contenido')
    evidence = {k: b[k] for k in fields if b.get(k)}
    evidence['categorias'] = [c['nombre'] for c in cats if c['tipo'] in ('genero', 'tematica', 'epoca', 'edad')]
    evidence['sinopsis_editorial'] = source_text(b)
    fam = family({c['id'] for c in cats}, evidence['sinopsis_editorial'])
    modules = [{'modulo': m, 'titulo': catalogue.MODULE_TITLES[m], 'necesidad': need}
               for m, (fams, need, ok) in MODULES.items() if fam in fams and ok(evidence)]
    return {'id': b['id'], 'familia': fam, 'modulos_permitidos': modules, 'evidencias': evidence}


def source_hash(p):
    """Cambia si cambian los datos que sostienen el texto; no por precios ni enlaces."""
    return hashlib.sha256(json.dumps(p, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def pending(data, out=OUT, state=None):
    state = state or {}
    rows = []
    for b in published(data):
        p = payload(data, b)
        if not p['modulos_permitidos']:
            continue
        h = source_hash(p)
        saved = read_json(out / (b['id'] + '.json'))
        if saved and saved.get('fuente_hash') == h and saved.get('version') == VERSION:
            continue
        if state.get(b['id'], {}).get('hash') == h and state[b['id']].get('intentos', 0) >= MAX_ATTEMPTS:
            continue
        rows.append((bool(catalogue.amazon_destination(b)), len(p['modulos_permitidos']), b.get('fecha_publicacion') or '', b))
    # Primero lo que se puede comprar, con más evidencia aprovechable y más reciente.
    return [r[-1] for r in sorted(rows, key=lambda r: r[:3], reverse=True)]


def build_prompt(payloads):
    return PROMPT.read_text(encoding='utf-8').replace('{{LIBROS}}', json.dumps(payloads, ensure_ascii=False))


def words(text):
    return re.findall(r'\w+', unicodedata.normalize('NFKC', text).lower())


def ngrams(text, n=COPY_WORDS):
    w = words(text)
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def as_text(value):
    return ' '.join(map(str, value)) if isinstance(value, list) else str(value)


def validate_block(p, x):
    """Errores de un bloque; las cifras y los nombres tienen que estar en las evidencias que el propio bloque cita."""
    if not isinstance(x, dict) or x.get('modulo') not in {m['modulo'] for m in p['modulos_permitidos']}:
        return ['módulo no permitido']
    text, keys = x.get('texto'), x.get('evidencias')
    if not isinstance(text, str) or not 60 <= len(text.strip()) <= 420 or '\n' in text.strip():
        return ['texto: longitud o formato']
    if not isinstance(keys, list) or not keys or any(k not in p['evidencias'] for k in keys):
        return ['evidencias inexistentes']
    errors = ['más de tres frases'] if len(re.findall(r'[.!?](?:\s|$)', text.strip())) > 3 else []
    cited = ' '.join(as_text(p['evidencias'][k]) for k in keys)
    source = p['evidencias']['sinopsis_editorial']
    if ngrams(text) & ngrams(source):
        errors.append(f'copia {COPY_WORDS} palabras seguidas de la sinopsis')
    numbers = set(re.findall(r'\d+', text)) - set(re.findall(r'\d+', cited))
    if numbers:
        errors.append('cifras sin respaldo: ' + ', '.join(sorted(numbers)))
    claims = {m.group(0).lower() for m in CLAIMS.finditer(text)} - {m.group(0).lower() for m in CLAIMS.finditer(source)}
    if claims:
        errors.append('afirmaciones sin respaldo: ' + ', '.join(sorted(claims)))
    if opinion := OPINION.search(text):
        errors.append('valoración: ' + opinion.group(0).lower())
    known = set(words(cited + ' ' + p['evidencias'].get('titulo', '') + ' ' + as_text(p['evidencias'].get('autores', ''))))
    # Mayúscula a mitad de frase = nombre propio: tiene que venir de las evidencias citadas.
    names = {m.group(0) for m in re.finditer(r'[A-ZÁÉÍÓÚÑ][\wáéíóúñü]+', text)
             if (before := text[:m.start()].rstrip()) and before[-1] not in '.!?¿¡«"(:\n'}
    unknown = sorted(n for n in names if n.lower() not in known)
    if unknown:
        errors.append('nombres sin respaldo: ' + ', '.join(unknown[:5]))
    return errors


def validate_text(p, t):
    """Devuelve (bloques aceptados, errores). Un bloque malo se descarta; la ficha se pinta si supera el umbral."""
    if not isinstance(t, dict) or t.get('id') != p['id']:
        return [], ['id distinto']
    blocks = t.get('bloques')
    if not isinstance(blocks, list) or len(blocks) > MAX_BLOCKS:
        return [], ['bloques: lista inválida']
    if t.get('abstencion') is not None:
        return [], [] if not blocks and t['abstencion'] in ABSTENTIONS else ['abstención inválida']
    if not blocks:
        return [], ['sin bloques ni abstención']
    accepted, errors = [], []
    for x in blocks:
        problems = validate_block(p, x)
        if not problems and x['modulo'] in {y['modulo'] for y in accepted}:
            problems = ['módulo repetido']
        mine = set(words(x['texto'])) if not problems else set()
        if not problems and any(len(mine & set(words(y['texto']))) > 0.6 * len(mine) for y in accepted):
            problems = ['repite otro bloque']
        if problems:
            errors.append(f"{x.get('modulo') if isinstance(x, dict) else '?'}: " + '; '.join(problems))
            continue
        accepted.append({'modulo': x['modulo'], 'texto': x['texto'].strip(), 'evidencias': x['evidencias']})
    # Umbral: al menos dos evidencias distintas y una que no sea un dato bibliográfico básico.
    keys = {k for x in accepted for k in x['evidencias']}
    if accepted and (len(keys) < 2 or not keys - BASIC):
        return [], errors + ['por debajo del umbral: solo datos básicos']
    return accepted, errors


def extract_json(answer):
    fenced = re.findall(r'```(?:json)?\s*(\{.*?\})\s*```', answer, re.S)
    for chunk in fenced[::-1] + [answer[answer.find('{'):answer.rfind('}') + 1]]:
        try:
            value = json.loads(chunk)
        except ValueError:
            continue
        if isinstance(value, dict) and isinstance(value.get('fichas'), list):
            return value['fichas']
    return None


def answer_label(ids):
    def label(answer):
        rows = extract_json(answer or '')
        if rows is None:
            return 'JSON_TRUNCADO'
        return 'JSON_VALIDO' if sorted(r.get('id') for r in rows if isinstance(r, dict)) == sorted(ids) else 'IDS_INCORRECTOS'
    return label


def save_results(payloads, rows, state, out=OUT):
    by_id = {r.get('id'): r for r in rows if isinstance(r, dict)}
    saved = rejected = 0
    for p in payloads:
        entry = state.setdefault(p['id'], {})
        h = source_hash(p)
        if entry.get('hash') != h:
            entry.update(hash=h, intentos=0)
        entry['intentos'] += 1
        t = by_id.get(p['id'])
        blocks, errors = ([], ['sin respuesta']) if t is None else validate_text(p, t)
        entry['errores'] = errors
        if not blocks and errors:  # sin nada aprovechable: se reintenta hasta MAX_ATTEMPTS
            rejected += 1
            continue
        record = {'id': p['id'], 'familia': p['familia'], 'bloques': blocks, 'abstencion': t.get('abstencion'),
                  'descartados': errors, 'version': VERSION, 'fuente_hash': h, 'origen': 'chatgpt-web'}
        write_json(out / (p['id'] + '.json'), record)
        saved += 1
    return saved, rejected


def consult(question, ids, port, wait_min):
    os.environ['RRSS_CHATGPT_CDP_PORT'] = str(port)
    sys.path.insert(0, str(RRSS_TOOLS))
    import chatgpt_consult
    repair = 'Devuelve otra vez la respuesta completa: un único bloque ```json con {"fichas": [...]} y exactamente estos id: ' + ', '.join(ids)
    answer, _ = chatgpt_consult.consult(question, (), wait_min, validate=answer_label(ids), repair=repair)
    return answer


def git(*args, cwd=ROOT, capture=False):
    if capture:
        return subprocess.check_output(['git', *args], cwd=cwd, text=True)
    subprocess.run(['git', *args], cwd=cwd, check=True)


def publish(out=OUT):
    """Copia los textos a un árbol limpio de origin/main y publica con el flujo protegido del barrido."""
    texts = sorted(out.glob('*.json'))
    if not texts:
        print('Sin textos que publicar')
        return False
    tree = ROOT / '.local/reading-texts/main'
    git('fetch', '-q', 'origin', 'main')
    if not tree.exists():
        git('worktree', 'add', '--detach', str(tree), 'origin/main')
    git('reset', '-q', '--hard', 'origin/main', cwd=tree)
    git('clean', '-qfd', cwd=tree)
    data = read_json(tree / 'data/reading-catalogue.json')
    ids = {b['id'] for b in published(data)}
    target = tree / 'data/reading-texts'
    target.mkdir(exist_ok=True)
    for path in texts:
        if path.stem in ids and read_json(path).get('bloques'):  # las abstenciones solo cuentan en .local
            shutil.copyfile(path, target / path.name)
    run = lambda *cmd: subprocess.run([sys.executable, *cmd], cwd=tree, check=True)
    for script in ('build-reading-catalogue.py', 'build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        run('scripts/' + script)
    for script in ('build-reading-catalogue.py', 'build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        run('scripts/' + script, '--check')
    run('tests/test-reading-catalogue.py')
    run('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_reading*.py', '-q')
    paths = [line[3:] for line in git('status', '--porcelain', '--untracked-files=all', cwd=tree, capture=True).splitlines()]
    if not paths:
        print('Los textos ya están en main')
        return False
    publisher = load_module('publish_reading_refresh', 'scripts/publish-reading-refresh.py')
    outside = [p for p in paths if not publisher.allowed_path(p)]
    if outside:
        raise ValueError('Cambios fuera de los artefactos permitidos: ' + str(outside))
    now = datetime.now(ZoneInfo('Europe/Madrid'))
    branch = 'automation/reading-catalogue-textos-' + now.strftime('%Y-%m-%d-%H%M%S')
    count = len([p for p in paths if p.startswith('data/reading-texts/')])
    git('switch', '-q', '-c', branch, cwd=tree)
    git('add', '--', *paths, cwd=tree)
    git('commit', '-q', '-m', f'Orientación propia en {count} fichas de lectura', cwd=tree)
    git('push', '-q', 'origin', 'HEAD:refs/heads/' + branch, cwd=tree)
    body = tree.parent / 'pr-body.md'
    body.write_text(f'Añade texto propio validado a {count} fichas: por qué leerlo, para quién, tono, libros afines del catálogo y preguntas frecuentes.\n\n'
                    'Cada texto pasa el validador de scripts/reading-texts.py (sin copia de la sinopsis, sin cifras, nombres ni premios sin respaldo). '
                    'Se ejecutan las reglas de main antes de fusionar y después se despliega.\n', encoding='utf-8')
    for old in json.loads(publisher.publication.gh('pr', 'list', '--state', 'open', '--json', 'number,headRefName')):
        if old['headRefName'].startswith('automation/reading-catalogue-textos-'):
            publisher.publication.gh('pr', 'close', str(old['number']), '--comment', 'Sustituida por una publicación de textos más reciente.')
    publisher.publication.gh('pr', 'create', '--base', 'main', '--head', branch,
                             '--title', f'Orientación propia en {count} fichas de lectura', '--body-file', str(body))
    git('switch', '-q', '--detach', cwd=tree)
    publisher.run(branch)
    return True


def loop(args):
    state = read_json(STATE, {})
    data = read_json(ROOT / 'data/reading-catalogue.json')
    deadline = time.time() + args.hours * 3600
    done = since_publish = 0
    while time.time() < deadline and done < args.max_books:
        books = pending(data, state=state)[:args.batch]
        if not books:
            print('Sin pendientes', flush=True)
            break
        payloads = [payload(data, b) for b in books]
        ids = [p['id'] for p in payloads]
        try:
            answer = consult(build_prompt(payloads), ids, args.port, args.wait_min)
            rows = extract_json(answer) or []
        except Exception as exc:  # noqa: BLE001 - un lote fallido no para el bucle
            print(f'Lote {ids[0]}…: {type(exc).__name__}', flush=True)
            rows = []
        saved, rejected = save_results(payloads, rows, state)
        write_json(STATE, state)
        done += len(books)
        since_publish += saved
        print(f'Lote de {len(books)}: {saved} guardados, {rejected} rechazados', flush=True)
        if args.publish_every and since_publish >= args.publish_every:
            try:
                publish()
                since_publish = 0
            except Exception as exc:  # noqa: BLE001 - se reintenta en la siguiente tanda
                print(f'Publicación fallida: {exc}', flush=True)
        if args.refresh_data:
            git('fetch', '-q', 'origin', 'main')
            data = json.loads(git('show', 'origin/main:data/reading-catalogue.json', capture=True))
    if args.publish_every and since_publish:
        publish()


def main(argv=None):
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('pending')
    pr = sub.add_parser('prompt')
    pr.add_argument('--ids', nargs='*')
    pr.add_argument('--batch', type=int, default=5)
    va = sub.add_parser('validate')
    va.add_argument('files', nargs='+', type=Path)
    ru = sub.add_parser('run')
    ru.add_argument('--port', type=int, default=9240)
    ru.add_argument('--batch', type=int, default=5)
    ru.add_argument('--max-books', type=int, default=10 ** 6)
    ru.add_argument('--hours', type=float, default=24)
    ru.add_argument('--wait-min', type=int, default=20)
    ru.add_argument('--publish-every', type=int, default=0, help='0 = solo guardar en .local')
    ru.add_argument('--refresh-data', action='store_true', help='releer el catálogo de origin/main tras cada lote')
    sub.add_parser('publish')
    args = parser.parse_args(argv)
    data = read_json(ROOT / 'data/reading-catalogue.json')
    if args.cmd == 'pending':
        rows = pending(data, state=read_json(STATE, {}))
        print(f'{len(rows)} pendientes')
        for b in rows[:20]:
            print(b['id'], b['titulo'])
    elif args.cmd == 'prompt':
        books = [b for b in published(data) if b['id'] in args.ids] if args.ids else pending(data)[:args.batch]
        print(build_prompt([payload(data, b) for b in books]))
    elif args.cmd == 'validate':
        by_id = {b['id']: b for b in published(data)}
        bad = 0
        for path in args.files:
            t = read_json(path)
            for row in (t['fichas'] if 'fichas' in t else [t]):
                blocks, errors = validate_text(payload(data, by_id[row['id']]), row) if row.get('id') in by_id else ([], ['libro desconocido'])
                bad += bool(errors)
                print(row.get('id'), f'{len(blocks)} bloques', 'OK' if not errors else '; '.join(errors))
        return 1 if bad else 0
    elif args.cmd == 'run':
        loop(args)
    elif args.cmd == 'publish':
        publish()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
