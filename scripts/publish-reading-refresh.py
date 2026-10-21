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

EXACT = {'assets/reading-market.json', 'data/reading-catalogue.json', 'data/reading-authors.json', 'data/reading-intake-state.json', 'data/reading-pinterest-state.json',
         'data/content-registry.json', 'recomendaciones/index.html', 'mapa-del-sitio/index.html',
         'sitemap.xml', 'editoriales-sitemap.xml'}


def allowed_path(path):
    return path in EXACT or bool(re.fullmatch(
        r'(?:recomendaciones/(?:libros|autores)/[a-z0-9-]+/index\.html|'
        r'editoriales/[a-z0-9-]+/index\.html|'
        r'assets/reading-covers/isbn-97[89][0-9]{10}(?:-320)?\.webp|'
        r'assets/reading-audio/[a-z0-9-]+-[a-f0-9]{12}\.mp3|'
        r'assets/pinterest/feeds/[a-z0-9-]+\.xml|'
        r'pagefind/[A-Za-z0-9_./-]+)', path)) and '..' not in path.split('/')


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
