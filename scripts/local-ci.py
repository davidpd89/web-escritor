#!/usr/bin/env python3
"""Puerta local equivalente al CI de un PR, antes de subirlo.

Lee .github/workflows: los workflows de pull_request cuyas `paths` casan con los cambios frente a origin/main
y, de sus pasos, las líneas `node qa/*.mjs`, `python … --check` y las pruebas. Las corre aquí en paralelo con los
servidores que esperan (4173 y 4175, que se sirven en puertos libres para que quepan varias puertas a la vez) y, con --baseline, repite los fallos sobre origin/main: lo que también falla
allí ya estaba roto y no bloquea este cambio.

  python scripts/local-ci.py                # lo que correría el CI para los cambios de esta rama
  python scripts/local-ci.py --baseline     # y separa los fallos que ya trae main
  python scripts/local-ci.py --all          # todos los pasos, sin mirar las rutas

Salida: 0 sin fallos nuevos, 1 con fallos nuevos, 2 si algo agotó el tiempo y queda sin verificar.
"""
import argparse
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORTS = (4173, 4175)
TIMEOUT = 900
# Pruebas y comprobaciones de solo lectura: node qa|tests, node --check|--test, python tests, check-*/audit-* y
# cualquier `--check`. Los generadores sin --check quedan fuera porque escriben en el árbol.
COMMAND = re.compile(r'^((?:[A-Z_][A-Z0-9_]*=\S+\s+)*)(node (?:--check \S+|--test \S+|(?:qa|tests)/\S+\.mjs.*'
                     r'|scripts/test-\S+\.mjs.*|scripts/\S+\.mjs.*--check.*)|python3? (?:-m (?:unittest|py_compile|compileall).*'
                     r'|tests/\S+.*|scripts/(?:check|audit)[-_]\S+\.py.*|scripts/\S+.*--check.*))$')
# Una línea que construye (`python scripts/build-public-dist.py`) y las siguientes del mismo paso, que leen lo
# construido (`--check-contents`): en GitHub corren en orden dentro de un bash -e. Antes se partían y la comprobación
# corría sola, sin lo construido: «ya fallaba en main» siempre.
PRODUCTOR = re.compile(r'^(python3?|node) scripts/build[-_][^\s$]+(?: [^$|;&>]*)?$')
# Preparación del paso que también va delante del comando: `mkdir -p artifacts/x` antes de `| tee artifacts/x/log`
# y `set -o pipefail`. Antes se descartaban: el tee fallaba en local sin la carpeta y salía «inestable».
PREPARA = re.compile(r'^(?:mkdir -p [^$|;&>]+|set (?:-[eu]+|-o pipefail)(?: -o pipefail)?)$')
# Dependen de artefactos que en CI crea un paso anterior (dist de vista previa, zip, informe de lychee).
NEEDS_BUILD = ('.preview-dist', 'qa-artifacts/', 'lychee/')
# La suite unittest completa pasa de 15 min en un solo proceso: se reparte en lotes que corren en paralelo.
SUITE = "python -m unittest discover -s tests -p 'test_*.py'"
SHARDS = 8
BASH = shutil.which('bash') or r'C:\Program Files\Git\bin\bash.exe'


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True, encoding='utf-8').strip()


def glob_regex(pattern):
    """Glob de GitHub Actions: ** cruza carpetas, * y ? no."""
    out, i = '', 0
    while i < len(pattern):
        if pattern.startswith('**/', i):
            out, i = out + '(?:.*/)?', i + 3
        elif pattern.startswith('**', i):
            out, i = out + '.*', i + 2
        elif pattern[i] == '*':
            out, i = out + '[^/]*', i + 1
        elif pattern[i] == '?':
            out, i = out + '[^/]', i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r'\Z')


