#!/usr/bin/env python3
"""Publish generated book updates through real CI, protected main and Pages."""
import argparse
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication', ROOT / 'scripts/publish-radar-refresh.py')
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)

EXACT = {'assets/page-order.generated.js', 'assets/reading-market.json', 'data/reading-catalogue.json', 'data/reading-authors.json', 'data/reading-publishers.json', 'data/reading-intake-state.json', 'data/reading-pinterest-state.json',
         'data/content-registry.json', 'recomendaciones/index.html', 'recomendaciones/autores/index.html',
         'recomendaciones/editoriales/index.html', 'recomendaciones/proximos-lanzamientos.ics', 'mapa-del-sitio/index.html',
         'sitemap.xml', 'editoriales-sitemap.xml'}


def allowed_path(path):
    return path in EXACT or bool(re.fullmatch(
        r'(?:recomendaciones/(?:libros|autores|editoriales)/[a-z0-9-]+/index\.html|'
        r'editoriales/[a-z0-9-]+/index\.html|'
        r'assets/reading-covers/isbn-97[89][0-9]{10}(?:-320)?\.webp|'
        r'assets/reading-audio/[a-z0-9-]+-[a-f0-9]{12}\.mp3|'
        r'assets/pinterest/feeds/[a-z0-9-]+\.xml|'
        r'pagefind/[A-Za-z0-9_./-]+)', path)) and '..' not in path.split('/')


def resume_pending(branch):
    """Resume current generated work; regenerate stale bot work from main.

    Old HTML/indices may conflict with a newer renderer or lack new workflows.
    Keep the old PR and branch for inspection instead of merging stale output.
    Never close a human PR or a proposal containing non-generated changes.
    """
    if not re.fullmatch(r'automation/reading-catalogue-[a-zA-Z0-9-]+', branch):
        raise ValueError('Only generated reading-catalogue branches are accepted')
    repo = publication.gh('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner')
    pr = json.loads(publication.gh('pr', 'view', branch, '--json',
                                  'number,headRefOid,baseRefName,state,author'))
    if pr['state'] != 'OPEN' or pr['baseRefName'] != 'main':
        raise ValueError('Expected an open PR targeting main')
    comparison = json.loads(publication.gh('api',
        f'repos/{repo}/compare/main...{pr["headRefOid"]}'))
    if not comparison['behind_by']:
        run(branch)
        return True
    if not pr['author'].get('is_bot') or pr['author']['login'] != 'app/github-actions':
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
    publication.gh('pr', 'close', str(pr['number']), '--comment',
        'La rama quedó detrás de main. Se conserva esta propuesta y su rama como referencia; '
        'el escritor diario vuelve a consultar las fuentes y regenera los artefactos con el código actual. '
        'No se fusionan páginas ni índices obsoletos.')
    print(f'Regenerating stale bot proposal #{pr["number"]} from current main', flush=True)
    return False


def run(branch, timeout=5400):
    if not re.fullmatch(r'automation/reading-catalogue-[a-zA-Z0-9-]+', branch):
        raise ValueError('Only generated reading-catalogue branches are accepted')
    pr = json.loads(publication.gh('pr', 'view', branch, '--json', 'number,headRefOid,mergeStateStatus'))
    if pr.get('mergeStateStatus') == 'BEHIND':
        repo = publication.gh('repo', 'view', '--json', 'nameWithOwner', '--jq', '.nameWithOwner')
        publication.gh('api', '--method', 'PUT', f'repos/{repo}/pulls/{pr["number"]}/update-branch',
                       '-f', f'expected_head_sha={pr["headRefOid"]}')
    workflows = tuple(dict.fromkeys((*publication.WORKFLOWS,
                                    'reading-intake-qa.yml', 'recommendations-browser-qa.yml', 'reading-pinterest-rss-qa.yml')))
    publication.publish_generated(branch, allowed_path, workflows, timeout=timeout, deploy_before=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branch', required=True)
    args = parser.parse_args()
    run(args.branch)
