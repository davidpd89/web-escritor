"""Rebasa la rama actual sobre main y regenera lo generado, sin resolver conflictos de HTML a mano.

El HTML del catálogo, Pagefind, el sitemap y el orden de páginas se versionan en git y salen de los builders. Dos ramas
que reconstruyen el catálogo chocan siempre en esos ficheros, aunque el código no choque. Este script:

1. rebasa sobre `--onto` (origin/main por defecto);
2. en cada conflicto, si TODOS los ficheros en conflicto son generados, toma la versión de main y sigue; si alguno es
   código o datos de verdad, aborta el rebase y lo dice (eso sí necesita una persona);
3. al terminar, ejecuta los builders en el mismo orden que la carga nocturna y hace un commit «Regenerar artefactos»
   si cambió algo;
4. comprueba con los `--check` de los builders y `check-asset-versions.py`.

Con `--rederivar-catalogo` el catálogo (`data/reading-catalogue.json`) también se trata como derivado: la rama declara
que su cambio en él es solo lo que produce el código de clasificación (`reading_taxonomy.repair_classification`, que la
carga nocturna aplica cada noche). Un conflicto en él toma la versión de main y, tras el rebase, se vuelve a derivar
sobre ella. Sin la opción, un conflicto en el catálogo sigue siendo real y aborta.

Uso: python scripts/rebase-regenerando.py [--onto origin/main] [--sin-fetch] [--rederivar-catalogo]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = 'data/reading-catalogue.json'

sys.path.insert(0, str(ROOT / 'scripts'))
import git_estado  # noqa: E402
import materializar_generados as materializar  # noqa: E402

generado = materializar.generado


def clasificar(estado) -> tuple[list[str], list[str]]:
    """Separa las entradas (XY, ruta) de `git_estado.entradas` en (a versionar, sueltos).

    Un fichero nuevo solo entra si es generado: informes sueltos (reports/…) que deja un builder no se versionan.
    """
    cambios = [p for xy, p in estado if xy != '??' or generado(p)]
    sueltos = [p for xy, p in estado if xy == '??' and not generado(p)]
    return cambios, sueltos


def git(*args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(['git', *args], cwd=ROOT, text=True, capture_output=True, check=check, encoding='utf-8')


def git_paths(args, paths):
    """Rutas por stdin: admite borrados y evita el límite de argv de Windows."""
    return subprocess.run(['git', *args, '--pathspec-from-file=-', '--pathspec-file-nul'],
                          cwd=ROOT, input=('\0'.join(paths) + '\0').encode('utf-8'),
                          capture_output=True, check=True)


def en_conflicto() -> list[str]:
    return [l for l in git('diff', '--name-only', '--diff-filter=U').stdout.splitlines() if l]


def rebase_en_curso() -> bool:
    gitdir = Path(git('rev-parse', '--git-dir').stdout.strip())
    gitdir = gitdir if gitdir.is_absolute() else ROOT / gitdir
    return (gitdir / 'rebase-merge').exists() or (gitdir / 'rebase-apply').exists()


def rebasar(onto: str, derivados: frozenset[str] = frozenset()) -> None:
    """`derivados`: ficheros de datos que esta rama declara derivados del código (se toman de main y se rederivan)."""
    r = git('rebase', onto, check=False)
    while r.returncode != 0:
        if not rebase_en_curso():
            sys.exit(f'El rebase falló sin conflicto:\n{r.stdout}{r.stderr}')
        conflictos = en_conflicto()
        reales = [p for p in conflictos if not generado(p) and p not in derivados]
        if reales or not conflictos:
            git('rebase', '--abort', check=False)
            sys.exit('Conflictos que no son generados (los resuelve una persona): ' + ', '.join(reales or ['?']))
        # En un rebase, «ours» es la base (main): lo generado se reconstruye al final desde las fuentes resultantes.
        presentes = set(git('ls-tree', '-r', '--name-only', '-z', 'HEAD').stdout.split('\0'))
        conservar = [p for p in conflictos if p in presentes]
        borrados = [p for p in conflictos if p not in presentes]
        if conservar:
            git_paths(['restore', '--source=HEAD', '--staged', '--worktree'], conservar)
        if borrados:
            git_paths(['rm', '-f', '--ignore-unmatch'], borrados)
        print(f'  {len(conflictos)} generado(s)/derivado(s) en conflicto: versión de main, se regeneran al final')
        r = subprocess.run(['git', '-c', 'core.editor=true', 'rebase', '--continue'], cwd=ROOT, text=True,
                           capture_output=True, encoding='utf-8')


def rederivar_catalogo(root: Path = ROOT) -> bool:
    """Vuelve a aplicar la clasificación (veredictos incluidos) al catálogo de la rama; True si cambió."""
    import json
    from datetime import date
    from reading_ratings_refresh import write_changed
    from reading_taxonomy import repair_classification
    path = root / CATALOGO
    data = json.loads(path.read_text(encoding='utf-8'))
    repair_classification(data, today=date.today().isoformat())
    return write_changed(path, data)


def regenerar() -> None:
    materializar.construir(ROOT)
    materializar.comprobar(ROOT)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--onto', default='origin/main')
    ap.add_argument('--sin-fetch', action='store_true')
    ap.add_argument('--rederivar-catalogo', action='store_true',
                    help='el cambio de la rama en el catálogo sale solo de repair_classification: se rederiva sobre main')
    a = ap.parse_args()
    if git('status', '--porcelain', '--untracked-files=no').stdout.strip():
        sys.exit('Hay cambios sin commit: confírmalos antes de rebasar.')
    if not a.sin_fetch:
        git('fetch', '-q', 'origin')
    print(f'Rebase sobre {a.onto}')
    rebasar(a.onto, frozenset({CATALOGO}) if a.rederivar_catalogo else frozenset())
    if a.rederivar_catalogo:
        print('Catálogo rederivado' if rederivar_catalogo() else 'Catálogo ya derivado')
    print('Regenerando artefactos')
    regenerar()
    cambios, sueltos = clasificar(git_estado.entradas(ROOT))
    fuera = [p for p in cambios if not generado(p) and not p.startswith(('data/', 'assets/'))]
    if fuera:
        print('Aviso: los builders tocaron ficheros fuera de lo generado: ' + ', '.join(fuera[:8]))
    if sueltos:
        print('Sin versionar (no son generados): ' + ', '.join(sueltos[:8]))
    if cambios:
        git_estado.preparar(ROOT, cambios)  # un borrado ya en el índice no tumba el commit (#1318)
        git('commit', '-q', '-m', f'Regenerar artefactos sobre {git("rev-parse", "--short", a.onto).stdout.strip()}')
        print(f'Commit de regeneración con {len(cambios)} fichero(s)')
    else:
        print('Nada que regenerar')
    return 0


if __name__ == '__main__':
    sys.exit(main())