def triggered(pr, changed):
    if 'paths' in pr:
        hit = set()
        for pattern in pr['paths']:
            neg = pattern.startswith('!')
            rx = glob_regex(pattern.lstrip('!'))
            matched = {f for f in changed if rx.match(f)}
            hit = hit - matched if neg else hit | matched
        return bool(hit)
    if 'paths-ignore' in pr:
        rxs = [glob_regex(p) for p in pr['paths-ignore']]
        return any(not any(rx.match(f) for rx in rxs) for f in changed)
    return True


CONTEXTO = {}


def contexto_pr(base):
    """Lo que GitHub pone en `github.*` en una pull_request, con su equivalente local."""
    head, rama = git('rev-parse', 'HEAD'), git('rev-parse', '--abbrev-ref', 'HEAD')
    return {'github.event.pull_request.base.sha': base, 'github.event.pull_request.head.sha': head,
            'github.sha': head, 'github.event_name': 'pull_request', 'github.head_ref': rama, 'github.ref_name': rama}


def expresion(expr, contexto):
    """`${{ a || b || 'x' }}` y `${{ cond && 'x' || 'y' }}`: la primera alternativa que da valor. None si no se puede
    resolver en local (inputs, cuerpo de la PR…): esa variable no se pasa."""
    for alt in expr.split('||'):
        *conds, valor = [t.strip() for t in alt.split('&&')]
        if all(evalua(c, contexto) for c in conds) and (v := termino(valor, contexto)):
            return v
    return None


def termino(t, contexto):
    return t[1:-1] if len(t) > 1 and t[0] == t[-1] == "'" else contexto.get(t)


def evalua(cond, contexto):
    m = re.fullmatch(r"(\S+)\s*(==|!=)\s*(\S+)", cond)
    if not m:
        return bool(termino(cond, contexto))
    igual = termino(m[1], contexto) == termino(m[3], contexto)
    return igual if m[2] == '==' else not igual


def plain_env(env, contexto=None):
    """Variables del workflow. Las que son expresiones `${{ github.* }}` se resuelven con su equivalente local
    (base de la PR = merge-base con origin/main); antes se descartaban y findability-inventory y
    publishing-metadata-preservation fallaban siempre con «BASE_SHA requerido», contadas como «ya fallaban en main»."""
    contexto = CONTEXTO if contexto is None else contexto
    out = {}
    for k, v in (env or {}).items():
        v = str(v)
        if '${{' in v:
            m = re.fullmatch(r'\s*\$\{\{(.*)\}\}\s*', v)
            v = m and expresion(m[1], contexto)
        if v is not None:
            out[k] = v
    return out


def loop_lines(run):
    """`for f in tests/test-*.py; do … python "$f"` (las pruebas de la puerta obligatoria): un comando por fichero."""
    lines = []
    for var, pattern, body in re.findall(r'for (\w+) in (\S+); do(.*?)\bdone\b', run, re.S):
        tool = re.search(r'\b(python3?|node) "?\$' + var + r'\b', body)
        if tool:
            lines += [f'{tool[1]} {p.relative_to(ROOT).as_posix()}' for p in sorted(ROOT.glob(pattern))]
    return lines


def collect(changed, everything):
    """Comandos únicos de los workflows activados, con su entorno."""
    import yaml  # aquí y no arriba: los tests de lotes importan este módulo en runners sin PyYAML
    commands = {}
    for path in sorted((ROOT / '.github/workflows').glob('*.yml')):
        flow = yaml.safe_load(path.read_text(encoding='utf-8'))
        on = flow.get(True) or flow.get('on') or {}
        if not isinstance(on, dict) or 'pull_request' not in on:
            continue
        if not everything and not triggered(on['pull_request'] or {}, changed):
            continue
        for job in (flow.get('jobs') or {}).values():
            for step in job.get('steps') or []:
                previos = []
                for line in loop_lines(step.get('run') or '') + (step.get('run') or '').splitlines():
                    m = COMMAND.match(line.strip())
                    if not m and PREPARA.match(line.strip()):
                        previos.append(line.strip())
                        continue
                    if not m and PRODUCTOR.match(line.strip()):
                        previos.append(re.sub(r'^python3 ', 'python ', line.strip()))
                        continue
                    # qa/production-*: miden la web desplegada, no esta rama.
                    if not m or '$' in line or '--update' in line or 'qa/production-' in line \
                            or any(n in line for n in NEEDS_BUILD):
                        continue
                    key = ' && '.join(previos + [re.sub(r'^python3 ', 'python ', m.group(2))])
                    if key == SUITE:
                        for i in range(SHARDS):
                            shard = f'python scripts/local-ci.py --unittest-shard {i}/{SHARDS}'
                            commands.setdefault(shard, (m.group(1) + shard, {}, path.name))
                        continue
                    if key not in commands:
                        env = {**plain_env(flow.get('env')), **plain_env(job.get('env')), **plain_env(step.get('env'))}
                        commands[key] = (m.group(1) + key, env, path.name)
    return list(commands.values())


