#!/usr/bin/env python3
"""Un deploy de Pages cancelado por concurrencia no es un fallo si un deploy posterior publica el mismo commit.

deploy-pages.yml cancela el build anterior (`concurrency: pages-build`, cancel-in-progress): un push a main durante nuestro deploy lo cancela
y el deploy nuevo ya contiene nuestro merge. 2026-11-04: la ingesta 41906759739 mergeó #1162 y luego se dio por
fallida («Pages failed ... 41919892051») por esa cancelación. Un fallo real sigue rompiendo la publicación.
"""
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publish', ROOT / 'scripts/publish-radar-refresh.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def scenario(later_conclusion, later_contains=True, exact_conclusion='cancelled', exact_present=True, main_files=(),
             vistas_en_cola=0, ajeno=False, aun_sin_registrar=0):
    """R5-14: el deploy se despacha por la API y se sigue por SU id (10). `exact_present=False`: main avanzó y nuestro
    deploy se construyó desde `newer-sha`. `vistas_en_cola`: la ejecución tarda en arrancar. `ajeno`: otro despacho
    verde del mismo commit aparece en la lista y no puede tapar el resultado del nuestro."""
    despachos, vistas = [], {'n': 0}
    nuestro_sha = 'merged-sha' if exact_present else 'newer-sha'

    def consultar(repo, run_id):
        assert (repo, run_id) == ('owner/repo', 10), (repo, run_id)
        vistas['n'] += 1
        if vistas['n'] <= aun_sin_registrar:
            return 404, None
        if vistas['n'] <= aun_sin_registrar + vistas_en_cola:
            return 200, {'databaseId': 10, 'headSha': nuestro_sha, 'status': 'queued', 'conclusion': None}
        return 200, {'databaseId': 10, 'headSha': nuestro_sha, 'status': 'completed', 'conclusion': exact_conclusion}

    def gh(*args):
        if args[0] == 'api' and args[1:3] == ('--method', 'POST') and args[3].endswith('deploy-pages.yml/dispatches'):
            despachos.append(args)
            assert 'inputs[before_sha]=base' in args, args
            return json.dumps({'workflow_run_id': 10})
        if args[:2] == ('repo', 'view'):
            return 'owner/repo'
        if args[:3] == ('api', '--paginate', '--slurp'):
            return json.dumps([[{'filename': 'data/x.json'}]])
        if args[:2] == ('pr', 'view'):
            if args[-1] == 'state,mergeCommit':
                return json.dumps({'state': 'MERGED', 'mergeCommit': {'oid': 'merged-sha'}})
            return json.dumps({'number': 1, 'headRefOid': 'head', 'baseRefName': 'main', 'baseRefOid': 'base', 'state': 'OPEN'})
        if args[:2] == ('pr', 'merge'):
            return ''
        if args[0] == 'api' and args[1].endswith('/compare/head...main'):
            return json.dumps({'ahead_by': len(main_files), 'files': [{'filename': f} for f in main_files]})
        if args[:2] == ('run', 'list'):
            assert '--event' not in args, 'R5-14: no se compara una lista de antes y de después'
            exact = {'databaseId': 10, 'headSha': nuestro_sha, 'status': 'completed', 'conclusion': exact_conclusion}
            otro = [{'databaseId': 13, 'headSha': 'merged-sha', 'status': 'in_progress', 'conclusion': None}] if ajeno else []
            return json.dumps([*otro, exact,
                               {'databaseId': 12, 'headSha': 'newer-sha', 'status': 'completed', 'conclusion': later_conclusion},
                               {'databaseId': 11, 'headSha': 'other-sha', 'status': 'completed', 'conclusion': 'success'}])
        if args[0] == 'api' and '/compare/merged-sha...' in args[1]:
            return 'ahead' if (later_contains and 'newer-sha' in args[1]) else 'diverged'
        raise AssertionError(args)

    with patch.object(module, 'gh', gh), patch.object(module, 'consultar_ejecucion', consultar), patch.object(module.time, 'sleep', lambda s: None), \
         patch.object(module, 'report_job', lambda *a, **k: None):
        try:
            module.publish_generated('automation/x', lambda p: True, (), deploy_before=True, pr_wait=0)
        finally:
            assert len(despachos) <= 1, f'un único despacho, no {len(despachos)}'
        assert len(despachos) == 1, 'publicación sin despacho de Pages'


scenario('success')  # cancelado y sustituido por un deploy verde que contiene el merge: pasa

for kwargs, error in (({'later_conclusion': 'failure'}, RuntimeError),
                      ({'later_conclusion': 'success', 'exact_conclusion': 'failure'}, RuntimeError)):
    try:
        scenario(**kwargs)
    except error as exc:
        assert 'Pages failed' in str(exc), exc
    else:
        raise AssertionError(f'{kwargs} debía fallar')

