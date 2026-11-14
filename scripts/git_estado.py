"""Rutas cambiadas del árbol de trabajo, leídas de forma robusta.

`git status --porcelain` sin más da «origen -> destino» cuando el índice tiene un renombrado (un libro retirado y
otro nuevo con HTML parecido) y entrecomilla rutas con espacios o tildes: cortar `línea[3:]` deja rutas que no
existen y tumba la publicación. Aquí: `-z` (sin comillas) y `--no-renames` (cada lado del renombrado por separado).
"""
import subprocess


def entradas(cwd, *pathspec, untracked='all'):
    """[(estado XY, ruta)] del árbol `cwd`; un renombrado aparece como borrado + alta."""
    out = subprocess.run(['git', 'status', '--porcelain=v1', '-z', '--no-renames', f'--untracked-files={untracked}',
                          *(['--', *pathspec] if pathspec else [])],
                         cwd=cwd, capture_output=True, check=True).stdout.decode('utf-8')
    return [(item[:2], item[3:]) for item in out.split('\0') if item]


def rutas(cwd, *pathspec, untracked='all'):
    return [path for _, path in entradas(cwd, *pathspec, untracked=untracked)]
