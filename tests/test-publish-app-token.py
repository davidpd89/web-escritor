#!/usr/bin/env python3
"""R4-9: la carga abre su PR con la App y no duplica a mano los estados de las comprobaciones que ya dispara la PR.

Con GITHUB_TOKEN una PR no lanza CI: la carga despachaba cada workflow y publicaba sus estados en el commit. Con el
token de la App la PR lanza sus `pull_request`; esas se reutilizan sin estado manual (r4 F6). Sin App, o si el token
falla, todo sigue por la vía de despacho de siempre.
"""
import importlib.util
import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publish', ROOT / 'scripts/publish-radar-refresh.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
APP = {'REPARADOR_APP_ID': '1', 'REPARADOR_APP_INSTALLATION_ID': '2', 'REPARADOR_APP_PRIVATE_KEY': 'k'}


def run_gh(args, environ, token_rc=0):
    """Ejecuta module.gh con subprocess simulado; devuelve [(orden, GH_TOKEN pasado)]."""
    calls = []

    def run(cmd, **kw):
        if cmd[0] == 'node':
            assert cmd[1].endswith('app_token.mjs'), cmd
            calls.append(('node', None))
            return subprocess.CompletedProcess(cmd, token_rc, stdout='' if token_rc else 'tok-app\n', stderr='HTTP 401')
        env = kw.get('env')
        calls.append((tuple(cmd[1:3]), None if env is None else env.get('GH_TOKEN')))
        return subprocess.CompletedProcess(cmd, 0, stdout='https://github.com/o/r/pull/1\n', stderr='')

    with patch.dict(os.environ, environ, clear=False), patch.object(module.subprocess, 'run', run):
        for name in APP:
            if name not in environ:
                os.environ.pop(name, None)
        module.gh(*args)
    return calls


# Con App: `pr create` va con su token; el token no se pide para nada más.
assert run_gh(('pr', 'create', '--head', 'automation/x-1'), APP) == [('node', None), (('pr', 'create'), 'tok-app')]
assert run_gh(('pr', 'merge', '7'), APP) == [(('pr', 'merge'), None)]
# Sin App configurada: ni se intenta, entorno por defecto.
assert run_gh(('pr', 'create', '--head', 'automation/x-1'), {}) == [(('pr', 'create'), None)]
# node no está o se cuelga: tampoco tumba la carga.
for exc in (FileNotFoundError('node'), subprocess.TimeoutExpired('node', 60)):
    def boom(cmd, exc=exc, **kw):
        if cmd[0] == 'node':
            raise exc
        return subprocess.CompletedProcess(cmd, 0, stdout='u', stderr='')
    with patch.dict(os.environ, APP), patch.object(module.subprocess, 'run', boom):
        assert module.app_env() is None
# El token falla: aviso y se abre con el token por defecto (la vía de despacho sigue funcionando).
assert run_gh(('pr', 'create', '--head', 'automation/x-1'), APP, token_rc=1) == [('node', None), (('pr', 'create'), None)]


def publish(event):
    """Publica una PR cuyo único workflow requerido corre como `event`; devuelve los estados publicados a mano."""
    workflow = 'required-merge-gate.yml'
    state = {'dispatched': False, 'reports': []}

    def gh(*args):
        if args[:2] == ('repo', 'view'):
            return 'owner/repo'
        if args[:3] == ('api', '--paginate', '--slurp'):
            return json.dumps([[{'filename': 'data/x.json'}]])
        if args[:2] == ('pr', 'view'):
            if args[-1] == 'state,mergeCommit':
                return json.dumps({'state': 'MERGED', 'mergeCommit': {'oid': 'merged'}})
            return json.dumps({'number': 7, 'headRefOid': 'sha', 'baseRefName': 'main', 'baseRefOid': 'base', 'state': 'OPEN'})
        if args[:2] == ('run', 'list'):
            asked = args[args.index('--event') + 1]
            if asked == event and (event == 'pull_request' or state['dispatched']):
                return json.dumps([{'databaseId': 5, 'headSha': 'sha', 'status': 'completed', 'conclusion': 'success'}])
            return '[]'
        if args[:3] == ('api', '--method', 'POST') and args[3].endswith('/dispatches'):
            state['dispatched'] |= args[3].split('/')[-2] == workflow  # tras fusionar se despacha Pages
            return json.dumps({'workflow_run_id': 5})
        if args[0] == 'api' and args[1].endswith('/jobs'):
            return json.dumps({'jobs': [{'name': module.REQUIRED_JOBS[workflow], 'status': 'completed',
                                         'conclusion': 'success', 'html_url': 'job'}]})
        if args[0] == 'api' and '/compare/' in args[1]:
            return json.dumps({'ahead_by': 0, 'files': []})
        if args[:2] in {('pr', 'merge'), ('run', 'view')}:
            return json.dumps({'status': 'completed'})
        raise AssertionError(args)

    with patch.object(module, 'gh', gh), patch.object(module.time, 'sleep', lambda s: None), \
         patch.object(module, 'report_job', lambda *a: state['reports'].append(a[3])):
        module.publish_generated('automation/x', lambda p: True, (workflow,), pr_wait=0)
    return state


# PR abierta con la App: su ejecución pull_request se reutiliza, sin despacho ni estados a mano.
state = publish('pull_request')
assert not state['dispatched'] and state['reports'] == [], state
# PR abierta con GITHUB_TOKEN (sin App o con el token fallido): despacho y estados a mano, como antes.
state = publish('workflow_dispatch')
assert state['dispatched'] and state['reports'] == ['pending', 'success'], state

print('OK publicación: PR con la App y estados a mano solo en ejecuciones despachadas')
