#!/usr/bin/env python3
"""Ejecuta en local los mismos pasos que «Required merge gate», leídos de su YAML.

Actions solo confirma: lo que falle aquí fallaría allí. Los dos pasos largos de contratos corren a la vez que la
cadena corta; cada paso deja su log y al final sale un resumen con los que fallan.

  python scripts/gate-local.py                 # todos los pasos
  python scripts/gate-local.py --skip contracts  # sin los pasos cuyo nombre contiene «contracts»
  python scripts/gate-local.py --only sitemap --only 'site shell'
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / '.github/workflows/required-merge-gate.yml'
# Pasos largos e independientes del artefacto: corren en paralelo con el resto.
PARALLEL = ('Run universal Python contracts', 'Run underscore-named Python contracts')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def steps(path=WORKFLOW):
    job = yaml.safe_load(path.read_text(encoding='utf-8'))['jobs']['required-merge-gate']
    return [s for s in job['steps'] if 'run' in s and s.get('if') != 'always()']


def expand(text, values):
    """Sustituye las expresiones ${{ ... }} de GitHub por sus valores locales; si falta alguna, falla."""
    def sub(m):
        expr = m.group(1).strip()
        for key, value in values.items():
            if key in expr:
                return value
        raise KeyError(f'Expresión sin valor local: {expr}')
    return re.sub(r'\$\{\{(.*?)\}\}', sub, text)


def local_values():
    head = git('rev-parse', 'HEAD')
    base = git('merge-base', 'origin/main', 'HEAD')
    title = git('log', '-1', '--format=%s')
    return {'head.sha': head, 'base.sha': base, 'pull_request.title': title, 'pull_request.body': ''}


def run_step(step, values, logs, bash):
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', RUNNER_TEMP=str(logs / 'runner'))
    for key, value in (step.get('env') or {}).items():
        env[key] = expand(str(value), values)
    (logs / 'runner').mkdir(exist_ok=True)
    script = expand(step['run'], values)
    log = logs / (re.sub(r'[^a-z0-9]+', '-', step['name'].lower()).strip('-') + '.log')
    start = time.monotonic()
    with log.open('w', encoding='utf-8') as out:
        rc = subprocess.run([bash, '-e', '-c', script], cwd=ROOT, env=env, stdout=out,
                            stderr=subprocess.STDOUT).returncode
    return step['name'], rc, time.monotonic() - start, log


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--skip', action='append', default=[], help='omite los pasos cuyo nombre contiene este texto')
    ap.add_argument('--only', action='append', default=[], help='ejecuta solo los pasos cuyo nombre contiene este texto')
    ap.add_argument('--logs', type=Path, default=None)
    args = ap.parse_args()
    bash = shutil.which('bash') or sys.exit('Hace falta bash (Git Bash en Windows)')
    chosen = [s for s in steps()
              if (not args.only or any(o.lower() in s['name'].lower() for o in args.only))
              and not any(k.lower() in s['name'].lower() for k in args.skip)]
    logs = args.logs or Path(tempfile.mkdtemp(prefix='gate-local-'))
    logs.mkdir(parents=True, exist_ok=True)
    values = local_values()
    print(f'{len(chosen)} pasos; logs en {logs}', flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=len(PARALLEL) + 1) as pool:
        futures = [pool.submit(run_step, s, values, logs, bash) for s in chosen if s['name'] in PARALLEL]

        def chain():
            done = []
            for s in chosen:
                if s['name'] not in PARALLEL:
                    done.append(run_step(s, values, logs, bash))
                    name, rc, secs, _ = done[-1]
                    print(f"{'ok   ' if rc == 0 else 'FALLA'} {secs:6.0f}s  {name}", flush=True)
            return done
        serial = pool.submit(chain)
        for f in futures:
            name, rc, secs, log = f.result()
            print(f"{'ok   ' if rc == 0 else 'FALLA'} {secs:6.0f}s  {name}", flush=True)
            results.append((name, rc, secs, log))
        results.extend(serial.result())
    failed = [r for r in results if r[1]]
    for name, _, _, log in failed:
        tail = log.read_text(encoding='utf-8', errors='replace').splitlines()[-25:]
        print(f'\n== FALLA: {name} ({log})\n' + '\n'.join(tail))
    print(f'\n{len(results) - len(failed)}/{len(results)} pasos bien')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
