#!/usr/bin/env python3
"""gh() repite los fallos transitorios de GitHub y no duplica una PR que el intento fallido sí creó."""
from __future__ import annotations
import importlib.util, subprocess
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publish_radar_refresh', ROOT / 'scripts' / 'publish-radar-refresh.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
GRAPHQL = 'GraphQL: Something went wrong while executing your query on 2026-11-04T11:07:05Z.'


def fake(script):
    calls = []
    def run(cmd, **kw):
        calls.append(cmd[1:])
        rc, out, err = script(cmd[1:], len(calls))
        if rc and kw.get('check'):
            raise subprocess.CalledProcessError(rc, cmd, out, err)
        return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr=err)
    return run, calls


with mock.patch.object(mod.time, 'sleep', lambda s: None):
    # 1. Transitorio y luego éxito: devuelve la salida del reintento.
    run, calls = fake(lambda a, n: (1, '', GRAPHQL) if n == 1 else (0, 'ok\n', ''))
    with mock.patch.object(mod.subprocess, 'run', run):
        assert mod.gh('api', 'x') == 'ok'
    assert calls == [['api', 'x'], ['api', 'x']], calls

    # 2. `pr create` falló pero la PR existe: se devuelve su URL sin crear otra.
    url = 'https://github.com/o/r/pull/9'
    run, calls = fake(lambda a, n: (1, '', GRAPHQL) if a[:2] == ['pr', 'create'] else (0, url + '\n', ''))
    with mock.patch.object(mod.subprocess, 'run', run):
        assert mod.gh('pr', 'create', '--base', 'main', '--head', 'automation/x-1', '--title', 't') == url
    assert [c[:2] for c in calls] == [['pr', 'create'], ['pr', 'list']], calls
    assert calls[1][calls[1].index('--head') + 1] == 'automation/x-1'

    # 3. `pr create` falló y no existe: se repite la creación.
    run, calls = fake(lambda a, n: (0, '', '') if a[:2] == ['pr', 'list'] else ((1, '', GRAPHQL) if n == 1 else (0, url, '')))
    with mock.patch.object(mod.subprocess, 'run', run):
        assert mod.gh('pr', 'create', '--head', 'automation/x-1') == url
    assert [c[:2] for c in calls] == [['pr', 'create'], ['pr', 'list'], ['pr', 'create']], calls

    # 4. Error real (no transitorio): se propaga sin repetir.
    run, calls = fake(lambda a, n: (1, '', 'a pull request for branch "x" already exists'))
    with mock.patch.object(mod.subprocess, 'run', run):
        try:
            mod.gh('pr', 'create', '--head', 'x'); raise SystemExit('should raise')
        except subprocess.CalledProcessError:
            pass
    assert len(calls) == 1, calls

    # 5. Transitorio persistente: se rinde tras GH_ATTEMPTS, sin bucle infinito.
    run, calls = fake(lambda a, n: (1, '', 'HTTP 502: Bad Gateway'))
    with mock.patch.object(mod.subprocess, 'run', run):
        try:
            mod.gh('api', 'x'); raise SystemExit('should raise')
        except subprocess.CalledProcessError:
            pass
    assert len(calls) == mod.GH_ATTEMPTS, calls
    # 6. Escrituras no se repiten: un dispatch o merge que sí llegó no se duplica.
    for args in (('workflow', 'run', 'x.yml'), ('pr', 'merge', '9', '--squash'),
                 ('api', '--method', 'PUT', 'repos/o/r/pulls/9/update-branch'), ('api', 'repos/o/r/statuses/s', '-f', 'state=failure')):
        run, calls = fake(lambda a, n: (1, '', GRAPHQL))
        with mock.patch.object(mod.subprocess, 'run', run):
            try:
                mod.gh(*args); raise SystemExit('should raise')
            except subprocess.CalledProcessError:
                pass
        assert len(calls) == 1, (args, calls)
print('ok gh transient retry')
