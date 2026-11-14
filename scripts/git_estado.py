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


def para_anadir(cwd, *pathspec, untracked='all'):
    """De `rutas`, solo las que todavía necesitan `git add`.

    Un borrado ya completo en el índice (`git rm --cached`, o `git add -A` sobre un fichero que ya no existe)
    sigue saliendo en `git status` — el árbol de trabajo coincide con el índice, así que su columna Y es ' ' — pero
    no existe ni en el árbol ni en el índice: volver a pedirle `git add` a ese camino falla con «pathspec … did not
    match any files» (14/11, página de autor retirada por `drop_retired_pages`). Lo que sí necesita `add` siempre
    tiene la columna Y distinta de ' ' (sin seguir, modificado sin indexar, o borrado sin indexar)."""
    return [path for estado, path in entradas(cwd, *pathspec, untracked=untracked) if estado[1] != ' ']
