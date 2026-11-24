#!/usr/bin/env python3
"""fallo_determinista lee los registros de los jobs aunque traigan colores ANSI.

Noche 24/11: `gh api .../jobs/ID/logs` respondía «the response contains terminal escape sequences; pass
--allow-escape-sequences», fallo_determinista daba siempre False y la carga repetía la puerta entera ante un fallo
determinista (~22 min). Se fija que la lectura pasa la opción y que con un gh antiguo se lee sin ella."""
from __future__ import annotations
import importlib.util, json, subprocess
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publish_radar_refresh', ROOT / 'scripts' / 'publish-radar-refresh.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

JOBS = json.dumps({'jobs': [{'id': 7, 'conclusion': 'failure'}]})
LOG = '\x1b[31m2026-11-24T01:00:00Z FALLA: tests/test_reading_x_smoke.py\x1b[0m\n'
ESCAPES = 'the response contains terminal escape sequences; pass --allow-escape-sequences to output it anyway'
VIEJO = 'unknown flag: --allow-escape-sequences'


def fake(responder):
    calls = []
    def run(cmd, **kw):
        args = cmd[1:]
        calls.append(args)
        rc, out, err = responder(args)
        if rc and kw.get('check'):
            raise subprocess.CalledProcessError(rc, cmd, out, err)
        return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr=err)
    return run, calls


def gh_actual(args):
    if '/jobs?per_page=100' in args[-1]:
        return 0, JOBS, ''
    return (0, LOG, '') if '--allow-escape-sequences' in args else (1, '', ESCAPES)


def gh_antiguo(args):
    if '/jobs?per_page=100' in args[-1]:
        return 0, JOBS, ''
    return (1, '', VIEJO) if '--allow-escape-sequences' in args else (0, LOG, '')


with mock.patch.object(mod.time, 'sleep', lambda s: None):
    # 1. gh actual: se pide con la opción y el fallo determinista se reconoce (no se repite la puerta).
    run, calls = fake(gh_actual)
    with mock.patch.object(mod.subprocess, 'run', run):
        assert mod.fallo_determinista('o/r', 1) is True, calls
    assert ['api', '--allow-escape-sequences', 'repos/o/r/actions/jobs/7/logs'] in calls, calls

    # 2. gh antiguo sin la opción: se lee sin ella.
    run, calls = fake(gh_antiguo)
    with mock.patch.object(mod.subprocess, 'run', run):
        assert mod.fallo_determinista('o/r', 1) is True, calls
    assert calls[-1] == ['api', 'repos/o/r/actions/jobs/7/logs'], calls

    # 3. Ninguna otra lectura de registros de jobs con `gh api` en scripts/ sin la opción.
    for path in (ROOT / 'scripts').glob('*.py'):
        for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if '/logs' in line and "gh('api'" in line and 'allow-escape-sequences' not in line and 'ruta' not in line:
                raise AssertionError(f'{path.name}:{n} lee registros de jobs sin --allow-escape-sequences')

print('ok: fallo_determinista lee registros con ANSI (gh actual y antiguo)')