def referencias(stem):
    """Ficheros versionados que nombran un script (con guion o guion bajo), sin contar docs ni informes."""
    names = {stem, stem.replace('-', '_'), stem.replace('_', '-')}
    out = subprocess.run(['git', 'grep', '-l', '-F', *[a for n in names for a in ('-e', n)]], cwd=ROOT,
                         text=True, capture_output=True, encoding='utf-8').stdout
    return {f for f in out.splitlines() if not f.endswith('.md') and not f.startswith(('docs/', '.ci/'))}


def scoped(changed, refs=referencias):
    """Comandos mínimos cuando todo lo cambiado es un script suelto y sus tests; None si hay que correr el CI entero.

    Un script de scripts/ que no nombra ningún workflow, builder, QA ni otro script solo puede romper sus propios
    tests: correr los 500 comandos de la vía completa por él solo alarga el ciclo de cambio.
    """
    scripts = [f for f in changed if re.fullmatch(r'scripts/[\w.-]+\.py', f)]
    tests = {f for f in changed if re.fullmatch(r'tests/test[_-][\w.-]+\.py', f)}
    if not changed or len(scripts) + len(tests) != len(changed):
        return None
    for script in scripts:
        users = refs(Path(script).stem) - set(changed) - {script}
        if any(not u.startswith('tests/') for u in users):
            return None
        tests |= {u for u in users if re.fullmatch(r'tests/test[_-][\w.-]+\.py', u)}
    commands = [(f'python -m py_compile {s}', {}, 'alcance') for s in sorted(scripts)]
    for t in sorted(tests):
        name = Path(t).name
        command = f'python -m unittest discover -s tests -p {name}' if name.startswith('test_') else f'python {t}'
        commands.append((command, {}, 'alcance'))
    return commands


# `python -m http.server` escucha con una cola de 5 conexiones: con varias pruebas de navegador a la vez, Windows
# rechaza el resto (ERR_CONNECTION_REFUSED) aunque el proceso siga vivo. 10/11: 40 pruebas caídas en 3 s.
SERVER_CODE = ('import sys, http.server as h\n'
               'class S(h.ThreadingHTTPServer):\n'
               '    request_queue_size = 512\n'
               '    daemon_threads = True\n'
               'S(("127.0.0.1", int(sys.argv[1])), h.SimpleHTTPRequestHandler).serve_forever()\n')

LITERAL = re.compile(r'(127\.0\.0\.1|localhost):(417[35])\b')
ENV_NAME = re.compile(r'process\.env\.([A-Z][A-Z0-9_]*)|environ(?:\.get\(|\[)[\'"]([A-Z][A-Z0-9_]*)')


def free_port():
    import socket
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def origin_vars(root):
    """Variables de entorno con las que cada prueba sustituye su origen por defecto (127.0.0.1:4173 o :4175).

    Se descubren en el código: las que aparecen en la misma línea que el literal. Así una prueba nueva con su propia
    variable (FERIAS_BASE_URL…) recibe el puerto real sin tocar esta lista."""
    found = {}
    for pattern in ('qa/**/*.mjs', 'tests/**/*.mjs', 'tests/**/*.py', 'scripts/*.mjs', 'scripts/*.py'):
        for path in Path(root).glob(pattern):
            try:
                text = path.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            for line in text.splitlines():
                literal = LITERAL.search(line)
                if literal:
                    for a, b in ENV_NAME.findall(line):
                        found.setdefault(a or b, int(literal.group(2)))
    return found


