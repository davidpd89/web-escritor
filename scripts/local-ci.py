#!/usr/bin/env python3
"""Puerta local equivalente al CI de un PR, antes de subirlo.

Lee .github/workflows: los workflows de pull_request cuyas `paths` casan con los cambios frente a origin/main
y, de sus pasos, las líneas `node qa/*.mjs`, `python … --check` y las pruebas. Las corre aquí en paralelo con los
servidores que esperan (4173 y 4175) y, con --baseline, repite los fallos sobre origin/main: lo que también falla
allí ya estaba roto y no bloquea este cambio.

  python scripts/local-ci.py                # lo que correría el CI para los cambios de esta rama
  python scripts/local-ci.py --baseline     # y separa los fallos que ya trae main
  python scripts/local-ci.py --all          # todos los pasos, sin mirar las rutas
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

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


def collect(changed, everything):
    """Comandos únicos de los workflows activados, con su entorno."""
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
                for line in (step.get('run') or '').splitlines():
                    m = COMMAND.match(line.strip())
                    # qa/production-*: miden la web desplegada, no esta rama.
                    if not m or '$' in line or '--update' in line or 'qa/production-' in line \
                            or any(n in line for n in NEEDS_BUILD):
                        continue
                    key = re.sub(r'^python3 ', 'python ', m.group(2))
                    if key not in commands:
                        env = {**plain_env(flow.get('env')), **plain_env(job.get('env')), **plain_env(step.get('env'))}
                        commands[key] = (m.group(1) + key, env, path.name)
    return list(commands.values())


def serve(root):
    procs = [subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=root,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for port in PORTS]
    for port in PORTS:
        for _ in range(50):
            try:
                urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=2)
                break
            except OSError:
                time.sleep(0.2)
    return procs


def stop(procs):
    for proc in procs:
        proc.terminate()
        proc.wait()


def kill_tree(proc):
    """Mata también node y su navegador: si quedan vivos, mantienen abierta la salida y la espera no acaba nunca."""
    if os.name == 'nt':
        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True)
    else:
        os.killpg(proc.pid, 9)


def run_one(command, env, root, timeout=TIMEOUT):
    start = time.time()
    proc = subprocess.Popen([BASH, '-c', command], cwd=root, env={**os.environ, **env}, stdout=subprocess.PIPE,
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


def run_all(items, root, jobs, timeout=TIMEOUT):
    procs = serve(root)
    try:
        with ThreadPoolExecutor(jobs) as pool:
            results = list(pool.map(lambda item: run_one(item[0], item[1], root, timeout), items))
    finally:
        stop(procs)
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
        git('worktree', 'add', '--detach', str(tree), 'origin/main')
    git('reset', '-q', '--hard', 'origin/main', cwd=tree)
    modules = tree / 'node_modules'
    if (ROOT / 'node_modules').exists() and not modules.exists():
        if os.name == 'nt':
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(modules), str(ROOT / 'node_modules')], check=True,
                           stdout=subprocess.DEVNULL)
        else:
            modules.symlink_to(ROOT / 'node_modules')
    return tree


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--all', action='store_true', help='todos los pasos de QA, sin filtrar por rutas')
    parser.add_argument('--baseline', action='store_true', help='repite los fallos sobre origin/main')
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--timeout', type=int, default=TIMEOUT, help='segundos por comando')
    parser.add_argument('--only', help='solo los comandos que contengan este texto')
    parser.add_argument('--list', action='store_true', help='enseña qué correría y sale')
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    subprocess.run(['git', 'fetch', '-q', 'origin', 'main'], cwd=ROOT)
    base = git('merge-base', 'HEAD', 'origin/main')
    changed = set(git('diff', '--name-only', base).splitlines())
    changed |= {l[3:] for l in git('status', '--porcelain', '--untracked-files=all').splitlines() if l}
    items = collect(changed, args.all)
    if args.only:
        items = [i for i in items if args.only in i[0]]
    print(f'{len(changed)} ficheros cambiados; {len(items)} comandos de CI', flush=True)
    if args.list:
        for command, _, flow in items:
            print(f'  {flow}: {command}')
        return 0

    results = run_all(items, ROOT, args.jobs, args.timeout)
    failed = [(item, res) for item, res in zip(items, results) if res[0] != 0]
    for (command, _, flow), (code, _, secs) in zip(items, results):
        print(f"{'ok ' if code == 0 else 'MAL'} {secs:5.0f}s {command}")
    if failed and args.baseline:
        print(f'Repitiendo {len(failed)} fallos sobre origin/main…', flush=True)
        again = run_all([item for item, _ in failed], baseline_tree(), args.jobs, args.timeout)
        # Si main falla por otro motivo (entorno, puerto), ese fallo tapaba el de la rama: cuenta como nuevo.
        new = [(item, res) for (item, res), old in zip(failed, again) if not same_failure(res, old)]
        known = [item[0] for (item, res), old in zip(failed, again) if same_failure(res, old)]
    else:
        new, known = failed, []
    for (command, _, flow), (code, output, _) in new:
        print(f'\n## {command}  ({flow}, código {code})\n{failure_line(output)}')
    for command in known:
        print(f'  ya falla igual en main: {command}')
    print(f'\n{len(items) - len(failed)} bien, {len(new)} fallos nuevos' + (f', {len(known)} ya fallaban en main' if known else ''))
    return 1 if new else 0


if __name__ == '__main__':
    sys.exit(main())
