#!/usr/bin/env python3
"""Publish generated book updates through real CI, protected main and Pages."""
import argparse
import importlib.util
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication', ROOT / 'scripts/publish-radar-refresh.py')
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)

EXACT = {'assets/page-order.generated.js', 'assets/reading-market.json', 'data/reading-catalogue.json', 'data/reading-authors.json', 'data/reading-publishers.json', 'data/reading-intake-state.json', 'data/reading-amazon-audit.json', 'data/reading-pinterest-state.json', 'data/reading-quarantine.json',
         'data/content-registry.json', 'recomendaciones/index.html', 'recomendaciones/autores/index.html',
         'recomendaciones/editoriales/index.html', 'recomendaciones/proximos-lanzamientos.ics', 'recomendaciones/ofertas.json', 'recomendaciones/llms.txt', 'mapa-del-sitio/index.html',
         'sitemap.xml', 'editoriales-sitemap.xml'}


def allowed_path(path):
    return path in EXACT or bool(re.fullmatch(
        r'(?:recomendaciones/(?:libros|autores|editoriales)/[a-z0-9-]+/index\.html|'
        r'recomendaciones/pagina/[0-9]+/index\.html|'
        r'editoriales/[a-z0-9-]+/index\.html|'
        r'assets/reading-covers/isbn-97[89][0-9]{10}(?:-320)?\.webp|'
        r'assets/reading-audio/[a-z0-9-]+-[a-f0-9]{12}\.mp3|'
        r'assets/pinterest/feeds/[a-z0-9-]+\.xml|'
        r'data/reading-texts/(?:isbn-97[89][0-9]{10}|lib-[0-9]{4})\.json|'
        r'pagefind/[A-Za-z0-9_./-]+)', path)) and '..' not in path.split('/')


def clean_main_tree(root, tree):
    """Árbol de origin/main limpio para publicar desde este equipo, con las dependencias de Node del checkout principal.

    git clean no toca node_modules (está ignorado) y un worktree nuevo no lo trae: sin él Pagefind no corre y la
    publicación se para. Así se paró la auditoría de Amazon del 07/11 con 603 formatos y 116 portadas ya aplicados.
    """
    def git(*args, cwd=root):
        subprocess.run(['git', *args], cwd=cwd, check=True)
    git('fetch', '-q', 'origin', 'main')
    if not tree.exists():
        git('worktree', 'add', '--detach', str(tree), 'origin/main')
    git('reset', '-q', '--hard', 'origin/main', cwd=tree)
    git('clean', '-qfd', cwd=tree)
    link_node_modules(tree)
    return tree


def link_node_modules(tree):
    """Enlaza tree/node_modules al node_modules del checkout principal del repositorio (no lo copia)."""
    common = subprocess.check_output(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                                     cwd=tree, text=True).strip()
    source, link = Path(common).parent / 'node_modules', Path(tree) / 'node_modules'
    if link.exists() or not source.is_dir():
        return
    if os.path.lexists(link):  # enlace roto
        if os.name == 'nt':
            os.rmdir(link)
        else:
            link.unlink()
    if os.name == 'nt':
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(source)], check=True, stdout=subprocess.DEVNULL)
    else:
        link.symlink_to(source, target_is_directory=True)


def resume_pending(branch):
    """Resume current generated work; otherwise say how to rebuild it from main.

    Returns 'resumed' (published as is), 'carry' (green but behind main: the caller moves its source data onto
    current main and rebuilds pages and indices, without querying the sources again; the PR stays open until the
    replacement exists; also red but behind main: the fix may already be in main, so its data is rebuilt with the
    new code instead of being queried again, 06/11: one failed test discarded 181 accepted books) or 'regenerate'
    (red after its rerun and already on current main: closed, the caller runs the full intake).
    Old HTML/indices may conflict with a newer renderer or lack new workflows, so stale output is never merged.
    Never close a human PR or a proposal containing non-generated changes (generated_by_bot lo decide por los
    commits, no por quién abrió la PR).
    """
    if not re.fullmatch(r'automation/reading-catalogue-[a-zA-Z0-9-]+', branch):
        raise ValueError('Only generated reading-catalogue branches are accepted')
    repo = publication.gh('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner')
    pr = json.loads(publication.gh('pr', 'view', branch, '--json',
                                  'number,headRefOid,baseRefName,state'))
    if pr['state'] != 'OPEN' or pr['baseRefName'] != 'main':
        raise ValueError('Expected an open PR targeting main')
    comparison = json.loads(publication.gh('api',
        f'repos/{repo}/compare/main...{pr["headRefOid"]}'))
    # A commit that already failed after the publisher's rerun fails again: regenerate it from main
    # (newer code and data) instead of blocking every later batch on the same red commit.
    failed = failed_checks(repo, pr['headRefOid'])
    if not comparison['behind_by'] and not failed:
        run(branch)
        return 'resumed'
    if not generated_by_bot(repo, pr['number']):
        raise ValueError('Refusing to replace a stale proposal not authored by the catalogue bot')
    pages = json.loads(publication.gh('api', '--paginate', '--slurp',
        f'repos/{repo}/pulls/{pr["number"]}/files?per_page=100'))
    paths = [item for page in pages for item in page]
    if not paths or any(not allowed_path(item['filename']) or
                       (item.get('previous_filename') and not allowed_path(item['previous_filename']))
                       for item in paths):
        raise ValueError('Stale PR contains changes outside the generated-artifact policy')
    current = json.loads(publication.gh('pr', 'view', branch, '--json', 'headRefOid'))
    if current['headRefOid'] != pr['headRefOid']:
        raise ValueError('Pending proposal changed during validation')
    if not failed or comparison['behind_by']:
        return 'carry'
    close_proposal(pr['number'], 'Falló la verificación (' + ', '.join(failed) + ') tras su reintento. Se conserva esta propuesta y su rama '
                   'como referencia; el escritor diario vuelve a consultar las fuentes y regenera los artefactos con el código actual. '
                   'No se fusionan páginas ni índices obsoletos.')
    return 'regenerate'


