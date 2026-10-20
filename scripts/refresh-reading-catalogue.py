#!/usr/bin/env python3
"""Single writer for free, bounded publisher intake and generated-only PRs."""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from reading_intake_pipeline import ingest
from reading_intake_fetch import read_json, write_if_changed

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_publication', ROOT / 'scripts/publish-reading-refresh.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


def command(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def refresh(*, publish=False):
    config = read_json(ROOT / 'data/reading-intake-config.json')
    if publish and subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True).strip():
        raise ValueError('La publicación automática exige un checkout limpio')
    if publish and not config.get('autopublish'):
        raise ValueError('Autopublicación desactivada en la configuración')
    # A failed previous batch stays inspectable; never pile up duplicate writers.
    opened = json.loads(publisher.publication.gh('pr', 'list', '--state', 'open', '--base', 'main', '--limit', '100', '--json', 'headRefName'))
    pending = [p['headRefName'] for p in opened if p['headRefName'].startswith('automation/reading-catalogue-')]
    if pending:
        if len(pending) != 1:
            raise ValueError('Hay varias cargas pendientes; revisar antes de continuar')
        if publish:
            publisher.run(pending[0])
        print('Carga pendiente conservada: ' + pending[0])
        return
    report = ingest(config, ROOT, ROOT / '.ci/reading-editorial-cache', apply=publish)
    write_if_changed(ROOT / '.ci/reading-intake/publisher-report.json', report)
    print(json.dumps(report['stats'], ensure_ascii=True), flush=True)
    if not publish or not (report['new_books'] or report['updated_books']):
        return
    # Register new routes before builders that deliberately consume git ls-files.
    command(sys.executable, 'scripts/build-reading-catalogue.py')
    command(sys.executable, 'scripts/build-editoriales.py', '--data', 'data/editoriales.json', '--output', '.')
    command('git', 'add', '--', 'data/reading-catalogue.json', 'data/reading-authors.json', 'data/reading-intake-state.json',
            'data/content-registry.json', 'assets/reading-covers', 'assets/reading-audio', 'recomendaciones', 'editoriales', 'editoriales-sitemap.xml', 'mapa-del-sitio/index.html')
    for script in ('build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        command(sys.executable, 'scripts/' + script)
    for script in ('build-reading-catalogue.py', 'build-site-shell.py', 'build-sitemap.py', 'build-pagefind-index.py'):
        command(sys.executable, 'scripts/' + script, '--check')
    command(sys.executable, 'tests/test-reading-catalogue.py')
    command(sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_reading*.py', '-q')
    command('git', 'diff', '--check')
    changed = subprocess.check_output(
        ['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True)
    paths = [line[3:] for line in changed.splitlines()]
    if not paths or any(not publisher.allowed_path(p) for p in paths):
        raise ValueError('Cambios fuera de los artefactos permitidos: ' + str([p for p in paths if not publisher.allowed_path(p)]))
    command('git', 'add', '--', *paths)
    day = datetime.now(ZoneInfo('Europe/Madrid')).date().isoformat()
    branch = 'automation/reading-catalogue-' + day + '-' + os.environ.get('GITHUB_RUN_ID', datetime.now().strftime('%H%M%S'))
    command('git', 'config', 'user.name', 'github-actions[bot]')
    command('git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    command('git', 'switch', '-c', branch)
    command('git', 'commit', '-m', 'Actualizar catálogo de lectura ' + day)
    command('git', 'push', 'origin', 'HEAD:refs/heads/' + branch)
    body = ROOT / '.ci/reading-intake/pr-body.md'
    body.write_text('Incorpora ' + str(len(report['new_books'])) + ' ediciones verificadas en sus fichas editoriales oficiales.\n\n'
                    'Carga sin LLM ni API de pago; portadas optimizadas, ISBN comprobados, autores y enlaces internos generados. '
                    'No importa precios ni valoraciones sin un proveedor autorizado. Los candidatos incompletos quedan pendientes.\n\n'
                    'Se ejecutan las pruebas reales del commit y las reglas de main antes de fusionar. Después se despliega y se comprueba producción.\n', encoding='utf-8')
    publisher.publication.gh('pr', 'create', '--base', 'main', '--head', branch,
                             '--title', 'Actualizar catálogo de lectura ' + day, '--body-file', str(body))
    publisher.run(branch)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    refresh(publish=args.publish)
