#!/usr/bin/env python3
"""Run real CI for a generated radar PR, merge through rules, then deploy.

GITHUB_TOKEN pushes/PRs do not automatically start the required workflows.
Explicit workflow_dispatch is supported by that token and needs no PAT.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import materializar_generados as materializar  # noqa: E402

STALE_EXIT_CODE = 75  # EX_TEMPFAIL: main avanzó durante la CI; regenerar desde main


def fresh_branch(prefix, cwd=None):
    """Nombre de rama que no existe ni en local ni en origin.

    Run 41797609876: el reintento por código 75 repetía GITHUB_RUN_ID y `git switch -c` abortaba con la rama
    del primer intento. El intento de Actions (re-run) y un sufijo creciente hacen cada nombre único.
    """
    run_id = os.environ.get('GITHUB_RUN_ID') or datetime.now().strftime('%H%M%S')
    attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '1')
    base = prefix + run_id + ('' if attempt in ('', '1') else '-a' + attempt)
    out = lambda *a: subprocess.check_output(['git', *a], cwd=cwd, text=True)
    taken = set(out('for-each-ref', '--format=%(refname:short)', 'refs/heads/').split())
    taken |= {line.split('refs/heads/', 1)[1] for line in
              out('ls-remote', '--heads', 'origin', prefix + '*').splitlines() if 'refs/heads/' in line}
    name, n = base, 2
    while name in taken:
        name, n = f'{base}-r{n}', n + 1
    return name

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


class StaleMerge(RuntimeError):
    """The PR could not merge because main moved while its CI was running."""


# Fallos de GitHub que no dicen nada del comando: repetirlo es seguro y casi siempre funciona.
# Run 41818107338: un «GraphQL: Something went wrong» en `gh pr create` tiró una carga ya trasladada y empujada.
TRANSIENT_GH = ('Something went wrong', 'HTTP 500', 'HTTP 502', 'HTTP 503', 'HTTP 504', 'Bad Gateway',
                'Service Unavailable', 'Gateway Timeout', 'timed out', 'connection reset', 'TLS handshake timeout')
GH_ATTEMPTS = 4
# Lecturas y `pr create` (que antes de repetir busca la PR) se repiten tal cual. Las escrituras solo con una
# comprobación previa (_comprobacion_escritura): repetir a ciegas un `workflow run` o un `pr merge` que sí llegó a
# GitHub duplicaría ejecuciones o fallaría tras haber funcionado.
READ_ONLY_GH = {('pr', 'view'), ('pr', 'list'), ('pr', 'checks'), ('pr', 'diff'), ('run', 'list'), ('run', 'view'),
                ('repo', 'view'), ('workflow', 'view'), ('pr', 'create')}


def _retryable(args):
    if tuple(args[:2]) in READ_ONLY_GH:
        return True
    return args[:1] == ('api',) and not any(a in ('--method', '-X', '-f', '-F', '--field', '--raw-field', '--input') for a in args)


def _existing_pr(args):
    """URL de la PR que un `gh pr create` fallido pudo llegar a crear, para no duplicarla al repetir."""
    if args[:2] != ('pr', 'create') or '--head' not in args:
        return None
    head = args[args.index('--head') + 1]
    found = subprocess.run(['gh', 'pr', 'list', '--head', head, '--state', 'open', '--json', 'url', '--jq', '.[0].url'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
    return found.stdout.strip() or None if found.returncode == 0 else None


def _flag(args, nombre):
    return args[args.index(nombre) + 1] if nombre in args and args.index(nombre) + 1 < len(args) else None


def _comprobacion_escritura(args):
    """F7 (Fable R4-10): para una escritura, (foto previa, ¿ya ocurrió?) o None si no se sabe comprobar.

    Antes de repetir una escritura cuyo primer intento dio un 5xx se mira si sí llegó a GitHub: un `pr merge` que
    fusionó, un `workflow run` que creó la ejecución, un `run rerun` que subió el número de intento, un `pr close` o
    un `run cancel` que ya tienen efecto. Un status (POST) y `update-branch` con `expected_head_sha` son idempotentes:
    repetirlos no duplica nada. Sin comprobación, la escritura no se repite (como antes).
    """
    a = tuple(args)
    if a[:2] == ('pr', 'merge') and len(a) > 2:
        return None, lambda _: json.loads(gh('pr', 'view', a[2], '--json', 'state'))['state'] == 'MERGED'
    if a[:2] == ('pr', 'close') and len(a) > 2:
        return None, lambda _: json.loads(gh('pr', 'view', a[2], '--json', 'state'))['state'] != 'OPEN'
    if a[:2] == ('run', 'cancel') and len(a) > 2:
        return None, lambda _: json.loads(gh('run', 'view', a[2], '--json', 'status'))['status'] == 'completed'
    if a[:2] == ('run', 'rerun') and len(a) > 2:
        def intento():
            return json.loads(gh('run', 'view', a[2], '--json', 'attempt'))['attempt']
        return intento(), lambda antes: intento() > antes
    if a[:2] == ('workflow', 'run') and len(a) > 2:
        def ids():
            filtro = ['--branch', _flag(a, '--ref')] if _flag(a, '--ref') else []
            return {r['databaseId'] for r in json.loads(gh('run', 'list', '--workflow', a[2], *filtro, '--event',
                                                           'workflow_dispatch', '--limit', '20', '--json', 'databaseId'))}
        return ids(), lambda antes: bool(ids() - antes)
    if a[:1] == ('api',) and _flag(a, '--method') in ('POST', 'PUT'):
        ruta = next((x for x in a[1:] if x.startswith('repos/')), '')
        if re.fullmatch(r'repos/[^/]+/[^/]+/statuses/[0-9a-f]{7,40}', ruta) or (
                ruta.endswith('/update-branch') and any(x.startswith('expected_head_sha=') for x in a)):
            return None, lambda _: False
    return None


def gh(*args: str):
    comprobacion = None if _retryable(args) else _comprobacion_escritura(args)
    for attempt in range(1, GH_ATTEMPTS + 1):
        try:
            result = subprocess.run(['gh', *args], check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            return result.stdout.strip()
        except subprocess.CalledProcessError as exc:
            # capture_output hides gh's own explanation; surface it in the job log.
            stderr = (exc.stderr or '').strip()
            print(f'gh {" ".join(args[:3])} failed: {stderr}', file=sys.stderr, flush=True)
            repetible = _retryable(args) or comprobacion is not None
            if attempt == GH_ATTEMPTS or not repetible or not any(m.lower() in stderr.lower() for m in TRANSIENT_GH):
                raise
            time.sleep(5 * attempt)
            created = _existing_pr(args)
            if created:
                return created
            if comprobacion is not None and comprobacion[1](comprobacion[0]):
                print(f'gh {" ".join(args[:3])}: el intento fallido sí llegó a GitHub; no se repite', flush=True)
                return ''


def superseding_pages(repo, merged_sha, after_id):
    """Primer deploy de Pages posterior a `after_id` cuyo commit contiene `merged_sha` (cualquier evento)."""
    runs = json.loads(gh('run', 'list', '--workflow', 'deploy-pages.yml', '--branch', 'main', '--limit', '50',
                         '--json', 'databaseId,headSha,status,conclusion'))
    for item in sorted((r for r in runs if r['databaseId'] > after_id), key=lambda r: r['databaseId']):
        if item['headSha'] == merged_sha or gh('api', f'repos/{repo}/compare/{merged_sha}...{item["headSha"]}',
                                               '--jq', '.status') in ('ahead', 'identical'):
            if item['status'] == 'completed' and item['conclusion'] == 'cancelled':
                continue
            return item
    return None


# La carga nocturna lleva su propia PR por ~75 min de CI: cada avance de main se la repite (2026-11-09: el radar
# fusionó #1239 a las 02:12 UTC en mitad de la carga). Un publicador automático que no es la carga cede el paso:
# espera a que no haya carga en curso antes de fusionar; si main avanza mientras, el StaleMerge de siempre regenera.
CARGA = ('reading-catalogue-sync.yml',)


def entrada_de_builders(path):
    """Ruta que alimenta (o es) lo generado: si main la cambió, los artefactos de la PR ya no la reflejan."""
    return materializar.generado(path) or any(fnmatch.fnmatch(path, patron) or fnmatch.fnmatch(path, patron.replace('**/', ''))
                                              for patron in materializar.FUENTES)


def main_cambio_entradas(repo, sha, hasta='main'):
    """Entradas de los builders que `hasta` (main, o la cabeza ya puesta al día) cambió desde `sha`; vacío si nada.

    main no exige ramas al día (strict desactivado: reiniciaba la CI de todas las PR abiertas), así que GitHub
    fusiona sin conflicto artefactos construidos con datos viejos (#1312, CodeRabbit). Solo cuentan las entradas
    de los builders: una instantánea de redes que entra a diario no obliga a regenerar.
    """
    data = json.loads(gh('api', f'repos/{repo}/compare/{sha}...{hasta}'))
    if not data.get('ahead_by'):
        return []
    # Un renombrado cuenta por los dos nombres: retirar una página generada (index.html -> .bak) también la cambia.
    files = [name for item in data.get('files', []) for name in (item['filename'], item.get('previous_filename')) if name]
    if len(data.get('files', [])) >= 300:  # la API trunca la lista: no se puede descartar nada
        return files[:5] + ['…']
    return [f for f in files if entrada_de_builders(f)]


def esperar_escritores(ceder_a, deadline, poll=60):
    propio = os.environ.get('GITHUB_RUN_ID', '')
    while True:
        activos = [f"{wf}#{item['databaseId']}" for wf in ceder_a
                   for item in json.loads(gh('run', 'list', '--workflow', wf, '--status', 'in_progress',
                                             '--limit', '20', '--json', 'databaseId') or '[]')
                   if str(item['databaseId']) != propio]
        if not activos:
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(f'La carga sigue en curso ({", ".join(activos)}); PR abierta, la fusiona el siguiente cron')
        print(f'ESPERA: carga en curso ({", ".join(activos)}); no se fusiona hasta que termine', flush=True)
        time.sleep(poll)


# Código que decide un veredicto de CI: si main lo cambia tras abrirse la PR, repetir la CI sobre el mismo commit
# vuelve a usar el código viejo. 15/11: #1333 y #1336 fallaron con pruebas ya arregladas en main (#1332, #1335).
QA_CODE_PREFIXES = ('qa/', 'tests/', 'scripts/', '.github/', 'package.json', 'package-lock.json')
QA_REFRESHES = 2
MIN_REFRESH_BUDGET = 1800  # segundos; con menos no cabe otra vuelta completa de CI


GENERATED_BRANCH = re.compile(r'automation/[a-zA-Z0-9][a-zA-Z0-9._-]*')


def main_cambio_qa(repo, sha):
    """Ficheros de código de CI que main tiene y la cabeza de la PR no (vacío si no hay)."""
    data = json.loads(gh('api', f'repos/{repo}/compare/{sha}...main'))
    if not data.get('ahead_by'):
        return []
    files = data.get('files', [])
    if len(files) >= 300:  # la API trunca la lista: el arreglo de QA puede estar fuera; se cuenta como cambio
        return [item['filename'] for item in files[:5]] + ['…']
    return [item['filename'] for item in files if item['filename'].startswith(QA_CODE_PREFIXES)]


def cancelar_si_sigue(run_id):
    """Cancela una ejecución obsoleta; si terminó entre el listado y la cancelación, no es un error."""
    try:
        gh('run', 'cancel', str(run_id))
    except subprocess.CalledProcessError:
        if json.loads(gh('run', 'view', str(run_id), '--json', 'status'))['status'] != 'completed':
            raise


def publish_generated(branch, allowed_path, workflows, *, timeout=5400, deploy_before=False, pr_wait=120,
                      ceder_a=(), qa_refreshes=QA_REFRESHES):
    # La rama acaba como argumento de `gh`: solo ramas generadas, sin espacios ni opciones.
    if not GENERATED_BRANCH.fullmatch(branch):
        raise ValueError(f'Rama no generada: {branch!r}')
    started = time.monotonic()
    repo = gh('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner')
    pr = json.loads(gh('pr', 'view', branch, '--json', 'number,headRefOid,baseRefName,baseRefOid,state'))
    if pr['baseRefName'] != 'main' or pr['state'] != 'OPEN':
        raise ValueError('Expected an open PR targeting main')
    sha = pr['headRefOid']
    pages = json.loads(gh('api', '--paginate', '--slurp', f'repos/{repo}/pulls/{pr["number"]}/files?per_page=100'))
    paths = [item for page in pages for item in page]
    if not paths or any(not allowed_path(item['filename']) or (item.get('previous_filename') and not allowed_path(item['previous_filename'])) for item in paths):
        raise ValueError('PR contains a path outside the generated-artifact policy')
    def runs_on_sha(workflow, event, exclude=frozenset()):
        runs = json.loads(gh('run', 'list', '--workflow', workflow, '--branch', branch,
                             '--event', event, '--limit', '100', '--json',
                             'databaseId,headSha,status,conclusion'))
        return [item for item in runs if item['databaseId'] not in exclude and item['headSha'] == sha]

    # A PR opened with a user token already starts its pull_request CI on this exact commit; dispatching the same
    # workflows again doubled the queue (20 concurrent jobs on the free plan). Reuse those runs and dispatch only
    # what is missing. A PR opened with GITHUB_TOKEN starts nothing, so after a short wait everything is dispatched.
    # Only runs that actually execute: one waiting for approval or cancelled would leave the poll waiting until timeout.
    def runnable(item):
        return item['status'] in {'queued', 'in_progress', 'completed'} and item['conclusion'] not in {
            'action_required', 'cancelled', 'stale', 'skipped', 'startup_failure'}

    source, pinned = {}, {}
    for attempt in range(pr_wait // 30 + 1):
        for workflow in workflows:
            usable = [item for item in runs_on_sha(workflow, 'pull_request') if runnable(item)]
            if workflow not in source and usable:
                # The chosen run is pinned: polling never drifts to another run of the same commit.
                source[workflow], pinned[workflow] = ('pull_request', frozenset()), usable[0]['databaseId']
        if len(source) == len(workflows) or attempt == pr_wait // 30:
            break
        time.sleep(30)
    # Dispatched workflows validate only runs started by this invocation, never old green runs.
    for workflow in workflows:
        if workflow in REQUIRED_JOBS:
            report_job(repo, sha, REQUIRED_JOBS[workflow], 'pending', f'https://github.com/{repo}/pull/{pr["number"]}')
        if workflow in source:
            print(f'REUSE pull_request run {pinned[workflow]} of {workflow} @ {sha}', flush=True)
            continue
        runs = json.loads(gh('run', 'list', '--workflow', workflow, '--branch', branch,
                             '--event', 'workflow_dispatch', '--limit', '100', '--json', 'databaseId'))
        source[workflow] = ('workflow_dispatch', frozenset(item['databaseId'] for item in runs))
        gh('workflow', 'run', workflow, '--ref', branch)

    deadline = time.monotonic() + timeout
    pending = set(workflows)
    retried = set()
    while pending:
        if time.monotonic() >= deadline:
            raise TimeoutError(f'CI timed out; PR left open: {sorted(pending)}')
        for workflow in sorted(pending):
            current = [item for item in runs_on_sha(workflow, *source[workflow])
                       if workflow not in pinned or item['databaseId'] == pinned[workflow]]
            if not current:
                continue
            result = current[0]
            if result['status'] != 'completed':
                continue
            url = f'https://github.com/{repo}/actions/runs/{result["databaseId"]}'
            context = REQUIRED_JOBS.get(workflow)
            if result['conclusion'] != 'success':
                # Browser jobs fail sporadically (one in four bot PRs lost its day this way);
                # a single rerun of the failed jobs on the same commit still needs real green.
                # main cambió entradas de lo generado (datos, html, plantillas) aunque no tocara código de QA: repetir
                # el mismo commit, o traer main con update-branch, deja lo generado desfasado frente al main actual
                # (un simple merge de dos regeneraciones no es una regeneración real). Se regenera desde main siempre,
                # haya o no cambiado también el código de QA (16/11: PR #1328 se quedó 3 noches reintentando lo mismo).
                entradas = main_cambio_entradas(repo, sha)
                if entradas:
                    raise StaleMerge(f'main cambió entradas de lo generado ({", ".join(entradas[:5])}) durante la CI '
                                     f'de #{pr["number"]}; se regenera desde main')
                # Si main cambió el código de CI desde esta cabeza (un arreglo de pruebas a mitad de carga), repetir el
                # mismo commit da el mismo fallo: se trae main a la rama y se valida la cabeza nueva desde cero.
                remaining = timeout - (time.monotonic() - started)
                cambios = main_cambio_qa(repo, sha) if qa_refreshes > 0 and remaining > MIN_REFRESH_BUDGET else []
                if cambios:
                    print(f'REFRESH {workflow} ({result["databaseId"]}) falló y main cambió {", ".join(cambios[:5])}; '
                          'actualizo la rama con main y repito la CI', flush=True)
                    try:
                        gh('api', '--method', 'PUT', f'repos/{repo}/pulls/{pr["number"]}/update-branch',
                           '-f', f'expected_head_sha={sha}')
                    except subprocess.CalledProcessError:
                        raise StaleMerge(f'#{pr["number"]} no se puede poner al día con main; se regenera') from None
                    for _ in range(20):  # la API responde 202 antes de mover la cabeza
                        nueva = json.loads(gh('pr', 'view', branch, '--json', 'headRefOid'))['headRefOid']
                        if nueva != sha:
                            break
                        time.sleep(15)
                    else:
                        raise RuntimeError(f'update-branch de #{pr["number"]} no movió la cabeza; PR left open')
                    # update-branch fusiona la main de ese instante, no la comparada arriba: si entre medias entraron
                    # entradas de builders, ya están en la cabeza nueva y solo se ven comparando las dos cabezas.
                    entradas = main_cambio_entradas(repo, sha, nueva)
                    if entradas:
                        raise StaleMerge(f'la puesta al día de #{pr["number"]} trajo entradas de lo generado '
                                         f'({", ".join(entradas[:5])}); se regenera desde main')
                    if context:
                        report_job(repo, sha, context, 'failure', url)
                    for other in pending - {workflow}:  # la cabeza vieja ya no se fusiona: libera la cola
                        for item in runs_on_sha(other, *source[other]):
                            if item['status'] != 'completed':
                                cancelar_si_sigue(item['databaseId'])
                    remaining = timeout - (time.monotonic() - started)  # descontar la actualización y los sondeos
                    return publish_generated(branch, allowed_path, workflows, timeout=int(remaining),
                                             deploy_before=deploy_before, pr_wait=pr_wait, ceder_a=ceder_a,
                                             qa_refreshes=qa_refreshes - 1)
                if workflow not in retried:
                    retried.add(workflow)
                    gh('run', 'rerun', str(result['databaseId']), '--failed')
                    print(f'RETRY {workflow} ({result["databaseId"]})', flush=True)
                    continue
                if context:
                    report_job(repo, sha, context, 'failure', url)
                raise RuntimeError(f'{workflow} failed ({result["databaseId"]}); PR left open')
            if context:
                jobs = json.loads(gh('api', f'repos/{repo}/actions/runs/{result["databaseId"]}/jobs'))['jobs']
                matching = [job for job in jobs if job['name'] == context]
                # GitHub can report the run as completed while its job record still reads in_progress
                # (lighthouse 42011162941: every step green, job closed minutes later). Keep polling
                # until the job itself closes; the deadline still bounds the wait.
                if len(matching) == 1 and matching[0].get('status') != 'completed':
                    continue
                if len(matching) != 1 or matching[0]['conclusion'] != 'success':
                    report_job(repo, sha, context, 'failure', url)
                    raise RuntimeError(f'{workflow}: required job missing, skipped or unsuccessful')
                report_job(repo, sha, context, 'success', matching[0]['html_url'])
            pending.remove(workflow)
            print(f'PASS {workflow} @ {sha}', flush=True)
        if pending:
            time.sleep(30)

    esperar_escritores(ceder_a, deadline)
    movidas = main_cambio_entradas(repo, sha)
    if movidas:
        raise StaleMerge(f'main cambió entradas de lo generado durante la CI de #{pr["number"]} '
                         f'({", ".join(movidas[:5])}); se regenera desde main')
    # A concurrent edit or newer main must pass normal branch rules too.
    # No --admin or bypass; every reported success above has real job evidence.
    try:
        gh('pr', 'merge', str(pr['number']), '--squash', '--match-head-commit', sha,
           '--subject', f'Actualizar artefactos generados (#{pr["number"]})',
           '--body', 'Actualización automática validada por los workflows y las reglas de main.')
    except subprocess.CalledProcessError:
        state = json.loads(gh('pr', 'view', str(pr['number']), '--json', 'mergeable,mergeStateStatus'))
        if state.get('mergeable') == 'CONFLICTING' or state.get('mergeStateStatus') in {'DIRTY', 'BEHIND'}:
            raise StaleMerge(f'main avanzó durante la CI de #{pr["number"]}; se regenera desde main') from None
        raise
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
        followed = None  # deploy posterior que contiene merged_sha, tras cancelarse el nuestro por concurrencia
        while time.monotonic() < deadline:
            if followed is None:
                runs = json.loads(gh('run', 'list', '--workflow', 'deploy-pages.yml', '--event', 'workflow_dispatch', '--limit', '100', '--json', 'databaseId,headSha,status,conclusion'))
                exact = [r for r in runs if r['databaseId'] not in before_ids and r['headSha'] == merged_sha]
                # `--ref main` despacha desde la punta: si main avanzó tras la fusión no hay run con el SHA exacto, y
                # vale un deploy posterior que contenga el merge (#1312, Codex y CodeRabbit).
                current = exact[0] if exact else superseding_pages(repo, merged_sha, max(before_ids, default=0))
            else:
                current = superseding_pages(repo, merged_sha, followed)
            if current and current['status'] == 'completed':
                if current['conclusion'] == 'cancelled':
                    # deploy-pages tiene concurrency cancel-in-progress: un push posterior a main cancela este deploy
                    # y publica también nuestro commit. 2026-11-04: la ingesta 41906759739 fallaba por eso tras mergear.
                    nxt = superseding_pages(repo, merged_sha, current['databaseId'])
                    if nxt:
                        print(f'Pages {current["databaseId"]} cancelled; following {nxt["databaseId"]} @ {nxt["headSha"]}', flush=True)
                        followed = current['databaseId']
                    time.sleep(30)
                    continue
                if current['conclusion'] != 'success':
                    raise RuntimeError(f'Pages failed for {merged_sha}: {current["databaseId"]}')
                print(f'PASS Pages and production smoke @ {merged_sha}: {current["databaseId"]} @ {current["headSha"]}', flush=True)
                return
            time.sleep(30)
        raise TimeoutError(f'Pages did not complete for exact merged commit {merged_sha}')


def run(branch: str, timeout: int = 5400):
    if not re.fullmatch(r'automation/radar-clock-[a-zA-Z0-9-]+', branch):
        raise ValueError('Only generated radar-clock branches are accepted')
    allowed = {'convocatorias-escritores/index.html', 'convocatorias-escritores/opportunities.json',
               'convocatorias-escritores/deadlines.ics', '.lycheeignore'}
    publish_generated(branch, lambda p: p in allowed or p.startswith('pagefind/')
                      or (p.startswith('editoriales/') and p.endswith('.html')), WORKFLOWS, timeout=timeout,
                      ceder_a=CARGA)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branch', required=True)
    args = parser.parse_args()
    run(args.branch)