# bot_identity (refresh-reading-catalogue.py) firma cada commit de la carga con esta identidad, sea cual sea el
# token que abra la PR. Es la seña invariante de que la propuesta es trabajo generado, no humano.
BOT_COMMIT_EMAIL = '41898282+github-actions[bot]@users.noreply.github.com'


def generated_by_bot(repo, number):
    """True si ningún commit de la PR introduce trabajo humano.

    El autor de la PR (quien ejecutó `gh pr create`) depende del token: en la CI nocturna es github-actions,
    pero una publicación lanzada en local con credencial de usuario abre la MISMA propuesta generada bajo otro
    login, y comprobar ese login dejaba la carga encallada cada noche (run 42945302882). Lo que no cambia es el
    autor de los commits de contenido, fijado por bot_identity; un PR con algún commit humano no es trabajo
    generado.

    El único commit de la propuesta que no firma la carga es el merge que GitHub crea al actualizar la rama con
    main: cuando la PR queda BEHIND, `run()` llama a update-branch y GitHub añade un «Merge branch 'main'…»
    firmado por su propia cuenta, no por bot_identity. Ese merge es maquinaria del reintento, no trabajo humano;
    exigir que TODOS los commits fueran del bot dejaba la carga encallada en cuanto se había actualizado la rama
    (run 42958539544). Por eso solo los commits que aportan cambios propios (sin segundo padre) han de llevar la
    identidad de la carga; un merge de GitHub no cuenta. La política de artefactos (allowed_path sobre los
    ficheros de la PR, en resume_pending) sigue siendo la red que impide colar ficheros no generados.
    """
    pages = json.loads(publication.gh('api', '--paginate', '--slurp',
        f'repos/{repo}/pulls/{number}/commits?per_page=100'))
    commits = [item for page in pages for item in page]
    return bool(commits) and all(len(c['parents']) > 1 or c['commit']['author']['email'] == BOT_COMMIT_EMAIL
                                 for c in commits)


def close_proposal(number, comment):
    """Close a bot proposal, keeping its branch: it is the evidence and the source of a later carry."""
    publication.gh('pr', 'close', str(number), '--comment', comment)
    print(f'Closed stale bot proposal #{number}', flush=True)


UNRELATED_WORKFLOWS = ('pro-resources-qa.yml', 'convocatorias-browser-qa.yml')


def failed_checks(repo, sha):
    """Required jobs the publisher already reported as failed on this exact commit."""
    status = json.loads(publication.gh('api', f'repos/{repo}/commits/{sha}/status'))
    return sorted({s['context'] for s in status.get('statuses', []) if s['state'] in ('failure', 'error')})


def run(branch, timeout=5400):
    if not re.fullmatch(r'automation/reading-catalogue-[a-zA-Z0-9-]+', branch):
        raise ValueError('Only generated reading-catalogue branches are accepted')
    pr = json.loads(publication.gh('pr', 'view', branch, '--json', 'number,headRefOid,mergeStateStatus,mergeable'))
    if pr.get('mergeable') == 'CONFLICTING' or pr.get('mergeStateStatus') == 'DIRTY':
        raise publication.StaleMerge(f'main adelantó la propuesta #{pr["number"]}; reconstruir antes de iniciar CI')
    if pr.get('mergeStateStatus') == 'BEHIND':
        repo = publication.gh('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner')
        publication.gh('api', '--method', 'PUT', f'repos/{repo}/pulls/{pr["number"]}/update-branch',
                       '-f', f'expected_head_sha={pr["headRefOid"]}')
    # Las fichas no tocan recursos profesionales ni convocatorias: esos navegadores solo alargaban la cola.
    workflows = tuple(dict.fromkeys((*(w for w in publication.WORKFLOWS if w not in UNRELATED_WORKFLOWS),
                                    'reading-intake-qa.yml', 'recommendations-browser-qa.yml', 'reading-pinterest-rss-qa.yml')))
    try:
        publication.publish_generated(branch, allowed_path, workflows, timeout=timeout, deploy_before=True)
    except publication.StaleMerge:
        raise
    except RuntimeError as exc:
        # Leave the failure on the commit so the next batch regenerates instead of retesting it.
        repo = publication.gh('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner')
        publication.report_job(repo, pr['headRefOid'], 'reading-catalogue-publication', 'failure',
                               f'https://github.com/{repo}/pull/{pr["number"]}')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branch', required=True)
    args = parser.parse_args()
    run(args.branch)