class Servers:
    """Los servidores de la QA de navegador, en puertos libres y vigilados.

    Los workflows y las pruebas citan 4173/4175. Con puertos fijos solo cabía una puerta por máquina (la del
    autorrepair y las de otras ramas esperaban en cola, 10/11), y dos a la vez se tumbaban los servidores. Ahora cada
    puerta elige puertos libres y `remap` pasa a cada comando el origen real: reescribe el literal en el comando y en
    su entorno, y fija las variables de origen que las pruebas ya leen (`origin_vars`).

    Si uno muere a mitad de la puerta, cada prueba posterior daba ERR_CONNECTION_REFUSED y contaba como fallo de la
    rama (30 «fallos» falsos el 9/11). Su salida va a .local/local-ci/server-<puerto>.log, antes de cada prueba se
    comprueba que contestan y, si alguno cayó, se relanza en el mismo puerto.
    """

    def __init__(self, root):
        self.root, self.procs, self.lock = root, {}, threading.Lock()
        self.ports = {port: free_port() for port in PORTS}
        self.vars = origin_vars(root)
        self.logs = ROOT / '.local/local-ci'
        self.logs.mkdir(parents=True, exist_ok=True)
        self.restarts = 0

    def origin(self, canonical):
        return f'http://127.0.0.1:{self.ports[canonical]}'

    def remap(self, command, env):
        sub = lambda text: LITERAL.sub(lambda m: f'{m.group(1)}:{self.ports[int(m.group(2))]}', text)
        env = {k: sub(v) for k, v in env.items()}
        for name, canonical in self.vars.items():
            env.setdefault(name, self.origin(canonical))
        return sub(command), env

    def start(self, canonical):
        port = self.ports[canonical]
        log = open(self.logs / f'server-{canonical}.log', 'a', encoding='utf-8')
        self.procs[canonical] = subprocess.Popen([sys.executable, '-c', SERVER_CODE, str(port)],
                                                 cwd=self.root, stdout=log, stderr=subprocess.STDOUT)
        for _ in range(50):
            if self.alive(port):
                return
            time.sleep(0.2)

    @staticmethod
    def alive(port):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=5)
            return True
        except OSError:
            return False

    def __enter__(self):
        for canonical in PORTS:
            self.start(canonical)
        return self

    def ensure(self):
        with self.lock:
            for canonical in PORTS:
                proc = self.procs.get(canonical)
                if proc is None or proc.poll() is not None or not self.alive(self.ports[canonical]):
                    code = None if proc is None else proc.poll()
                    print(f'  servidor {self.ports[canonical]} caído (salida {code}); se relanza', flush=True)
                    if proc is not None and proc.poll() is None:
                        kill_tree(proc)
                    self.restarts += 1
                    self.start(canonical)

    def __exit__(self, *exc):
        for proc in self.procs.values():
            proc.terminate()
            proc.wait()


def kill_tree(proc):
    """Mata también node y su navegador: si quedan vivos, mantienen abierta la salida y la espera no acaba nunca."""
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True)
    else:
        os.killpg(proc.pid, 9)


def private_dist(command, root):
    """Carpeta de distribución propia para cada comando. Tres pruebas comparten por defecto .preview-dist-sitewide-qa:
    una la borra al acabar y las otras la construyen solo si no existe, así que en paralelo leían un sitio a medias
    (10/11: «llms.txt missing», 236 fallos del contrato, Traceback)."""
    key = hashlib.sha1(f'{Path(root).resolve()}|{command}'.encode()).hexdigest()[:12]
    return Path(tempfile.gettempdir()) / 'local-ci-dist' / key


