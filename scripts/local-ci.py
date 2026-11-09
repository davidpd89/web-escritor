#!/usr/bin/env python3
"""Puerta local equivalente al CI de un PR, antes de subirlo.

Lee .github/workflows: los workflows de pull_request cuyas `paths` casan con los cambios frente a origin/main
y, de sus pasos, las líneas `node qa/*.mjs`, `python … --check` y las pruebas. Las corre aquí en paralelo con los
servidores que esperan (4173 y 4175) y, con --baseline, repite los fallos sobre origin/main: lo que también falla
allí ya estaba roto y no bloquea este cambio.

  python scripts/local-ci.py                # lo que correría el CI para los cambios de esta rama
  python scripts/local-ci.py --baseline     # y separa los fallos que ya trae main
  python scripts/local-ci.py --all          # todos los pasos, sin mirar las rutas

Salida: 0 sin fallos nuevos, 1 con fallos nuevos, 2 si algo agotó el tiempo y queda sin verificar.
"""
import argparse
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


def plain_env(env):
    """Variables del workflow que no dependen de expresiones ${{ }} (esas solo existen en GitHub)."""
    return {k: str(v) for k, v in (env or {}).items() if '${{' not in str(v)}


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
                for line in loop_lines(step.get('run') or '') + (step.get('run') or '').splitlines():
                    m = COMMAND.match(line.strip())
                    # qa/production-*: miden la web desplegada, no esta rama.
                    if not m or '$' in line or '--update' in line or 'qa/production-' in line \
                            or any(n in line for n in NEEDS_BUILD):
                        continue
                    key = re.sub(r'^python3 ', 'python ', m.group(2))
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


def busy_ports():
    """En Windows http.server usa SO_REUSEADDR: un servidor previo en el puerto contestaría por el nuestro."""
    busy = []
    for port in PORTS:
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=1)
            busy.append(port)
        except OSError:
            pass
    return busy


class Servers:
    """Los servidores 4173/4175 de la QA de navegador, vigilados.

    Si uno muere a mitad de la puerta, cada prueba posterior daba ERR_CONNECTION_REFUSED y contaba como fallo de la
    rama (30 «fallos» falsos el 9/11). Ahora su salida va a .local/local-ci/server-<puerto>.log, antes de cada prueba se
    comprueba que contestan y, si alguno cayó, se relanza.
    """

    def __init__(self, root, lock_path=None):
        # lock_path: los tests usan uno propio; con el de la máquina esperarían a la puerta que los ejecuta.
        self.root, self.procs, self.lock = root, {}, threading.Lock()
        self.lock_path = lock_path
        self.logs = ROOT / '.local/local-ci'
        self.logs.mkdir(parents=True, exist_ok=True)
        self.restarts = 0

    def start(self, port):
        log = open(self.logs / f'server-{port}.log', 'a', encoding='utf-8')
        self.procs[port] = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'],
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
        self.lock_file = ports_lock(self.lock_path or PORTS_LOCK)
        if busy_ports():
            release(self.lock_file)
            raise SystemExit(f'Puertos ocupados por otro servidor: {busy_ports()}; ciérralo antes de la puerta.')
        for port in PORTS:
            self.start(port)
        return self

    def ensure(self):
        with self.lock:
            for port in PORTS:
                proc = self.procs.get(port)
                if proc is None or proc.poll() is not None or not self.alive(port):
                    code = None if proc is None else proc.poll()
                    print(f'  servidor {port} caído (salida {code}); se relanza', flush=True)
                    if proc is not None and proc.poll() is None:
                        kill_tree(proc)
                    self.restarts += 1
                    self.start(port)

    def __exit__(self, *exc):
        try:
            for proc in self.procs.values():
                proc.terminate()
                proc.wait()
        finally:
            release(self.lock_file)


PORTS_LOCK = Path(tempfile.gettempdir()) / 'web-escritor-local-ci-ports.lock'


def ports_lock(path=PORTS_LOCK, wait=3 * 3600):
    """Cerrojo de máquina sobre los puertos 4173/4175.

    Dos puertas a la vez (la de la autorreparación y otra a mano, en worktrees distintos) compartían los puertos: en
    Windows http.server usa SO_REUSEADDR, así que la segunda no veía el puerto ocupado y, al cerrar sus servidores,
    tumbaba los de la otra. Ahora la segunda espera su turno.
    """
    handle = open(path, 'a+b')
    start, said = time.time(), False
    while True:
        try:
            if os.name == 'nt':
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return handle
        except OSError:
            if time.time() - start > wait:
                handle.close()
                raise SystemExit('Otra puerta local lleva más de 3 h con los puertos de QA; revísala.')
            if not said:
                print('Otra puerta local usa los puertos de QA: espero mi turno…', flush=True)
                said = True
            time.sleep(5)


