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
# An expired call must not leave its lychee exception behind to fail the bot's PR:
# the refresh prunes it, and workflow allowlist, git add and publisher all accept it.
prune = workflow.index('python tests/test-lychee-ignore-hygiene.py --prune-unused')
assert workflow.index('python scripts/build-pagefind-index.py') < prune < workflow.index('name: Validate regenerated artifacts')
assert 'deadlines.ics|.lycheeignore|pagefind/*|editoriales/*.html)' in workflow
# The editorial stale warnings (>90 days) also follow the real clock and the merge gate checks them with the real
# date (check-professional-resources). The clock refresh detects that drift, regenerates and publishes them: on 10/11
# the intake that used to regenerate them failed and every PR went red at release-readiness.
clock = workflow[workflow.index('name: Resolve Madrid civil date'):workflow.index('name: Regenerate deterministic')]
assert 'python scripts/check-professional-resources.py' in clock
regen = workflow[workflow.index('name: Regenerate deterministic'):workflow.index('name: Detect whether')]
assert 'python scripts/build-editoriales.py --data data/editoriales.json --output .' in regen
assert '            editoriales/ \
' in workflow
publisher = (ROOT/'scripts/publish-radar-refresh.py').read_text(encoding='utf-8')
assert "p.startswith('editoriales/') and p.endswith('.html')" in publisher
assert '            .lycheeignore \\\n' in workflow
assert "'.lycheeignore'}" in (ROOT/'scripts/publish-radar-refresh.py').read_text(encoding='utf-8')

def scenario(failure=None, skipped_job=False, conflict=False, pr_runs=(), blocked=(), lagging_job=0, carga=0):
    calls = []
    carga = {'left': carga}
    lag = {'left': lagging_job}
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
            if '--status' in args:
                # Carga nocturna en curso las primeras `carga` consultas; la propia ejecución (GITHUB_RUN_ID) no cuenta.
                if carga['left']:
                    carga['left'] -= 1
                    return json.dumps([{'databaseId': 99}, {'databaseId': 4242}])
                return json.dumps([{'databaseId': 4242}])
            if args[args.index('--event') + 1] == 'pull_request':
                if name in blocked:
                    # Waiting for approval or cancelled: never executes, so it must not be reused.
                    return json.dumps([
                        {'databaseId':7,'headSha':'expected-sha','status':'completed','conclusion':'action_required'},
                        {'databaseId':6,'headSha':'expected-sha','status':'completed','conclusion':'cancelled'},
                    ])
                if name not in pr_runs:
                    return json.dumps([])
                return json.dumps([
                    {'databaseId':5,'headSha':'different-sha','status':'completed','conclusion':'success'},
                    {'databaseId':4,'headSha':'expected-sha','status':'completed','conclusion':
                        'failure' if name == failure else 'success'},
                ])
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
            if lag['left']:
                # Run already completed, job record not yet closed.
                lag['left'] -= 1
                return json.dumps({'jobs':[{'name':name,'status':'in_progress','conclusion':None,
                                           'html_url':'https://github.com/owner/repo/actions/runs/2/job/1'}
                                          for name in module.REQUIRED_JOBS.values()]})
            return json.dumps({'jobs':[{'name':name,'status':'completed','conclusion':'skipped' if skipped_job else 'success',
                                       'html_url':'https://github.com/owner/repo/actions/runs/2/job/1'}
                                      for name in module.REQUIRED_JOBS.values()]})
        return ''
    with patch.object(module, 'gh', gh), patch.object(module.time, 'sleep', lambda _s: None), \
            patch.dict(module.os.environ, {'GITHUB_RUN_ID': '4242'}):
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
        # Workflows already running for the PR's exact commit are reused, never dispatched twice.
        assert {call[2] for call in calls if call[:2] == ('workflow','run')} == set(module.WORKFLOWS) - set(pr_runs) | {'deploy-pages.yml'}
        assert '--match-head-commit' in merges[0] and 'expected-sha' in merges[0]
        assert '--admin' not in merges[0]
        assert len(successes) == len(module.REQUIRED_JOBS)
        assert all('job/1' in str(call) for call in successes)

scenario()
for workflow_name in module.WORKFLOWS:
    scenario(workflow_name)
scenario(skipped_job=True)
reused = module.WORKFLOWS[:4]
scenario(pr_runs=reused)
scenario(reused[0], pr_runs=reused)
scenario(pr_runs=reused[2:], blocked=reused[:2])
scenario(conflict=True)
# A job record that lags behind its completed run is awaited, not reported as failed.
scenario(lagging_job=2)
# Con la carga en curso no se fusiona hasta que termine: espera, consulta otra vez y entonces fusiona.
scenario(carga=3)
# Si la carga no termina antes del plazo, la PR queda abierta y no se fusiona ni se despliega.
def sin_fin():
    calls = []
    def gh(*args):
        calls.append(args)
        return json.dumps([{'databaseId': 99}])
    with patch.object(module, 'gh', gh), patch.object(module.time, 'sleep', lambda _s: None):
        try:
            module.esperar_escritores(module.CARGA, deadline=0)
            raise AssertionError('una carga eterna no puede dejar fusionar')
        except TimeoutError as exc:
            assert 'PR abierta' in str(exc)
    assert not any(c[:2] == ('pr', 'merge') for c in calls)
    # Sin nada a lo que ceder (la propia carga publicando) no se consulta nada.
    calls.clear()
    with patch.object(module, 'gh', gh):
        module.esperar_escritores((), deadline=0)
    assert not calls
sin_fin()
print('PASS radar publication: all real workflows required, exact SHA, failed CI never merges/deploys')