def run_one(command, env, root, timeout=TIMEOUT):
    start = time.time()
    dist = private_dist(command, root)
    shutil.rmtree(dist, ignore_errors=True)
    env = {'SITEWIDE_DIST': str(dist), **env}
    proc = subprocess.Popen([BASH, '-c', command], cwd=root, env={**os.environ, 'PYTHONUTF8': '1', **env}, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
                            start_new_session=os.name != 'nt')
    try:
        output, _ = proc.communicate(timeout=timeout)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        output, _ = proc.communicate()
        code, output = 124, f'sin terminar en {timeout} s\n{output}'
    shutil.rmtree(dist, ignore_errors=True)
    Path(f'{dist}-manifest.json').unlink(missing_ok=True)
    return code, output, time.time() - start


def needs_server(items):
    """Solo la QA de navegador (node) o lo que cite los puertos usa los servidores: el resto corre sin ellos."""
    return any(re.search(r'(^|[\s/])node|417[35]', command) for command, *_ in items)


def run_all(items, root, jobs, timeout=TIMEOUT):
    if not needs_server(items):
        with ThreadPoolExecutor(jobs) as pool:
            return list(pool.map(lambda item: run_one(item[0], item[1], root, timeout), items))
    with Servers(root) as servers:
        def one(item):
            servers.ensure()
            command, env = servers.remap(item[0], item[1])
            res = run_one(command, env, root, timeout)
            # Si el servidor cayó durante la prueba, el fallo es del entorno: se repite una vez con él relanzado.
            if res[0] != 0 and 'ERR_CONNECTION_REFUSED' in res[1]:
                servers.ensure()
                res = run_one(command, env, root, timeout)
            return res
        with ThreadPoolExecutor(jobs) as pool:
            results = list(pool.map(one, items))
        if servers.restarts:
            print(f'Servidores relanzados {servers.restarts} vez/veces; causa en .local/local-ci/server-*.log', flush=True)
    return results


def failure_line(output):
    lines = [l for l in output.splitlines() if re.search(r'Error|FAIL|assert|Traceback', l)]
    return (lines or output.strip().splitlines()[-1:] or [''])[0].strip()[:200]


# Fallos del entorno, no del código: un paquete o módulo que no está instalado. Si fallan igual en main no prueban
# nada (los dos lados están ciegos). El 10/11, un venv a medio crear y un worktree sin node_modules dieron
# «0 fallos nuevos» con 27 comprobaciones sin correr de verdad.
ENVIRONMENT = re.compile(r"ModuleNotFoundError|No module named|Cannot find (module|package)|ERR_MODULE_NOT_FOUND"
                         r"|npx canceled due to missing packages|Executable doesn't exist|is not recognized as an internal")


def environment_failure(output):
    return bool(ENVIRONMENT.search(output))


def same_failure(branch, main):
    """Main falla igual: mismo error, sin contar números ni rutas. Un tiempo agotado no prueba nada, y un fallo del
    entorno tampoco."""
    norm = lambda res: re.sub(r'\d+|/tmp/\S+|[A-Za-z]:[\\/]\S+', '#', failure_line(res[1]))
    return (main[0] != 0 and 124 not in (branch[0], main[0]) and not environment_failure(branch[1])
            and norm(branch) == norm(main))


def inestables(new, again):
    """Separa los fallos que pasan al repetirlos (inestables) de los que se repiten (nuevos de verdad)."""
    return ([(item, res) for (item, res), r in zip(new, again) if r[0] != 0],
            [item[0] for (item, _), r in zip(new, again) if r[0] == 0])


def baseline_tree():
    tree = ROOT / '.local/local-ci/main'
    if not tree.exists():
        git('worktree', 'add', '-q', '--detach', str(tree), 'origin/main')
    git('reset', '-q', '--hard', 'origin/main', cwd=tree)
    modules = tree / 'node_modules'
    if (ROOT / 'node_modules').exists() and not modules.exists():
        enlazar(modules, ROOT / 'node_modules')
    materializar(tree)
    return tree


