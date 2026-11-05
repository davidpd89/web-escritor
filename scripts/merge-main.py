#!/usr/bin/env python3
"""Fusiona origin/main en la rama y rehace los artefactos generados en vez de resolverlos a mano.

El bot fusiona fichas y pagefind varias veces al día, así que cualquier PR que también los toque queda en
conflicto. Aquí los conflictos en ficheros generados se resuelven con la versión de main y luego se regeneran
desde los datos ya fusionados; un conflicto en cualquier otro fichero aborta la fusión para revisarlo a mano.

  python scripts/merge-main.py           # fusiona, regenera, comprueba y deja el commit hecho
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = re.compile(r'^(pagefind/|recomendaciones/|editoriales/|editoriales-sitemap\.xml$|sitemap[^/]*\.xml$'
                       r'|mapa-del-sitio/|assets/page-order\.generated\.js$|data/content-registry\.json$)')
# Mismo orden que refresh-reading-catalogue.py: las fichas de editorial leen el catálogo y el sitemap y
# Pagefind leen las fichas; si falta uno, la PR sale con páginas desincronizadas.
BUILDERS = (('build-reading-catalogue.py',),
            ('build-editoriales.py', '--data', 'data/editoriales.json', '--output', '.'),
            ('build-page-order.py',), ('build-site-shell.py',), ('build-sitemap.py',), ('build-pagefind-index.py',))


def git(*args, check=True):
    return subprocess.run(['git', *args], cwd=ROOT, check=check, capture_output=True, text=True, encoding='utf-8')


def main():
    if git('status', '--porcelain', '--untracked-files=no').stdout.strip():
        raise SystemExit('Hay cambios sin commit; guárdalos antes de fusionar.')
    git('fetch', '-q', 'origin', 'main')
    if git('merge', '--no-edit', '--no-ff', 'origin/main', check=False).returncode:
        conflicts = git('diff', '--name-only', '--diff-filter=U').stdout.split()
        manual = [f for f in conflicts if not GENERATED.match(f)]
        if manual:
            git('merge', '--abort')
            raise SystemExit('Conflictos en ficheros no generados, resuélvelos a mano: ' + ', '.join(manual))
        for f in conflicts:
            # Borrado en main y cambiado aquí (fragmentos de pagefind): se va; el índice regenerado decide.
            if git('checkout', '--theirs', '--', f, check=False).returncode:
                git('rm', '-q', '--', f)
            else:
                git('add', '--', f)
        print(f'{len(conflicts)} conflictos en generados: versión de main, se regeneran.', flush=True)
    for script, *args in BUILDERS:
        subprocess.run([sys.executable, 'scripts/' + script, *args], cwd=ROOT, check=True)
    for script, *args in BUILDERS:
        subprocess.run([sys.executable, 'scripts/' + script, *args, '--check'], cwd=ROOT, check=True)
    git('add', '-A', '--', 'pagefind', 'recomendaciones', 'editoriales', 'editoriales-sitemap.xml', 'mapa-del-sitio',
        'assets/page-order.generated.js')
    git('add', '-u')
    staged = git('diff', '--cached', '--quiet', check=False).returncode
    if git('rev-parse', '-q', '--verify', 'MERGE_HEAD', check=False).returncode == 0:
        git('commit', '--no-edit')
    elif staged:
        git('commit', '-m', 'Regenera artefactos tras fusionar main')
    print(git('log', '--oneline', '-1').stdout.strip())


if __name__ == '__main__':
    main()
