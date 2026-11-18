#!/usr/bin/env python3
"""Si la CI de una PR de datos falla y main ya cambió el código de pruebas, se pone la rama al día y se repite la CI.

15/11/2026: #1333 y #1336 fallaron con pruebas que main ya había arreglado (#1332, #1335). El publicador repetía la CI
sobre el mismo commit, con el código viejo, y la carga entera (~75 min) se perdía. Sin cambios de código en main, el
fallo sigue siendo un fallo (tras el reintento único de siempre).
"""
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publish', ROOT / 'scripts/publish-radar-refresh.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def scenario(main_files, conflict=False, workflows=('qa.yml',), cancel_race=False, traidos=()):
    """`traidos`: lo que la puesta al día metió de verdad en la rama (main pudo avanzar tras la comparación)."""
    state = {'head': 'old', 'calls': [], 'clock': 0.0}

    def gh(*args):
        state['calls'].append(args)
        if args[:2] == ('repo', 'view'):
            return 'owner/repo'
        if args[:3] == ('api', '--paginate', '--slurp'):
            return json.dumps([[{'filename': 'data/x.json'}]])
        if args[:2] == ('pr', 'view'):
            if args[-1] == 'headRefOid':
                return json.dumps({'headRefOid': state['head']})
            if args[-1] == 'state,mergeCommit':
                return json.dumps({'state': 'MERGED', 'mergeCommit': {'oid': 'merged'}})
            return json.dumps({'number': 7, 'headRefOid': state['head'], 'baseRefName': 'main',
                               'baseRefOid': 'base', 'state': 'OPEN'})
        if args[0] == 'api' and '/compare/' in args[1]:
            files = {'/compare/old...main': main_files, '/compare/old...new': list(main_files) + list(traidos)}.get(
                args[1][args[1].index('/compare/'):], [])
            return json.dumps({'ahead_by': len(files), 'files': [{'filename': f} for f in files]})
        if args[0] == 'api' and args[1:3] == ('--method', 'PUT'):
            if conflict:
                raise module.subprocess.CalledProcessError(1, 'gh')
            state['head'] = 'new'
            return ''
        if args[:2] == ('run', 'list') and cancel_race and args[3] == 'b.yml':
            # La ejecución de la cabeza vieja sigue listada (en marcha) también después de la puesta al día.
            vieja = [{'databaseId': 9, 'headSha': 'old', 'status': 'in_progress', 'conclusion': None}]
            nueva = [{'databaseId': 2, 'headSha': 'new', 'status': 'completed', 'conclusion': 'success'}]
            return json.dumps(vieja + (nueva if state['head'] == 'new' else []))
        if args[:2] == ('run', 'cancel') and cancel_race:
            state['cancelado'] = True
            raise module.subprocess.CalledProcessError(1, 'gh')  # terminó entre el listado y la cancelación
        if args[0] == 'api' and args[1:3] == ('--method', 'POST') and args[3].endswith('/dispatches'):
            return json.dumps({'workflow_run_id': 3})
        if args[:3] == ('run', 'view', '3'):
            return json.dumps({'databaseId': 3, 'headSha': 'merged', 'status': 'completed', 'conclusion': 'success'})
        if args[:2] == ('run', 'view'):
            return json.dumps({'status': 'completed'})
        if args[:2] == ('run', 'list'):
            ok = state['head'] == 'new'
            return json.dumps([{'databaseId': 1 if not ok else 2, 'headSha': state['head'], 'status': 'completed',
                                'conclusion': 'success' if ok else 'failure'}])
        if args[:2] in {('run', 'rerun'), ('pr', 'merge'), ('run', 'cancel')}:
            return ''
        raise AssertionError(args)

    with patch.object(module, 'gh', gh), patch.object(module.time, 'sleep', lambda s: None), \
         patch.object(module, 'report_job', lambda *a, **k: None):
        module.publish_generated('automation/x', lambda p: True, workflows, pr_wait=0)
    return state


# main arregló una prueba: se pone la rama al día y la cabeza nueva pasa y se fusiona, sin repetir el commit viejo.
state = scenario(['qa/catalogue-filter-interaction-matrix.mjs'])
assert any(c[:2] == ('pr', 'merge') and 'new' in c for c in state['calls']), state['calls']
assert not any(c[:2] == ('run', 'rerun') for c in state['calls'])

# main no cambió ni código de QA ni entradas de los builders: no hay arreglo que traer ni nada que regenerar;
# reintento único y fallo.
for files in ([], ['.ci/performance-budget.json']):
    try:
        scenario(files)
    except RuntimeError as exc:
        assert 'failed' in str(exc), exc
    else:
        raise AssertionError(f'{files}: debía fallar')

# main cambió solo entradas de los builders (datos, html, plantillas), sin tocar código de QA: un reintento repetiría
# el mismo fallo contra lo generado ya desfasado y update-branch solo mezclaría dos regeneraciones distintas del
# mismo artefacto; se regenera desde main sin esperar a que cambie también el código (16/11: PR #1328, tres noches
# reintentando el mismo commit porque main solo había movido `recomendaciones/**` y `data/**`).
for files in (['data/reading-catalogue.json'], ['recomendaciones/libros/x/index.html']):
    try:
        scenario(files)
    except module.StaleMerge as exc:
        assert 'entradas de lo generado' in str(exc), exc
    else:
        raise AssertionError(f'{files}: debía pedir regenerar')

# La rama no se puede poner al día (conflicto con datos de main): se regenera.
try:
    scenario(['tests/x.py'], conflict=True)
except module.StaleMerge:
    pass
else:
    raise AssertionError('conflicto: debía pedir regenerar')
# main trajo a la vez un arreglo de QA y entradas de los builders: actualizar la rama dejaría lo generado viejo y
# ocultaría el cambio a la comprobación previa a fusionar; se regenera desde main (Codex/CodeRabbit en #1337).
try:
    scenario(['qa/x.mjs', 'data/reading-catalogue.json'])
except module.StaleMerge as exc:
    assert 'reading-catalogue.json' in str(exc), exc
else:
    raise AssertionError('entradas de builders en main: debía pedir regenerar')

# Comparación truncada (300 ficheros): el arreglo de QA puede no estar en la lista; no se repite el commit viejo.
truncada = json.dumps({'ahead_by': 400, 'files': [{'filename': f'data/{i}.json'} for i in range(300)]})
with patch.object(module, 'gh', lambda *a: truncada):
    assert module.main_cambio_qa('o/r', 'old'), 'truncada: debe contar como cambio'

# Una ejecución obsoleta termina justo antes de cancelarla: no tumba la publicación.
state = scenario(['qa/x.mjs'], workflows=('qa.yml', 'b.yml'), cancel_race=True)
assert state.get('cancelado'), 'el escenario debe intentar cancelar la ejecución vieja'
assert any(c[:2] == ('pr', 'merge') and 'new' in c for c in state['calls']), state['calls']

# main avanzó entre la comparación y la puesta al día y trajo entradas de builders: se regenera (CodeRabbit, #1337).
try:
    scenario(['qa/x.mjs'], traidos=['data/reading-catalogue.json'])
except module.StaleMerge as exc:
    assert 'puesta al día' in str(exc), exc
else:
    raise AssertionError('entradas traídas por la puesta al día: debía pedir regenerar')

print('OK publicación: arreglos de CI en main se traen a la PR de datos')