def release(handle):
    try:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_UN)
    except OSError:
        pass
    handle.close()


def kill_tree(proc):
    """Mata también node y su navegador: si quedan vivos, mantienen abierta la salida y la espera no acaba nunca."""
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True)
    else:
        os.killpg(proc.pid, 9)


def run_one(command, env, root, timeout=TIMEOUT):
    start = time.time()
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
            res = run_one(item[0], item[1], root, timeout)
            # Si el servidor cayó durante la prueba, el fallo es del entorno: se repite una vez con él relanzado.
            if res[0] != 0 and 'ERR_CONNECTION_REFUSED' in res[1]:
                servers.ensure()
                res = run_one(item[0], item[1], root, timeout)
            return res
        with ThreadPoolExecutor(jobs) as pool:
            results = list(pool.map(one, items))
        if servers.restarts:
            print(f'Servidores relanzados {servers.restarts} vez/veces; causa en .local/local-ci/server-*.log', flush=True)
    return results


def failure_line(output):
    lines = [l for l in output.splitlines() if re.search(r'Error|FAIL|assert|Traceback', l)]
    return (lines or output.strip().splitlines()[-1:] or [''])[0].strip()[:200]


def same_failure(branch, main):
    """Main falla igual: mismo error, sin contar números ni rutas. Un tiempo agotado no prueba nada."""
    norm = lambda res: re.sub(r'\d+|/tmp/\S+|[A-Za-z]:[\\/]\S+', '#', failure_line(res[1]))
    return main[0] != 0 and 124 not in (branch[0], main[0]) and norm(branch) == norm(main)


def baseline_tree():
    tree = ROOT / '.local/local-ci/main'
    if not tree.exists():
        git('worktree', 'add', '-q', '--detach', str(tree), 'origin/main')
    git('reset', '-q', '--hard', 'origin/main', cwd=tree)
    modules = tree / 'node_modules'
    if (ROOT / 'node_modules').exists() and not modules.exists():
        if os.name == 'nt':
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(modules), str(ROOT / 'node_modules')], check=True,
                           stdout=subprocess.DEVNULL)
        else:
            modules.symlink_to(ROOT / 'node_modules')
    return tree


def ci_python():
    """Python con solo scripts/requirements.txt, como el job python-tests del CI (cacheado por hash del fichero).

    Sin esto, un test que importa un paquete instalado aquí pero no en el runner (PyYAML, 2026-11-09) pasa la puerta
    local y cae en el CI."""
    import hashlib
    reqs = ROOT / 'scripts/requirements.txt'
    digest = hashlib.sha256(reqs.read_bytes()).hexdigest()[:12]
    venv = ROOT / '.local/local-ci' / f'venv-{digest}'
    exe = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not exe.exists():
        print(f'Creando el entorno del CI ({venv.name})…', flush=True)
        subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
        subprocess.run([str(exe), '-m', 'pip', 'install', '-q', '-r', str(reqs)], check=True)
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--all', action='store_true', help='todos los pasos de QA, sin filtrar por rutas')
    parser.add_argument('--baseline', action='store_true', help='repite los fallos sobre origin/main')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--timeout', type=int, default=TIMEOUT, help='segundos por comando')
    parser.add_argument('--only', help='solo los comandos que contengan este texto')
    parser.add_argument('--list', action='store_true', help='enseña qué correría y sale')
    parser.add_argument('--unittest-shard', metavar='I/N', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.unittest_shard:
        return unittest_shard(args.unittest_shard)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    subprocess.run(['git', 'fetch', '-q', 'origin', 'main'], cwd=ROOT)
    base = git('merge-base', 'HEAD', 'origin/main')
    changed = set(git('diff', '--name-only', base).splitlines())
    changed |= {l[3:] for l in git('status', '--porcelain', '--untracked-files=all').splitlines() if l}
    items = None if args.all else scoped(changed)
    if items is not None:
        print('Solo scripts sueltos y sus tests: puerta por alcance (el CI de GitHub sigue corriendo todo)')
    else:
        items = collect(changed, args.all)
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
    for (command, _, flow), (code, output, _) in new:
        print(f'\n## {command}  ({flow}, código {code})\n{failure_line(output)}')
    for command in known:
        print(f'  ya falla igual en main: {command}')
    for command in slow:
        print(f'  sin verificar (agotó {args.timeout} s): {command}')
    print(f'\n{len(items) - len(failed) - len(timed_out)} bien, {len(new)} fallos nuevos' + (f', {len(known)} ya fallaban en main' if known else '')
          + (f', {len(slow)} sin verificar' if slow else ''))
    return 1 if new else 2 if slow else 0


if __name__ == '__main__':
    sys.exit(main())
