"""Única fuente de la cadena de builders que materializa lo generado (fichas, editoriales, orden, shell, sitemap, Pagefind).

Antes cada llamador (carga, rebase-regenerando, merge-main) copiaba la lista y el orden; una copia olvidó registrar
las fichas nuevas antes de los builders que leen `git ls-files` (site-shell, Pagefind) y las dejaba fuera del índice.

    python scripts/materializar_generados.py            # construye y comprueba
    python scripts/materializar_generados.py --check    # solo comprueba que lo versionado está al día
"""
from __future__ import annotations

import fnmatch
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Salidas de los builders. Los datos (data/**, assets/reading-covers/**) NO están aquí: un conflicto en ellos es real.
GENERADOS = (
    'pagefind/*', 'recomendaciones/*.html', 'editoriales/*.html', 'editoriales-sitemap.xml', 'sitemap*.xml',
    'mapa-del-sitio/index.html', 'assets/page-order.generated.js',
    'data/content-registry.json', 'editoriales/editoriales-data.json', 'recomendaciones/llms.txt',
    'recomendaciones/ofertas.json', 'recomendaciones/proximos-lanzamientos.ics',
)
# Hasta aquí se crean rutas nuevas; los siguientes leen `git ls-files` y necesitan verlas registradas.
CREAN_RUTAS = (
    ('build-reading-catalogue.py',),
    ('build-editoriales.py', '--data', 'data/editoriales.json', '--output', '.'),
    ('build-page-order.py',),
)
INDEXAN = (
    ('build-site-shell.py',),
    ('build-sitemap.py',),
    ('build-pagefind-index.py',),
)
BUILDERS = CREAN_RUTAS + INDEXAN
CHECKS = ('build-reading-catalogue.py', 'build-page-order.py', 'build-site-shell.py', 'build-sitemap.py',
          'build-pagefind-index.py')
RUTAS_NUEVAS = ('recomendaciones', 'editoriales', 'mapa-del-sitio')


def generado(path: str) -> bool:
    return any(fnmatch.fnmatch(path, patron) for patron in GENERADOS)


def _py(root: Path, script: str, *args: str) -> None:
    print('  ' + ' '.join((script, *args)), flush=True)
    subprocess.run([sys.executable, 'scripts/' + script, *args], cwd=root, check=True)


def registrar_rutas_nuevas(root: Path = ROOT) -> list[str]:
    """`git add -N` de las páginas nuevas: ls-files las ve sin meter su contenido en el índice."""
    nuevas = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard', '--', *RUTAS_NUEVAS],
                            cwd=root, capture_output=True, text=True, check=True, encoding='utf-8').stdout.split('\n')
    nuevas = [p for p in nuevas if p.endswith('.html')]
    if nuevas:
        subprocess.run(['git', 'add', '--intent-to-add', '--', *nuevas], cwd=root, check=True)
    return nuevas


def construir(root: Path = ROOT, antes_de_indexar=None) -> None:
    for script, *args in CREAN_RUTAS:
        _py(root, script, *args)
    (antes_de_indexar or registrar_rutas_nuevas)(root)
    for script, *args in INDEXAN:
        _py(root, script, *args)


def comprobar(root: Path = ROOT, assets: bool = True) -> None:
    for script in CHECKS:
        _py(root, script, '--check')
    if assets:
        _py(root, 'check-asset-versions.py')


def main(argv: list[str]) -> int:
    if '--check' not in argv:
        construir()
    comprobar()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