# Ningún deploy posterior contiene el merge: no se da por bueno, se agota la espera.
clock = iter(range(0, 10**6, 60))
with patch.object(module.time, 'monotonic', lambda: next(clock)):
    try:
        scenario('success', later_contains=False)
    except TimeoutError:
        pass
    else:
        raise AssertionError('un deploy que no contiene el merge no puede validar la publicación')

# #1312: main avanzó antes del dispatch y nuestro deploy se construyó desde un commit posterior que contiene el merge.
scenario('success', exact_present=False)
try:
    scenario('success', later_contains=False, exact_present=False)
except RuntimeError as exc:
    assert 'no contiene el merge' in str(exc), exc
else:
    raise AssertionError('un deploy propio que no contiene el merge no valida la publicación')

# R5-14: la ejecución tarda en arrancar (cola de Actions): se espera a ESA, sin redespachar.
scenario('success', exact_conclusion='success', vistas_en_cola=3)
# 20/11 (carga 44792117743): la ejecución recién despachada da 404 unos segundos; se espera, sin redespachar.
scenario('success', exact_conclusion='success', aun_sin_registrar=2)
# Un 404 que no se resuelve sí falla (no se espera para siempre).
clock = iter(range(0, 10**6, 60))
with patch.object(module.time, 'monotonic', lambda: next(clock)):
    try:
        scenario('success', exact_conclusion='success', aun_sin_registrar=10**6)
    except RuntimeError as exc:
        assert 'sigue sin poder leerse (HTTP 404)' in str(exc), exc
    else:
        raise AssertionError('un 404 permanente debe fallar')

# Codex #1508: el código sale de la línea de estado de `gh api -i`, no del texto de error; CodeRabbit #1508: la
# espera no pasa del límite del job.
class Salida:
    def __init__(self, stdout):
        self.stdout = stdout
respuestas = {'404': 'HTTP/2.0 404 Not Found\r\nX: y\r\n\r\n{"message": "Not Found"}',
              '200': 'HTTP/2.0 200 OK\r\nX: y\r\n\r\n' + json.dumps({'id': 7, 'head_sha': 's', 'status': 'completed', 'conclusion': 'success'})}
with patch.object(module.subprocess, 'run', lambda cmd, **k: Salida(respuestas['404' if cmd[-1].endswith('/1') else '200'])):
    assert module.consultar_ejecucion('o/r', 1) == (404, None)
    respuestas['404'] = ''  # sin respuesta (fallo de red): código 0, se reintenta
    assert module.consultar_ejecucion('o/r', 1) == (0, None)
    assert module.consultar_ejecucion('o/r', 7) == (200, {'databaseId': 7, 'headSha': 's', 'status': 'completed', 'conclusion': 'success'})
esperas, ahora = [], [0.0]
def dormir(s):
    esperas.append(s)
    ahora[0] += s
with patch.object(module, 'consultar_ejecucion', lambda r, i: (404, None)),      patch.object(module.time, 'monotonic', lambda: ahora[0]), patch.object(module.time, 'sleep', dormir):
    try:
        module.ejecucion('o/r', 1, hasta=25)
    except RuntimeError:
        pass
    else:
        raise AssertionError('un 404 permanente debe fallar')
assert sum(esperas) == 25 and esperas[-1] == 5, esperas
intentos = iter([(0, None), (502, None), (200, {'databaseId': 1})])
with patch.object(module, 'consultar_ejecucion', lambda r, i: next(intentos)), patch.object(module.time, 'sleep', lambda s: None):
    assert module.ejecucion('o/r', 1) == {'databaseId': 1}
with patch.object(module, 'consultar_ejecucion', lambda r, i: (403, None)):
    try:
        module.ejecucion('o/r', 1)
    except RuntimeError as exc:
        assert 'HTTP 403' in str(exc), exc
    else:
        raise AssertionError('un 403 no se espera')
# R5-14: un despacho ajeno del mismo commit no tapa el fallo del nuestro.
try:
    scenario('success', exact_conclusion='failure', ajeno=True)
except RuntimeError as exc:
    assert 'Pages failed' in str(exc) and ': 10' in str(exc), exc
else:
    raise AssertionError('un deploy ajeno no puede validar el nuestro fallido')

# #1312: main cambió datos de los builders durante la CI: no se fusionan artefactos viejos.
for files, stale in ((('redes-sociales/social-metrics.json',), False), (('data/reading-catalogue.json',), True),
                     (('index.html',), True), (('pagefind/x.pf_meta',), True)):
    try:
        scenario('success', main_files=files)
    except module.StaleMerge:
        assert stale, files
    else:
        assert not stale, f'{files} debía regenerar'

print('PASS Pages cancelado por concurrencia sigue al deploy posterior que contiene el merge')
