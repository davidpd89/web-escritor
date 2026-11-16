#!/usr/bin/env python3
"""gh() repite los fallos transitorios de GitHub y no duplica una PR que el intento fallido sí creó."""
from __future__ import annotations
import importlib.util, json, subprocess
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
    pausas = []
    with mock.patch.object(mod.subprocess, 'run', run), mock.patch.object(mod.time, 'sleep', pausas.append):
        try:
            mod.gh('api', 'x'); raise SystemExit('should raise')
        except subprocess.CalledProcessError:
            pass
    assert len(calls) == mod.GH_ATTEMPTS, calls
    assert pausas == [5 * n for n in range(1, mod.GH_ATTEMPTS)], pausas  # sin pausa tras el último intento
    # 6. F7 (Fable R4-10): una escritura que da un 502 se repite solo tras comprobar que no llegó; si llegó, no.
    def github(llego):
        """gh falso: cada escritura falla con 502 la primera vez; `llego` dice si ese primer intento tuvo efecto."""
        estado = {'merged': False, 'closed': False, 'attempt': 1, 'cancel': False, 'fallos': set(),
                  'head': 'abcdef1', 'padres': {}}
        def update_branch():
            estado['padres']['merge1'] = ['abcdef1999', 'main000']
            estado['head'] = 'merge1'
        def script(a, n):
            clave = tuple(a[:2])
            escritura = clave in {('pr', 'merge'), ('pr', 'close'), ('run', 'rerun'), ('run', 'cancel')} \
                or (a[0] == 'api' and '--method' in a)
            if escritura:
                primero = clave not in estado['fallos']
                estado['fallos'].add(clave)
                if primero and not llego:
                    return 1, '', 'HTTP 502: Bad Gateway'
                {('pr', 'merge'): lambda: estado.update(merged=True), ('pr', 'close'): lambda: estado.update(closed=True),
                 ('run', 'rerun'): lambda: estado.update(attempt=estado['attempt'] + 1),
                 ('run', 'cancel'): lambda: estado.update(cancel=True)}.get(
                    clave, update_branch if a[-3:-2] == ['repos/o/r/pulls/9/update-branch'] else lambda: None)()
                return (1, '', 'HTTP 502: Bad Gateway') if primero else (0, 'hecho', '')
            if a[:2] == ['api', 'repos/o/r/pulls/9']:
                return 0, json.dumps({'cabeza': estado['head'], 'base': 'main'}), ''
            if a[0] == 'api' and '/compare/' in a[1]:
                return 0, 'ahead', ''
            if a[0] == 'api' and a[1].startswith('repos/o/r/commits/'):
                return 0, json.dumps(estado['padres'].get(a[1].rsplit('/', 1)[1], [])), ''
            if clave == ('pr', 'view'):
                return 0, json.dumps({'state': 'MERGED' if estado['merged'] else 'CLOSED' if estado['closed'] else 'OPEN'}), ''
            if clave == ('run', 'view'):
                return 0, json.dumps({'attempt': estado['attempt'], 'status': 'completed' if estado['cancel'] else 'in_progress'}), ''
            return 0, '', ''
        return script, estado
    escrituras = {('pr', 'merge', '9', '--squash'): lambda e: e['merged'],
                  ('pr', 'close', '9'): lambda e: e['closed'],
                  ('run', 'rerun', '77', '--failed'): lambda e: e['attempt'] == 2,
                  ('run', 'cancel', '77'): lambda e: e['cancel'],
                  ('api', '--method', 'POST', 'repos/o/r/statuses/abcdef1', '-f', 'state=success'): lambda e: True,
                  ('api', '--method', 'PUT', 'repos/o/r/pulls/9/update-branch', '-f', 'expected_head_sha=abcdef1'):
                      lambda e: e['head'] == 'merge1'}
    for llego in (False, True):
        for args, hecho in escrituras.items():
            script, estado = github(llego)
            run, calls = fake(lambda a, n: script(a, n))
            with mock.patch.object(mod.subprocess, 'run', run):
                mod.gh(*args)  # el 502 ya no tumba la carga
            assert hecho(estado), (llego, args, estado)
            veces = sum(1 for c in calls if tuple(c[:len(args)]) == args)
            idempotente = '/statuses/' in args[3] if args[0] == 'api' else False  # update-branch aplicado: 1 PUT
            assert veces == (2 if not llego or idempotente else 1), (llego, args, calls)
    # El último intento fusionó pero devolvió 502: se comprueba el efecto antes de propagar el error.
    fusion = {'merged': False, 'merges': 0}
    def merge_tardio(a, n):
        if a[:2] == ['pr', 'merge']:
            fusion['merges'] += 1
            fusion['merged'] = fusion['merges'] == mod.GH_ATTEMPTS
            return 1, '', 'HTTP 502: Bad Gateway'
        return 0, json.dumps({'state': 'MERGED' if fusion['merged'] else 'OPEN'}), ''
    run, calls = fake(merge_tardio)
    with mock.patch.object(mod.subprocess, 'run', run):
        assert mod.gh('pr', 'merge', '9', '--squash') == ''
    assert fusion['merges'] == mod.GH_ATTEMPTS, calls
    # update-branch con 502 y la cabeza movida por otro push (no hija de la esperada): se repite y el 422 se propaga.
    def otro_push(a, n):
        if '--method' in a:
            return (1, '', 'HTTP 502: Bad Gateway') if n == 1 else (1, '', 'HTTP 422: expected head sha mismatch')
        if a[1] == 'repos/o/r/pulls/9':
            return 0, json.dumps({'cabeza': 'ajeno22', 'base': 'main'}), ''
        return 0, json.dumps(['otro333']), ''
    run, calls = fake(otro_push)
    with mock.patch.object(mod.subprocess, 'run', run):
        try:
            mod.gh('api', '--method', 'PUT', 'repos/o/r/pulls/9/update-branch', '-f', 'expected_head_sha=abcdef1')
            raise SystemExit('should raise')
        except subprocess.CalledProcessError as exc:
            assert '422' in exc.stderr, exc.stderr
    assert sum('--method' in c for c in calls) == 2, calls
    # Un push lineal de otro escritor sobre la cabeza esperada no prueba que update-branch llegara: se repite.
    def lineal(a, n):
        if '--method' in a:
            return (1, '', 'HTTP 502: Bad Gateway') if n == 1 else (1, '', 'HTTP 422: expected head sha mismatch')
        if a[1] == 'repos/o/r/pulls/9':
            return 0, json.dumps({'cabeza': 'lineal33', 'base': 'main'}), ''
        if '/compare/' in a[1]:
            return 0, 'ahead', ''
        return 0, json.dumps(['abcdef1999']), ''
    run, calls = fake(lineal)
    with mock.patch.object(mod.subprocess, 'run', run):
        try:
            mod.gh('api', '--method', 'PUT', 'repos/o/r/pulls/9/update-branch', '-f', 'expected_head_sha=abcdef1')
            raise SystemExit('should raise')
        except subprocess.CalledProcessError as exc:
            assert '422' in exc.stderr, exc.stderr
    assert sum('--method' in c for c in calls) == 2, calls
    # Escrituras sin comprobación conocida no se repiten a ciegas; `workflow run` tampoco (R5-14: sin id de ejecución).
    for args in (('api', '--method', 'DELETE', 'repos/o/r/git/refs/heads/x'), ('api', '--method', 'POST', 'repos/o/r/issues'),
                 ('api', '--method', 'PUT', 'repos/o/r/pulls/9/update-branch'),
                 ('workflow', 'run', 'x.yml', '--ref', 'automation/x-1')):
        run, calls = fake(lambda a, n: (1, '', GRAPHQL))
        with mock.patch.object(mod.subprocess, 'run', run):
            try:
                mod.gh(*args); raise SystemExit('should raise')
            except subprocess.CalledProcessError:
                pass
        assert len(calls) == 1, (args, calls)
print('ok gh transient retry')
