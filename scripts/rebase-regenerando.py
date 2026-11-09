"""Rebasa la rama actual sobre main y regenera lo generado, sin resolver conflictos de HTML a mano.

El HTML del catálogo, Pagefind, el sitemap y el orden de páginas se versionan en git y salen de los builders. Dos ramas
que reconstruyen el catálogo chocan siempre en esos ficheros, aunque el código no choque. Este script:

1. rebasa sobre `--onto` (origin/main por defecto);
2. en cada conflicto, si TODOS los ficheros en conflicto son generados, toma la versión de main y sigue; si alguno es
   código o datos de verdad, aborta el rebase y lo dice (eso sí necesita una persona);
3. al terminar, ejecuta los builders en el mismo orden que la carga nocturna y hace un commit «Regenerar artefactos»
   si cambió algo;
4. comprueba con los `--check` de los builders y `check-asset-versions.py`.

Uso: python scripts/rebase-regenerando.py [--onto origin/main] [--sin-fetch]
"""
from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Salidas de los builders. Los datos (data/**, assets/reading-covers/**) NO están aquí: un conflicto en ellos es real.
GENERADOS = (
    'pagefind/*', 'recomendaciones/*.html', 'editoriales/*.html', 'editoriales-sitemap.xml', 'sitemap*.xml',
    'mapa-del-sitio/index.html', 'assets/page-order.generated.js',
)
BUILDERS = (
    ('build-reading-catalogue.py',),
    ('build-editoriales.py', '--data', 'data/editoriales.json', '--output', '.'),
    ('build-page-order.py',),
    ('build-site-shell.py',),
    ('build-sitemap.py',),
    ('build-pagefind-index.py',),
)
CHECKS = ('build-reading-catalogue.py', 'build-page-order.py', 'build-site-shell.py', 'build-sitemap.py',
          'build-pagefind-index.py')


def generado(path: str) -> bool:
    return any(fnmatch.fnmatch(path, patron) for patron in GENERADOS)


def git(*args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(['git', *args], cwd=ROOT, text=True, capture_output=True, check=check, encoding='utf-8')


def en_conflicto() -> list[str]:
    return [l for l in git('diff', '--name-only', '--diff-filter=U').stdout.splitlines() if l]


def rebase_en_curso() -> bool:
    gitdir = Path(git('rev-parse', '--git-dir').stdout.strip())
    gitdir = gitdir if gitdir.is_absolute() else ROOT / gitdir
    return (gitdir / 'rebase-merge').exists() or (gitdir / 'rebase-apply').exists()


def rebasar(onto: str) -> None:
    r = git('rebase', onto, check=False)
    while r.returncode != 0:
        if not rebase_en_curso():
            sys.exit(f'El rebase falló sin conflicto:\n{r.stdout}{r.stderr}')
        conflictos = en_conflicto()
        reales = [p for p in conflictos if not generado(p)]
        if reales or not conflictos:
            git('rebase', '--abort', check=False)
            sys.exit('Conflictos que no son generados (los resuelve una persona): ' + ', '.join(reales or ['?']))
        # En un rebase, «ours» es la base (main): lo generado se reconstruye al final desde las fuentes resultantes.
        git('checkout', '--ours', '--', *conflictos)
        git('add', '--', *conflictos)
        print(f'  {len(conflictos)} generado(s) en conflicto: versión de main, se regeneran al final')
        r = subprocess.run(['git', '-c', 'core.editor=true', 'rebase', '--continue'], cwd=ROOT, text=True,
                           capture_output=True, encoding='utf-8')


def regenerar() -> None:
    for builder in BUILDERS:
        print('  ' + ' '.join(builder))
        subprocess.run([sys.executable, 'scripts/' + builder[0], *builder[1:]], cwd=ROOT, check=True)
    for script in CHECKS:
        subprocess.run([sys.executable, 'scripts/' + script, '--check'], cwd=ROOT, check=True)
    subprocess.run([sys.executable, 'scripts/check-asset-versions.py'], cwd=ROOT, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--onto', default='origin/main')
    ap.add_argument('--sin-fetch', action='store_true')
    a = ap.parse_args()
    if git('status', '--porcelain', '--untracked-files=no').stdout.strip():
        sys.exit('Hay cambios sin commit: confírmalos antes de rebasar.')
    if not a.sin_fetch:
        git('fetch', '-q', 'origin')
    print(f'Rebase sobre {a.onto}')
    rebasar(a.onto)
    print('Regenerando artefactos')
    regenerar()
    estado = git('status', '--porcelain', '--untracked-files=all').stdout.splitlines()
    # Un fichero nuevo solo entra si es generado: informes sueltos (reports/…) que deja un builder no se versionan.
    cambios = [l[3:] for l in estado if not l.startswith('??') or generado(l[3:])]
    sueltos = [l[3:] for l in estado if l.startswith('??') and not generado(l[3:])]
    fuera = [p for p in cambios if not generado(p) and not p.startswith(('data/', 'assets/'))]
    if fuera:
        print('Aviso: los builders tocaron ficheros fuera de lo generado: ' + ', '.join(fuera[:8]))
    if sueltos:
        print('Sin versionar (no son generados): ' + ', '.join(sueltos[:8]))
    if cambios:
        git('add', '-A', '--', *cambios)
        git('commit', '-q', '-m', f'Regenerar artefactos sobre {git("rev-parse", "--short", a.onto).stdout.strip()}')
        print(f'Commit de regeneración con {len(cambios)} fichero(s)')
    else:
        print('Nada que regenerar')
    return 0


if __name__ == '__main__':
    sys.exit(main())
