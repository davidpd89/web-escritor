"""Única fuente de la cadena de builders que materializa lo generado (fichas, editoriales, orden, shell, sitemap, Pagefind).

Antes cada llamador (carga, rebase-regenerando, merge-main) copiaba la lista y el orden; una copia olvidó registrar
las fichas nuevas antes de los builders que leen `git ls-files` (site-shell, Pagefind) y las dejaba fuera del índice.

    python scripts/materializar_generados.py            # construye y comprueba
    python scripts/materializar_generados.py --check    # solo comprueba que lo versionado está al día
    python scripts/materializar_generados.py --solo-construir   # CI (.github/actions/materializar): sin comprobar
    python scripts/materializar_generados.py --asegurar   # antes de una suite: construye solo si hace falta
"""
from __future__ import annotations

import fnmatch
import os
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
# Entradas de los builders: la misma lista que la clave de caché de .github/actions/materializar (lo comprueba un test).
FUENTES = ('data/**', 'scripts/build-*.py', 'scripts/site_shell.py', 'scripts/reading*.py', 'scripts/templates/**',
           'scripts/materializar_generados.py', '**/*.html.tmpl')
TESTIGO = 'assets/page-order.generated.js'   # si está versionado, lo generado sigue en git (antes del corte)
HUELLA = Path('.local') / 'materializado.huella'


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


def _git(root: Path, *args: str) -> str:
    return subprocess.run(['git', *args], cwd=root, capture_output=True, text=True, encoding='utf-8').stdout


def huella(root: Path = ROOT) -> str:
    """Hash de las fuentes versionadas (ruta + contenido). Lo generado no entra aunque viva en data/."""
    import hashlib
    h = hashlib.sha256()
    for path in sorted(p for p in _git(root, 'ls-files', '-z', '--', *(':(glob)' + f for f in FUENTES)).split('\0')
                       if p and not generado(p)):
        h.update(path.encode() + b'\0' + (root / path).read_bytes() + b'\0')
    return h.hexdigest()


def asegurar(root: Path = ROOT) -> bool:
    """Deja lo generado al día antes de una suite que lo lee; devuelve si construyó.

    Mientras lo generado esté versionado (antes del corte) no hace nada: el checkout ya lo trae. Tras el corte,
    construye solo si cambiaron las fuentes desde la última vez (huella en .local/), así los tests no tienen que
    construir cada uno en un directorio temporal: se materializa una vez, igual que en CI con la acción.
    """
    if _git(root, 'ls-files', '--', TESTIGO).strip():
        return False
    actual, marca = huella(root), root / HUELLA
    if (root / TESTIGO).exists() and marca.exists() and marca.read_text(encoding='utf-8') == actual:
        return False
    print('Materializando lo generado (cambiaron las fuentes)…', flush=True)
    construir(root)
    marca.parent.mkdir(parents=True, exist_ok=True)
    marca.write_text(actual, encoding='utf-8')
    return True


def comprobar(root: Path = ROOT, assets: bool = True) -> None:
    for script in CHECKS:
        _py(root, script, '--check')
    if assets:
        _py(root, 'check-asset-versions.py')


def main(argv: list[str]) -> int:
    if '--asegurar' in argv:
        construido = asegurar()
        salida = os.environ.get('GITHUB_OUTPUT')
        if salida:  # la acción materializar solo guarda caché si de verdad construyó
            with open(salida, 'a', encoding='utf-8') as f:
                f.write(f"construido={'true' if construido else 'false'}" + chr(10))
        return 0
    if '--check' not in argv:
        construir()
    if '--solo-construir' not in argv:
        comprobar()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
