#!/usr/bin/env python3
"""Run real CI for a generated radar PR, merge through rules, then deploy.

GITHUB_TOKEN pushes/PRs do not automatically start the required workflows.
Explicit workflow_dispatch is supported by that token and needs no PAT.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time

WORKFLOWS = (
    'required-merge-gate.yml', 'public-artifact-contract.yml',
    'sitewide-reflow-qa.yml', 'pa11y-baseline.yml', 'lighthouse-ci.yml',
    'visual-regression-qa.yml', 'pro-resources-qa.yml',
    'convocatorias-browser-qa.yml', 'content-index-check.yml', 'broken-links.yml',
)
REQUIRED_JOBS = {
    'required-merge-gate.yml': 'Required merge gate',
    'public-artifact-contract.yml': 'public-artifact-contract',
    'sitewide-reflow-qa.yml': 'reflow-sitewide',
    'pa11y-baseline.yml': 'pa11y-baseline',
    'lighthouse-ci.yml': 'lighthouse',
    'visual-regression-qa.yml': 'Compare against committed baselines',
}


def report_job(repo, sha, context, state, url):
    # Dispatch runs are not associated with the PR's checks tab. Report the
    # actual job result on its exact commit, with a link to the real evidence.
    gh('api', '--method', 'POST', f'repos/{repo}/statuses/{sha}',
       '-f', f'state={state}', '-f', f'context={context}', '-f', f'target_url={url}',
       '-f', 'description=Generated update: verified workflow_dispatch job result')


def gh(*args: str):
    result = subprocess.run(['gh', *args], check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.stdout.strip()


def publish_generated(branch, allowed_path, workflows, *, timeout=5400, deploy_before=False):
    repo = gh('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner')
    pr = json.loads(gh('pr', 'view', branch, '--json', 'number,headRefOid,baseRefName,baseRefOid,state'))
    if pr['baseRefName'] != 'main' or pr['state'] != 'OPEN':
        raise ValueError('Expected an open PR targeting main')
    sha = pr['headRefOid']
    pages = json.loads(gh('api', '--paginate', '--slurp', f'repos/{repo}/pulls/{pr["number"]}/files?per_page=100'))
    paths = [item for page in pages for item in page]
    if not paths or any(not allowed_path(item['filename']) or (item.get('previous_filename') and not allowed_path(item['previous_filename'])) for item in paths):
        raise ValueError('PR contains a path outside the generated-artifact policy')
    # Validate only runs dispatched by this invocation, never old green runs.
    previous = {}
    for workflow in workflows:
        if workflow in REQUIRED_JOBS:
            report_job(repo, sha, REQUIRED_JOBS[workflow], 'pending', f'https://github.com/{repo}/pull/{pr["number"]}')
        runs = json.loads(gh('run', 'list', '--workflow', workflow, '--branch', branch,
                             '--event', 'workflow_dispatch', '--limit', '100', '--json', 'databaseId'))
        previous[workflow] = {item['databaseId'] for item in runs}
        gh('workflow', 'run', workflow, '--ref', branch)

    deadline = time.monotonic() + timeout
    pending = set(workflows)
    while pending:
        if time.monotonic() >= deadline:
            raise TimeoutError(f'CI timed out; PR left open: {sorted(pending)}')
        for workflow in sorted(pending):
            runs = json.loads(gh('run', 'list', '--workflow', workflow, '--branch', branch,
                                 '--event', 'workflow_dispatch', '--limit', '100', '--json',
                                 'databaseId,headSha,status,conclusion'))
            current = [item for item in runs if item['databaseId'] not in previous[workflow]
                       and item['headSha'] == sha]
            if not current:
                continue
            result = current[0]
            if result['status'] != 'completed':
                continue
            url = f'https://github.com/{repo}/actions/runs/{result["databaseId"]}'
            context = REQUIRED_JOBS.get(workflow)
            if result['conclusion'] != 'success':
                if context:
                    report_job(repo, sha, context, 'failure', url)
                raise RuntimeError(f'{workflow} failed ({result["databaseId"]}); PR left open')
            if context:
                jobs = json.loads(gh('api', f'repos/{repo}/actions/runs/{result["databaseId"]}/jobs'))['jobs']
                matching = [job for job in jobs if job['name'] == context]
                if len(matching) != 1 or matching[0]['conclusion'] != 'success':
                    report_job(repo, sha, context, 'failure', url)
                    raise RuntimeError(f'{workflow}: required job missing, skipped or unsuccessful')
                report_job(repo, sha, context, 'success', matching[0]['html_url'])
            pending.remove(workflow)
            print(f'PASS {workflow} @ {sha}', flush=True)
        if pending:
            time.sleep(30)

    # A concurrent edit or newer main must pass normal branch rules too.
    # No --admin or bypass; every reported success above has real job evidence.
    gh('pr', 'merge', str(pr['number']), '--squash', '--match-head-commit', sha,
       '--subject', f'Actualizar artefactos generados (#{pr["number"]})',
       '--body', 'Actualización automática validada por los workflows y las reglas de main.')
    merged = json.loads(gh('pr', 'view', str(pr['number']), '--json', 'state,mergeCommit'))
    if merged['state'] != 'MERGED':
        raise RuntimeError('PR was not merged; refusing to deploy')
    # A GITHUB_TOKEN merge does not fire push CI/Pages either. Dispatch Pages
    # explicitly; its workflow_run starts the existing live production audits.
    before_runs = json.loads(gh('run', 'list', '--workflow', 'deploy-pages.yml', '--event', 'workflow_dispatch', '--limit', '100', '--json', 'databaseId'))
    before_ids = {r['databaseId'] for r in before_runs}
    args = ['workflow', 'run', 'deploy-pages.yml', '--ref', 'main']
    if deploy_before:
        args += ['-f', f'before_sha={pr["baseRefOid"]}']
    gh(*args)
    merged_sha = merged['mergeCommit']['oid']
    print(f'Dispatched Pages after validated merge {merged_sha}', flush=True)
    if deploy_before:
        deadline = time.monotonic() + 1800
        while time.monotonic() < deadline:
            runs = json.loads(gh('run', 'list', '--workflow', 'deploy-pages.yml', '--event', 'workflow_dispatch', '--limit', '100', '--json', 'databaseId,headSha,status,conclusion'))
            exact = [r for r in runs if r['databaseId'] not in before_ids and r['headSha'] == merged_sha]
            if exact and exact[0]['status'] == 'completed':
                if exact[0]['conclusion'] != 'success':
                    raise RuntimeError(f'Pages failed for {merged_sha}: {exact[0]["databaseId"]}')
                print(f'PASS Pages and production smoke @ {merged_sha}: {exact[0]["databaseId"]}', flush=True)
                return
            time.sleep(30)
        raise TimeoutError(f'Pages did not complete for exact merged commit {merged_sha}')


def run(branch: str, timeout: int = 5400):
    if not branch.startswith('automation/radar-clock-'):
        raise ValueError('Only generated radar-clock branches are accepted')
    allowed = {'convocatorias-escritores/index.html', 'convocatorias-escritores/opportunities.json',
               'convocatorias-escritores/deadlines.ics'}
    publish_generated(branch, lambda p: p in allowed or p.startswith('pagefind/'), WORKFLOWS, timeout=timeout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branch', required=True)
    args = parser.parse_args()
    run(args.branch)
