"""Revisión de la clasificación del catálogo entero con GPT (High y búsqueda web), por lotes.

GPT ve cada libro con su clasificación actual y señala los géneros que confunden al lector («sobran»: Narnia no es
terror, un atlas de la Biblia no es humor) y los que le corresponden. La opinión se guarda por libro en
.local/reading-classification-review/opiniones.json; la publicación de textos (scripts/reading-texts.py) la lleva a
data/reading-classification-review.json y reading_taxonomy.apply_review la aplica en cada carga.

  python scripts/reading-classification-review.py run [--pestanas 2] [--lote 60] [--puerto 9262]
  python scripts/reading-classification-review.py lote N salida.txt | importar respuesta.txt | estado
  python scripts/reading-classification-review.py aplicar   # repara el catálogo de este árbol con la revisión

Un libro vuelve a la cola si gana un género que GPT no vio ni propuso (la clasificación cambió después de revisarlo).
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / 'data/reading-catalogue.json'
STATE = ROOT / '.local/reading-classification-review'
OPS = STATE / 'opiniones.json'
DRIVER = ROOT / 'scripts/gpt-consulta.mjs'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
FICTION = {'terror', 'misterio-y-thriller', 'fantasia', 'fantasia-juvenil', 'fantasia-oscura', 'ciencia-ficcion',
           'romance', 'romantasy', 'novela-historica', 'narrativa', 'aventuras', 'relatos', 'humor', 'narrativa-juvenil'}
NON_FICTION = {'ensayo', 'divulgacion-cientifica', 'desarrollo-personal', 'historia', 'filosofia', 'psicologia', 'cocina',
               'guias-y-referencia', 'religion-y-espiritualidad', 'arte-y-diseno', 'viajes', 'economia-y-empresa',
               'derecho', 'familia-y-crianza', 'nutricion-y-bienestar', 'ocio-y-aficiones', 'politica-y-actualidad'}
PUBLICOS = ('infantil', 'juvenil', 'adultos')
MIN_MOTIVO = 20  # reading_taxonomy.review_drop no aplica un «sobran» con un motivo más corto

PROMPT = '''Eres un librero experto. Revisa la clasificación de estos libros de un catálogo español. Para cada libro di:
- "generos": de 1 a 3 géneros de ESTA lista cerrada (escribe el nombre exacto), el principal primero: {gen}.
  Ficción solo si la obra es ficción: una guía, atlas o enciclopedia SOBRE fantasía o terror no es fantasía ni terror (es Guías y referencia, Arte y diseño, Ensayo...). Humor solo si el libro es de humor, no porque sea ameno. Infantil = libros para niños hasta ~12 años; Narrativa juvenil = novela para adolescentes.
- "publico": "infantil", "juvenil" o "adultos".
- "sobran": nombres exactos de géneros de "clasificacion_actual" que están MAL para este libro (lista vacía si todos valen). No pongas aquí uno solo por ser secundario: solo los que confunden al lector (Narnia no es Terror; un atlas de la Biblia no es Humor).
- "motivo": si "sobran" no está vacío o tu público difiere, una frase concreta con el dato que lo respalda; si no, "".
Busca en internet (ficha de la editorial, Goodreads, Casa del Libro, Wikipedia) los libros que no conozcas; no adivines por el título.
Responde SOLO con un bloque ```json con esta forma: {{"libros": [{{"id": "...", "generos": [...], "publico": "...", "sobran": [...], "motivo": "..."}}]}} y un elemento por libro, en el mismo orden.

Libros:
{libros}
'''


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True), encoding='utf-8')
    os.replace(tmp, path)


class Catalogo:
    def __init__(self, path=CATALOGUE):
        cat = json.loads(Path(path).read_text(encoding='utf-8'))
        self.names = {c['id']: c['nombre'] for c in cat['categorias']}
        self.genres = [c['id'] for c in cat['categorias'] if c['tipo'] == 'genero' and c.get('activa', True)]
        self.by = {}
        for r in cat['libro_categorias']:
            self.by.setdefault(r['libro_id'], set()).add(r['categoria_id'])
        self.books = {b['id']: b for b in cat['libros'] if b.get('estado') == 'publicado'}
        self.inv = {re.sub(r'\s+', ' ', v).casefold(): k for k, v in self.names.items() if k in self.genres}

    def current(self, ident):
        return self.by.get(ident, set()) & set(self.genres)

    def pending(self, ops):
        """Sin opinión, o con un género actual que GPT no vio ni propuso."""
        out = []
        for i in self.books:
            op = ops.get(i)
            if not op or self.current(i) - set(op.get('genero_nuestro') or []) - set(op.get('generos_gpt') or []):
                out.append(i)
        return out

    def score(self, ident):
        """Sospecha: los más probables de estar mal van primero."""
        b, g = self.books[ident], self.current(ident)
        s = 3 * (len(g) >= 4) + 3 * bool(g & FICTION and g & NON_FICTION and 'biografias-y-memorias' not in g)
        s += 3 * bool('infantil' in g and g & {'terror', 'romantasy', 'misterio-y-thriller', 'romance'})
        s += 2 * bool(re.search(r'\b(atlas|enciclopedia|diccionario|gu[ií]a|manual)\b', b.get('titulo', ''), re.I)
                      and g & FICTION)
        return s + 2 * ('terror' in g) + (len(g) == 0) + ('amazon.es' in (b.get('fuente_bibliografica_url') or ''))

    def ficha(self, ident):
        b = self.books[ident]
        m = re.search(r'La editorial la incluye en ([^.]*)\.', b.get('descripcion_breve') or '')
        sin = (b.get('sinopsis_completa') or b.get('sinopsis_breve') or '').replace('\n', ' ')
        return {'id': ident, 'titulo': b.get('titulo'), 'autores': b.get('autores'), 'editorial': b.get('editorial'),
                'paginas': b.get('numero_paginas'), 'materias_editorial': m[1] if m else None,
                'sinopsis': sin[:420] or None,
                'clasificacion_actual': [self.names[x] for x in sorted(self.current(ident))]}

    def prompt(self, ids):
        return PROMPT.format(gen='; '.join(self.names[g] for g in self.genres),
                             libros=json.dumps([self.ficha(i) for i in ids], ensure_ascii=False, indent=0))

    def genre(self, name):
        return self.inv.get(re.sub(r'\s+', ' ', str(name)).casefold().strip())


def extract(text):
    m = re.search(r'\{\s*"libros"\s*:.*\}', text or '', re.S)
    if not m:
        return None
    raw = m[0]
    for end in range(len(raw), 0, -1):  # recorta lo que GPT pega tras el JSON
        if raw[end - 1] == '}':
            try:
                return json.loads(raw[:end])
            except ValueError:
                continue
    return None


def parse(cat, text, asked=None):
    """Opiniones válidas de una respuesta: {id: opinión}. Un nombre fuera de la lista (un público escrito como
    género, «Infantil y juvenil») se ignora sin tumbar la opinión; un «sobran» solo cuenta si el libro lo tiene."""
    data = extract(text)
    out = {}
    for e in (data or {}).get('libros', []):
        i = e.get('id') if isinstance(e, dict) else None
        if i not in cat.books or (asked is not None and i not in asked):
            continue
        gs = [g for x in e.get('generos') or [] if (g := cat.genre(x))]
        so = [g for x in e.get('sobran') or [] if (g := cat.genre(x)) and g in cat.current(i)]
        pub = str(e.get('publico') or '').casefold().strip()
        if not gs or pub not in PUBLICOS:
            continue
        out[i] = {'generos_gpt': list(dict.fromkeys(gs)), 'publico_gpt': pub, 'sobran': sorted(set(so)),
                  'motivo': str(e.get('motivo') or '').strip(), 'genero_nuestro': sorted(cat.current(i)),
                  'fecha': time.strftime('%Y-%m-%d')}
    return out


def edge_alive(port, launch=True):
    """Si el Edge del puerto no responde se abre con su perfil (la sesión de ChatGPT vive en el perfil)."""
    for attempt in range(2):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/json/version', timeout=5)
            return True
        except OSError:
            if attempt or not launch or not Path(EDGE).exists():
                return False
            subprocess.Popen([EDGE, f'--remote-debugging-port={port}',
                              '--user-data-dir=' + str(Path.home() / f'.edge-gpt-{port}'),
                              '--start-minimized', '--no-first-run', 'about:blank'])
            time.sleep(20)
    return False


def ask(question, answer, port):
    """Una consulta en su propia pestaña; el conductor la cierra siempre (también en error o fin de plazo)."""
    env = {**os.environ, 'GPT_PUERTO': str(port)}
    r = subprocess.run(['node', str(DRIVER), str(question), str(answer)], capture_output=True, text=True,
                       encoding='utf-8', errors='replace', timeout=1900, env=env, cwd=ROOT)
    return r.returncode, (r.stdout + r.stderr)[-300:].replace('\n', ' ')


def run(args):
    if str(args.puerto) == '9240':
        raise SystemExit('9240 es el Edge de los textos: usa otro puerto')
    STATE.mkdir(parents=True, exist_ok=True)
    fails = rounds = 0
    while not args.rondas or rounds < args.rondas:
        rounds += 1
        cat, ops = Catalogo(), read_json(OPS, {})
        queue = sorted(cat.pending(ops), key=lambda i: (-cat.score(i), i))
        if not queue:
            print('FIN: catálogo revisado', flush=True)
            return 0
        if not edge_alive(args.puerto):
            print(time.strftime('%H:%M'), f'Edge {args.puerto} no responde', flush=True)
        batches = [queue[k * args.lote:(k + 1) * args.lote] for k in range(args.pestanas)]
        batches = [b for b in batches if b]
        for k, ids in enumerate(batches):
            (STATE / f'pregunta-{k}.txt').write_text(cat.prompt(ids), encoding='utf-8')
            (STATE / f'respuesta-{k}.txt').unlink(missing_ok=True)
        with cf.ThreadPoolExecutor(len(batches)) as ex:
            results = list(ex.map(lambda k: ask(STATE / f'pregunta-{k}.txt', STATE / f'respuesta-{k}.txt',
                                                args.puerto), range(len(batches))))
        ops = read_json(OPS, {})
        for k, (ids, (rc, tail)) in enumerate(zip(batches, results)):
            got = parse(cat, read_json_text(STATE / f'respuesta-{k}.txt'), set(ids)) if rc == 0 else {}
            ops.update(got)
            fails = 0 if got else fails + 1
            print(time.strftime('%H:%M'), f'ronda {rounds} pestaña {k}:', f'{len(got)}/{len(ids)}' if rc == 0
                  else f'fallo {rc} {tail}', flush=True)
        write_json(OPS, ops)
        print(estado(cat, ops, quiet=True), flush=True)
        if fails >= 6:
            print('PARO: 6 lotes seguidos sin respuesta válida (¿sesión de ChatGPT caída?)', flush=True)
            return 1
        if fails:
            time.sleep(90 * fails)  # un fallo pasajero (Edge reiniciando, GPT ocupado) no agota los intentos
    return 0


def read_json_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except OSError:
        return ''


def estado(cat=None, ops=None, quiet=False):
    cat, ops = cat or Catalogo(), read_json(OPS, {}) if ops is None else ops
    flagged = {i: o for i, o in ops.items() if o.get('sobran') and len(o.get('motivo', '')) >= MIN_MOTIVO}
    line = (f'opiniones {len(ops)} de {len(cat.books)} | con sobran {len(flagged)} | '
            f'pendientes {len(cat.pending(ops))}')
    if quiet:
        return line
    print(line)
    for i, o in list(flagged.items())[-40:]:
        if i in cat.books:
            print(cat.books[i]['titulo'][:55], '|', o['genero_nuestro'], '-> sobran', o['sobran'], '|', o['motivo'][:110])
    return None


def aplicar():
    """Aplica data/reading-classification-review.json al catálogo de este árbol (la carga nocturna lo hace sola)."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from reading_taxonomy import repair_classification
    from reading_ratings_refresh import write_changed
    data = json.loads(CATALOGUE.read_text(encoding='utf-8'))
    original = json.loads(json.dumps(data))
    repair_classification(data, today=time.strftime('%Y-%m-%d'))
    if data != original:
        write_changed(CATALOGUE, data)
        print('catálogo reparado con la revisión')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--pestanas', type=int, default=2)  # cada pestaña de ChatGPT ocupa cientos de MB
    r.add_argument('--lote', type=int, default=60)
    r.add_argument('--puerto', default=os.environ.get('GPT_PUERTO', '9262'))
    r.add_argument('--rondas', type=int, default=0, help='0 = hasta revisar todo')
    lo = sub.add_parser('lote')
    lo.add_argument('n', type=int)
    lo.add_argument('salida')
    im = sub.add_parser('importar')
    im.add_argument('respuesta')
    sub.add_parser('estado')
    sub.add_parser('aplicar')
    args = ap.parse_args(argv)
    if args.cmd == 'run':
        return run(args)
    if args.cmd == 'lote':
        cat = Catalogo()
        ids = sorted(cat.pending(read_json(OPS, {})), key=lambda i: (-cat.score(i), i))[:args.n]
        Path(args.salida).write_text(cat.prompt(ids), encoding='utf-8')
        print(len(ids), 'libros')
        return 0
    if args.cmd == 'importar':
        cat, ops = Catalogo(), read_json(OPS, {})
        got = parse(cat, read_json_text(args.respuesta))
        ops.update(got)
        write_json(OPS, ops)
        print('importadas', len(got))
        return 0 if got else 1
    if args.cmd == 'aplicar':
        return aplicar()
    estado()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