def enlazar(dst, src):
    if os.name == 'nt':
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(dst), str(src)], check=True, stdout=subprocess.DEVNULL)
    else:
        dst.symlink_to(src)


def node_modules_listos(root=None):
    """Un worktree nuevo no trae node_modules: sin esto, todo test de navegador cae en el import (2026-11-09, 13
    comandos «MAL 0s» en la rama y en main). Se enlazan los del checkout principal si el lock coincide; si no, npm ci."""
    root = Path(root or ROOT)
    if (root / 'node_modules').exists() or not (root / 'package-lock.json').exists():
        return
    common = subprocess.run(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'], cwd=root,
                            capture_output=True, text=True, check=True).stdout.strip()
    principal = Path(common).parent
    lock = principal / 'package-lock.json'
    if (principal / 'node_modules').exists() and lock.exists() and \
            lock.read_bytes() == (root / 'package-lock.json').read_bytes():
        print(f'Enlazando node_modules de {principal}', flush=True)
        enlazar(root / 'node_modules', principal / 'node_modules')
    else:
        print('Instalando node_modules (npm ci)…', flush=True)
        subprocess.run('npm ci --no-audit --no-fund', cwd=root, shell=True, check=True)


def ci_python():
    """Python con solo scripts/requirements.txt, como el job python-tests del CI (cacheado por hash del fichero).

    Sin esto, un test que importa un paquete instalado aquí pero no en el runner (PyYAML, 2026-11-09) pasa la puerta
    local y cae en el CI."""
    import hashlib
    reqs = ROOT / 'scripts/requirements.txt'
    digest = hashlib.sha256(reqs.read_bytes()).hexdigest()[:12]
    venv = ROOT / '.local/local-ci' / f'venv-{digest}'
    exe = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    # La marca se escribe solo tras un pip install completo: un entorno a medias (puerta cortada durante la
    # instalación, 2026-11-09) tenía python.exe sin Pillow y hacía fallar 28 comandos en la rama y en main.
    listo = venv / '.instalado'
    if not listo.exists():
        print(f'Creando el entorno del CI ({venv.name})…', flush=True)
        shutil.rmtree(venv, ignore_errors=True)
        subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
        subprocess.run([str(exe), '-m', 'pip', 'install', '-q', '-r', str(reqs)], check=True)
        listo.write_text(digest, encoding='utf-8')
    return exe.as_posix()


def unittest_shard(spec):
    """Un lote de `discover -s tests -p 'test_*.py'`: los ficheros i, i+n, i+2n… (reparto por turno, parejo)."""
    import unittest
    index, total = (int(x) for x in spec.split('/'))
    files = sorted(p.name for p in (ROOT / 'tests').glob('test_*.py'))[index::total]
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.discover(str(ROOT / 'tests'), pattern=name, top_level_dir=str(ROOT / 'tests'))
                               for name in files)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


def materializar(root):
    """Lo generado al día antes de la suite (paso 3 de docs/arquitectura-catalogo): sin efecto mientras esté en git."""
    script = Path(root) / 'scripts' / 'materializar_generados.py'
    if script.exists():
        spec = importlib.util.spec_from_file_location('materializar_generados', script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, 'asegurar'):
            mod.asegurar(Path(root))


# Cambian el comportamiento de todo el CI: con ellos no hay impacto acotado posible.
GLOBAL = re.compile(r'(\.github/|package(-lock)?\.json$|scripts/requirements[\w.-]*\.txt$|scripts/local-ci\.py$)')
PY_TEST = re.compile(r'tests/test[_-][\w.-]+\.py')
NODE_TEST = re.compile(r'(?:tests|qa)/[\w./-]+\.mjs')
CODE = ('.py', '.mjs', '.js')
CENTRAL = 60  # un fichero que nombran más de 60 ficheros es central: mejor la vía completa


def test_command(path):
    name = Path(path).name
    if path.endswith('.mjs'):
        return f'node {path}'
    return f'python -m unittest discover -s tests -p {name}' if name.startswith('test_') else f'python {path}'


