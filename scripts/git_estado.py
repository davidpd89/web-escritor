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
    # lexists: un enlace simbólico colgante existe para git aunque su destino no (Codex, #1315).
    keep = [p for p in paths if os.path.lexists(Path(cwd) / p) or p.rstrip('/') in known or p.rstrip('/') in dirs]
    if keep:
        subprocess.run(['git', 'add', '-A', '--pathspec-from-file=-', '--pathspec-file-nul'], cwd=cwd, check=True,
                       input='\0'.join(keep).encode('utf-8', 'surrogateescape'),
                       env={**(env or os.environ), 'GIT_LITERAL_PATHSPECS': '1'})
    return keep


def foto(cwd, *pathspec):
    """{ruta: bytes, o None si está borrada} de lo cambiado frente a HEAD: el punto al que vuelve `restaurar`."""
    from pathlib import Path
    salida = {}
    for path in rutas(cwd, *pathspec):
        f = Path(cwd) / path
        salida[path] = f.read_bytes() if f.is_file() else None
    return salida


def restaurar(cwd, antes, *pathspec):
    """Deshace lo escrito desde `foto(cwd, *pathspec)` sin tocar lo que ya había: un paso que falla a medias
    (precios, portadas) no se lleva por delante lo que dejó el paso anterior (las altas de la noche)."""
    import os
    from pathlib import Path
    ahora = rutas(cwd, *pathspec)
    volver = [p for p in ahora if p not in antes]
    if volver:
        arbol = subprocess.run(['git', 'ls-tree', '-r', '-z', '--name-only', 'HEAD'], cwd=cwd, capture_output=True,
                               check=True).stdout.decode('utf-8', 'surrogateescape')
        en_head = set(filter(None, arbol.split('\0')))
        for path in (p for p in volver if p not in en_head):
            (Path(cwd) / path).unlink(missing_ok=True)
        desde_head = [p for p in volver if p in en_head]
        if desde_head:
            subprocess.run(['git', 'checkout', 'HEAD', '--pathspec-from-file=-', '--pathspec-file-nul'], cwd=cwd,
                           check=True, input='\0'.join(desde_head).encode('utf-8', 'surrogateescape'),
                           env={**os.environ, 'GIT_LITERAL_PATHSPECS': '1'})
    for path, contenido in antes.items():
        f = Path(cwd) / path
        if contenido is None:
            f.unlink(missing_ok=True)
        elif not f.is_file() or f.read_bytes() != contenido:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(contenido)
