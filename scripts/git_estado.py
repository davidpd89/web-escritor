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
                         cwd=cwd, capture_output=True, check=True).stdout
    # surrogateescape: un nombre que no es UTF-8 no tumba la carga y vuelve intacto a `preparar` (#1312, CodeRabbit).
    out = out.decode('utf-8', 'surrogateescape')
    return [(item[:2], item[3:]) for item in out.split('\0') if item]


def rutas(cwd, *pathspec, untracked='all'):
    return [path for _, path in entradas(cwd, *pathspec, untracked=untracked)]


def preparar(cwd, paths, env=None):
    """`git add -A` de `paths` sin fallar por una ruta cuyo borrado ya está en el índice.

    14/11 (#43579987645): `registrar` añade la carpeta `recomendaciones` entera (borrados incluidos) y luego
    `git add -- <ruta borrada>` daba «pathspec did not match any files»: ya no está ni en disco ni en el índice.
    Esas rutas ya están preparadas; se omiten. Todo publicador prepara rutas por aquí, nunca con `add -- *rutas`.
    Las rutas van por stdin (`--pathspec-from-file`), literales: miles de fichas no caben en la línea de órdenes
    de Windows (32 767 caracteres, WinError 206), y un `*` o `[` en un nombre no se expande como patrón.
    """
    import os
    from pathlib import Path
    paths = list(dict.fromkeys(paths))
    if not paths:
        return []
    out = subprocess.run(['git', 'ls-files', '-z', '--cached'], cwd=cwd, capture_output=True, check=True,
                         env=env).stdout.decode('utf-8', 'surrogateescape')
    known, dirs = set(), set()
    for tracked in filter(None, out.split('\0')):
        known.add(tracked)
        parts = tracked.split('/')
        dirs.update('/'.join(parts[:i]) for i in range(1, len(parts)))
    keep = [p for p in paths if (Path(cwd) / p).exists() or p.rstrip('/') in known or p.rstrip('/') in dirs]
    if keep:
        subprocess.run(['git', 'add', '-A', '--pathspec-from-file=-', '--pathspec-file-nul'], cwd=cwd, check=True,
                       input='\0'.join(keep).encode('utf-8', 'surrogateescape'),
                       env={**(env or os.environ), 'GIT_LITERAL_PATHSPECS': '1'})
    return keep