def impacto(changed, refs=referencias, workflow=None):
    """Puerta por impacto (test impact analysis, como `nx affected` o pytest-testmon, pero por nombres).

    Corre las pruebas que nombran lo cambiado, las de los scripts que lo importan (hasta 40 ficheros) y los pasos de
    los workflows que ejecutan esos scripts. Devuelve None, y se usa la vía completa, si cambia algo global
    (workflows, dependencias, esta puerta), un fichero central o un fichero de datos que ninguna prueba nombra.

    10/11: la vía completa (560 comandos, 45–90 min, con falsos fallos del entorno) rechazó tres arreglos correctos
    de la autorreparación y la carga estuvo 4 h sin publicar. El CI de GitHub sigue corriendo todo antes del merge.
    """
    if not changed or any(GLOBAL.match(f) for f in changed):
        return None
    tests, compiles, stems = set(), set(), set()
    pending, seen = [(f, 0) for f in sorted(changed)], set()
    while pending:
        f, depth = pending.pop()
        if f in seen:
            continue
        seen.add(f)
        if PY_TEST.fullmatch(f) or NODE_TEST.fullmatch(f):
            tests.add(f)
            continue
        if f.endswith('.py'):
            compiles.add(f)
        stem = Path(f).stem if f.endswith(CODE) else Path(f).name
        users = refs(stem) - {f}
        if len(users) > CENTRAL:
            return None
        stems.add(stem)
        named = {u for u in users if PY_TEST.fullmatch(u) or NODE_TEST.fullmatch(u)}
        readers = [u for u in users if re.fullmatch(r'scripts/[\w.-]+\.(?:py|mjs)', u)]
        if not named and not readers and not f.endswith(CODE):
            return None  # datos o HTML que nada nombra: no sabemos qué los cubre
        tests |= named
        if depth == 0:
            # quien importa el módulo o lee el dato directamente: sus pruebas y sus pasos también. Solo un nivel:
            # seguir a los que importan a los que importan llevaba un cambio en el núcleo a 116 comandos.
            pending += [(r, 1) for r in readers]
    if workflow is None:
        workflow = collect(set(), True)
    by_test = {}
    items = []
    for command, env, flow in workflow:
        words = re.split(r'[\s/]', command)
        if any(Path(w).stem in stems for w in words if w):
            items.append((command, env, flow))
        for t in tests:
            if t in command:
                by_test.setdefault(t, (command, env, flow))
    if compiles:
        items.append(('python -m py_compile ' + ' '.join(sorted(compiles)), {}, 'impacto'))
    for t in sorted(tests):
        items.append(by_test.get(t) or (test_command(t), {}, 'impacto'))
    unique = {}
    for item in items:
        unique.setdefault(item[0], item)
    return list(unique.values())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--all', action='store_true', help='todos los pasos de QA, sin filtrar por rutas')
    parser.add_argument('--baseline', action='store_true', help='repite los fallos sobre origin/main')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--timeout', type=int, default=TIMEOUT, help='segundos por comando')
    parser.add_argument('--only', help='solo los comandos que contengan este texto')
    parser.add_argument('--list', action='store_true', help='enseña qué correría y sale')
    parser.add_argument('--completa', action='store_true', help='la vía completa de los workflows, sin puerta por impacto')
    parser.add_argument('--tambien', action='append', default=[], metavar='CMD',
                        help='añade un comando (p. ej. el paso que falló en el workflow); se puede repetir')
    parser.add_argument('--unittest-shard', metavar='I/N', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.unittest_shard:
        return unittest_shard(args.unittest_shard)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    subprocess.run(['git', 'fetch', '-q', 'origin', 'main'], cwd=ROOT)
    base = git('merge-base', 'HEAD', 'origin/main')
    CONTEXTO.update(contexto_pr(base))
    changed = set(git('diff', '--name-only', base).splitlines())
    changed |= {l[3:] for l in git('status', '--porcelain', '--untracked-files=all').splitlines() if l}
    items = None if args.all else scoped(changed)
    if items is not None:
        print('Solo scripts sueltos y sus tests: puerta por alcance (el CI de GitHub sigue corriendo todo)')
    elif not (args.all or args.completa) and (items := impacto(changed)) is not None:
        print('Puerta por impacto: pruebas y pasos que tocan lo cambiado (el CI de GitHub sigue corriendo todo)')
    else:
        items = collect(changed, args.all)
    items += [(c, {}, 'también') for c in args.tambien if c not in {i[0] for i in items}]
    if args.only:
        items = [i for i in items if args.only in i[0]]
    print(f'{len(changed)} ficheros cambiados; {len(items)} comandos de CI', flush=True)
    if args.list:
        for command, _, flow in items:
            print(f'  {flow}: {command}')
        return 0

    venv = ('python scripts/local-ci.py --unittest-shard', 'python -m unittest discover -s tests -p ')
    if any(command.startswith(venv) for command, *_ in items):
        py = ci_python()
        items = [(f'"{py}"' + c[len('python'):] if c.startswith(venv) else c, e, f) for c, e, f in items]
    if any(command.startswith('node ') for command, *_ in items):
        node_modules_listos()
    materializar(ROOT)
    results = run_all(items, ROOT, args.jobs, args.timeout)
    failed = [(item, res) for item, res in zip(items, results) if res[0] != 0]
    for (command, _, flow), (code, _, secs) in zip(items, results):
        print(f"{'ok ' if code == 0 else 'MAL'} {secs:5.0f}s {command}")
    # Un tiempo agotado no se compara con main (same_failure nunca lo daría por conocido): repetirlo solo gasta 15 min.
    timed_out = [(item, res) for item, res in failed if res[0] == 124]
    failed = [(item, res) for item, res in failed if res[0] != 124]
    if failed and args.baseline:
        print(f'Repitiendo {len(failed)} fallos sobre origin/main…', flush=True)
        again = run_all([item for item, _ in failed], baseline_tree(), args.jobs, args.timeout)
        # Si main falla por otro motivo (entorno, puerto), ese fallo tapaba el de la rama: cuenta como nuevo.
        new = [(item, res) for (item, res), old in zip(failed, again) if not same_failure(res, old)]
        known = [item[0] for (item, res), old in zip(failed, again) if same_failure(res, old)]
    else:
        new, known = failed, []
    new += timed_out
    # Agotar el tiempo no es un fallo de la rama ni un aprobado: queda sin verificar (salida 2) y lo decide el CI.
    slow = [item[0] for item, res in new if res[0] == 124]
    new = [(item, res) for item, res in new if res[0] != 124]
    flaky = []
    if new:
        # Como flaky_test_attempts de Bazel o pytest-rerunfailures: cada fallo nuevo se repite una vez en la rama. Si
        # pasa, es inestable: se informa y no bloquea (el 10/11, manecillas TimeoutError, el lote 0/8 y un CLS
        # rechazaron arreglos correctos). El CI de GitHub lo vuelve a correr igualmente.
        print(f'Repitiendo {len(new)} fallos nuevos en la rama…', flush=True)
        new, flaky = inestables(new, run_all([item for item, _ in new], ROOT, args.jobs, args.timeout))
    for (command, _, flow), (code, output, _) in new:
        print(f'\n## {command}  ({flow}, código {code})\n{failure_line(output)}')
    for command in known:
        print(f'  ya falla igual en main: {command}')
    for command in flaky:
        print(f'  inestable (falló y pasó al repetirlo): {command}')
    for command in slow:
        print(f'  sin verificar (agotó {args.timeout} s): {command}')
    print(f'\n{sum(1 for r in results if r[0] == 0)} bien, {len(new)} fallos nuevos' + (f', {len(known)} ya fallaban en main' if known else '')
          + (f', {len(flaky)} inestables' if flaky else '') + (f', {len(slow)} sin verificar' if slow else ''))
    return 1 if new else 2 if slow else 0


if __name__ == '__main__':
    sys.exit(main())
