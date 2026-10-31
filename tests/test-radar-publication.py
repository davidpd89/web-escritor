#!/usr/bin/env python3
"""Exercise the clock publication coordinator without GitHub mutations."""
import importlib.util
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publish', ROOT/'scripts/publish-radar-refresh.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
workflow = (ROOT/'.github/workflows/radar-clock-refresh.yml').read_text(encoding='utf-8')
assert 'actions: write' in workflow
assert 'python scripts/publish-radar-refresh.py --branch "$branch"' in workflow
assert 'gh pr merge --auto' not in workflow

def scenario(failure=None, skipped_job=False, conflict=False):
    calls = []
    dispatched = set()
    def gh(*args):
        calls.append(args)
        if args[:3] == ('api', '--paginate', '--slurp'):
            return json.dumps([[{'filename': 'convocatorias-escritores/index.html'}]])
        if args[:2] == ('repo','view'):
            return 'owner/repo'
        if args[:2] == ('pr','view'):
            if args[-1] == 'files':
                return json.dumps({'files':[{'path':'convocatorias-escritores/index.html'}]})
            if args[-1] == 'mergeable,mergeStateStatus':
                return json.dumps({'mergeable':'CONFLICTING','mergeStateStatus':'DIRTY'})
            if args[-1] == 'state,mergeCommit':
                return json.dumps({'state':'MERGED','mergeCommit':{'oid':'merged-sha'}})
            return json.dumps({'number':1,'headRefOid':'expected-sha','baseRefName':'main','state':'OPEN'})
        if args[:2] == ('run','list'):
            name = args[3]
            if name not in dispatched:
                return json.dumps([{'databaseId':1}])
            return json.dumps([
                {'databaseId':3,'headSha':'different-sha','status':'completed','conclusion':'success'},
                {'databaseId':2,'headSha':'expected-sha','status':'completed','conclusion':
                    'failure' if name == failure else 'success'},
                {'databaseId':1,'headSha':'expected-sha','status':'completed','conclusion':'success'},
            ])
        if args[:2] == ('pr','merge') and conflict:
            raise subprocess.CalledProcessError(1, ['gh', *args], stderr='Pull request is not mergeable')
        if args[:2] == ('workflow','run'):
            dispatched.add(args[2])
        if args[0] == 'api' and args[-1].endswith('/jobs'):
            return json.dumps({'jobs':[{'name':name,'conclusion':'skipped' if skipped_job else 'success',
                                       'html_url':'https://github.com/owner/repo/actions/runs/2/job/1'}
                                      for name in module.REQUIRED_JOBS.values()]})
        return ''
    with patch.object(module, 'gh', gh), patch.object(module.time, 'sleep', lambda _s: None):
        if conflict:
            try:
                module.run('automation/radar-clock-test')
                raise AssertionError('a conflicting PR must not be reported as merged')
            except module.StaleMerge:
                pass
        elif failure or skipped_job:
            try:
                module.run('automation/radar-clock-test')
                raise AssertionError('failed CI must stop publication')
            except RuntimeError:
                pass
        else:
            module.run('automation/radar-clock-test')
    merges = [call for call in calls if call[:2] == ('pr','merge')]
    deployments = [call for call in calls if call[:3] == ('workflow','run','deploy-pages.yml')]
    successes = [call for call in calls if call[0] == 'api' and 'state=success' in call]
    if conflict:
        assert not deployments
    elif failure or skipped_job:
        assert not merges and not deployments
        # A failed run gets exactly one rerun of its failed jobs before publication stops.
        assert sum(call[:2] == ('run','rerun') for call in calls) == (1 if failure else 0)
    else:
        assert len(merges) == len(deployments) == 1
        assert '--match-head-commit' in merges[0] and 'expected-sha' in merges[0]
        assert '--admin' not in merges[0]
        assert len(successes) == len(module.REQUIRED_JOBS)
        assert all('job/1' in str(call) for call in successes)

scenario()
for workflow_name in module.WORKFLOWS:
    scenario(workflow_name)
scenario(skipped_job=True)
scenario(conflict=True)
print('PASS radar publication: all real workflows required, exact SHA, failed CI never merges/deploys')
