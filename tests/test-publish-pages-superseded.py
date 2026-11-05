#!/usr/bin/env python3
"""Un deploy de Pages cancelado por concurrencia no es un fallo si un deploy posterior publica el mismo commit.

deploy-pages.yml usa `concurrency: pages, cancel-in-progress: true`: un push a main durante nuestro deploy lo cancela
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


def scenario(later_conclusion, later_contains=True, exact_conclusion='cancelled'):
    def gh(*args):
        if args[:2] == ('repo', 'view'):
            return 'owner/repo'
        if args[:3] == ('api', '--paginate', '--slurp'):
            return json.dumps([[{'filename': 'data/x.json'}]])
        if args[:2] == ('pr', 'view'):
            if args[-1] == 'state,mergeCommit':
                return json.dumps({'state': 'MERGED', 'mergeCommit': {'oid': 'merged-sha'}})
            return json.dumps({'number': 1, 'headRefOid': 'head', 'baseRefName': 'main', 'baseRefOid': 'base', 'state': 'OPEN'})
        if args[:2] == ('pr', 'merge') or args[:2] == ('workflow', 'run'):
            return ''
        if args[:2] == ('run', 'list'):
            exact = {'databaseId': 10, 'headSha': 'merged-sha', 'status': 'completed', 'conclusion': exact_conclusion}
            if '--event' in args:  # sondeo del deploy exacto disparado por la publicación
                return json.dumps([exact] if 'databaseId,headSha,status,conclusion' in args else [{'databaseId': 1}])
            return json.dumps([exact,
                               {'databaseId': 12, 'headSha': 'newer-sha', 'status': 'completed', 'conclusion': later_conclusion},
                               {'databaseId': 11, 'headSha': 'other-sha', 'status': 'completed', 'conclusion': 'success'}])
        if args[0] == 'api' and '/compare/merged-sha...' in args[1]:
            return 'ahead' if (later_contains and 'newer-sha' in args[1]) else 'diverged'
        raise AssertionError(args)

    with patch.object(module, 'gh', gh), patch.object(module.time, 'sleep', lambda s: None), \
         patch.object(module, 'report_job', lambda *a, **k: None):
        module.publish_generated('automation/x', lambda p: True, (), deploy_before=True, pr_wait=0)


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

print('PASS Pages cancelado por concurrencia sigue al deploy posterior que contiene el merge')
