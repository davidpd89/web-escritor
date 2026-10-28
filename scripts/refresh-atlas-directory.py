#!/usr/bin/env python3
"""Un solo escritor para el directorio del Atlas: consulta Wikidata y publica un PR solo con artefactos generados."""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication', ROOT / 'scripts/publish-radar-refresh.py')
publication = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publication)

BRANCH_RE = re.compile(r'automation/atlas-directory-[a-zA-Z0-9-]+')


def allowed_path(path):
    """El directorio solo cambia la lista de datos, el hub y el índice de búsqueda."""
    return path in {'data/atlas/directory.json', 'atlas-literario/index.html'} or bool(
        re.fullmatch(r'pagefind/[A-Za-z0-9_./-]+', path)) and '..' not in path.split('/')


def command(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def refresh(*, publish=False):
    if publish and subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True).strip():
        raise ValueError('La publicación automática exige un checkout limpio')
    opened = json.loads(publication.gh('pr', 'list', '--state', 'open', '--base', 'main', '--limit', '100', '--json', 'headRefName'))
    pending = [p['headRefName'] for p in opened if BRANCH_RE.fullmatch(p['headRefName'])]
    for branch in pending:
        info = json.loads(publication.gh('pr', 'view', branch, '--json', 'number,mergeStateStatus,author'))
        stale = info.get('mergeStateStatus') in {'DIRTY', 'BEHIND'}
        by_bot = info['author'].get('is_bot') and info['author'].get('login') == 'app/github-actions'
        if not (stale and by_bot):
            print('Carga pendiente conservada: ' + branch)
            return
        publication.gh('pr', 'close', str(info['number']), '--comment',
                       'La rama quedó detrás de main: se cierra y se regenera desde main en esta ejecución.')
    command(sys.executable, 'scripts/atlas_wikidata_feed.py', '--apply')
    changed = subprocess.check_output(['git', 'status', '--porcelain', '--', 'data/atlas/directory.json'], cwd=ROOT, text=True).strip()
    if not changed:
        print('Sin cambios en el directorio del Atlas')
        return
    if not publish:
        print('Cambios detectados (modo prueba, no se publica)')
        return
    data = 'data/atlas/catalogue.json'
    command(sys.executable, 'scripts/build-atlas-pages.py', '--data', data, '--root', '.')
    command('git', 'add', '--', 'data/atlas/directory.json', 'atlas-literario')
    for script in ('build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        command(sys.executable, 'scripts/' + script)
    for check in (['scripts/build-atlas-pages.py', '--data', data, '--root', '.', '--check'],
                  ['scripts/check_atlas_release_contract.py', '--root', '.', '--manifest', 'data/atlas-routes-manifest.json'],
                  ['scripts/build-site-shell.py', '--check'], ['scripts/build-sitemap.py', '--check'],
                  ['scripts/build-pagefind-index.py', '--check']):
        command(sys.executable, *check)
    command(sys.executable, 'tests/test-atlas-pages.py')
    command(sys.executable, 'tests/test-atlas-wikidata-feed.py')
    command('git', 'diff', '--check')
    paths = [line[3:] for line in subprocess.check_output(
        ['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True).splitlines()]
    outside = [p for p in paths if not allowed_path(p)]
    if not paths or outside:
        raise ValueError('Cambios fuera de los artefactos permitidos: ' + str(outside))
    command('git', 'add', '--', *paths)
    day = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    branch = 'automation/atlas-directory-' + day + '-' + os.environ.get('GITHUB_RUN_ID', datetime.now().strftime('%H%M%S'))
    command('git', 'config', 'user.name', 'github-actions[bot]')
    command('git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    command('git', 'switch', '-c', branch)
    command('git', 'commit', '-m', 'Actualizar el directorio del Atlas ' + day)
    command('git', 'push', 'origin', 'HEAD:refs/heads/' + branch)
    body = ROOT / '.ci/atlas-directory-pr-body.md'
    body.parent.mkdir(parents=True, exist_ok=True)
    body.write_text('Actualiza el directorio del Atlas literario con lugares de Wikidata (datos CC0): librerías, bibliotecas, '
                    'museos y casas de escritores con web oficial HTTPS, coordenadas y notoriedad mínima.\n\n'
                    'No crea relaciones obra-lugar ni fichas editoriales. Se ejecutan las pruebas reales del commit y las reglas '
                    'de main antes de fusionar; después se despliega y se comprueba producción.\n', encoding='utf-8')
    publication.gh('pr', 'create', '--base', 'main', '--head', branch, '--title', 'Actualizar el directorio del Atlas ' + day,
                   '--body-file', str(body))
    publication.publish_generated(branch, allowed_path, publication.WORKFLOWS, deploy_before=True)


def main(publish):
    try:
        refresh(publish=publish)
    except publication.StaleMerge as exc:
        print(exc, flush=True)
        sys.exit(publication.STALE_EXIT_CODE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    main(args.publish)
