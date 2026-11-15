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


def scenario(main_files, conflict=False):
    state = {'head': 'old', 'calls': []}

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
            files = main_files if args[1].endswith('/compare/old...main') else []
            return json.dumps({'ahead_by': len(files), 'files': [{'filename': f} for f in files]})
        if args[0] == 'api' and args[1:3] == ('--method', 'PUT'):
            if conflict:
                raise module.subprocess.CalledProcessError(1, 'gh')
            state['head'] = 'new'
            return ''
        if args[:2] == ('run', 'list'):
            ok = state['head'] == 'new'
            return json.dumps([{'databaseId': 1 if not ok else 2, 'headSha': state['head'], 'status': 'completed',
                                'conclusion': 'success' if ok else 'failure'}])
        if args[:2] in {('run', 'rerun'), ('pr', 'merge'), ('workflow', 'run'), ('run', 'cancel')}:
            return ''
        raise AssertionError(args)

    with patch.object(module, 'gh', gh), patch.object(module.time, 'sleep', lambda s: None), \
         patch.object(module, 'report_job', lambda *a, **k: None):
        module.publish_generated('automation/x', lambda p: True, ('qa.yml',), pr_wait=0)
    return state


# main arregló una prueba: se pone la rama al día y la cabeza nueva pasa y se fusiona, sin repetir el commit viejo.
state = scenario(['qa/catalogue-filter-interaction-matrix.mjs'])
assert any(c[:2] == ('pr', 'merge') and 'new' in c for c in state['calls']), state['calls']
assert not any(c[:2] == ('run', 'rerun') for c in state['calls'])

# main solo cambió datos: no hay arreglo que traer; reintento único y fallo.
for files in ([], ['data/social/snapshot.json']):
    try:
        scenario(files)
    except RuntimeError as exc:
        assert 'failed' in str(exc), exc
    else:
        raise AssertionError(f'{files}: debía fallar')

# La rama no se puede poner al día (conflicto con datos de main): se regenera.
try:
    scenario(['tests/x.py'], conflict=True)
except module.StaleMerge:
    pass
else:
    raise AssertionError('conflicto: debía pedir regenerar')
print('OK publicación: arreglos de CI en main se traen a la PR de datos')
