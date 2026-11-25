#!/usr/bin/env python3
"""Gestión de los almacenes de portadas (repositorios de Pages aparte, 1 GB cada uno).

  cupo KB                 estado del almacén activo según su tamaño en KB (lo usa la carga): ok, aviso o lleno
  migrar DIR              copia las portadas locales al almacén clonado en DIR, las registra y las sube
  verificar [--borrar]    comprueba que cada portada migrada responde en Pages y, con --borrar, quita la copia local
  nuevo N                 crea el almacén web-escritor-portadas-N con Pages, deploy key, secreto y variable

Ninguna portada cambia de almacén: cuando el activo se llena se abre otro y las siguientes van allí
(ver el bloque de varios almacenes en reading_cover_store.py).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reading_cover_store as store  # noqa: E402

AVISO_KB = 800 * 1024   # quedan ~8 noches a 250 altas/noche: tiempo de abrir otro
LLENO_KB = 900 * 1024   # Pages publica hasta 1 GB por sitio; por encima no se escribe más ahí
LOCAL = 'assets/reading-covers'
OWNER = 'davidpd89'


def cupo(kb: int | None) -> str:
    """Tamaño desconocido = ok: no saber el tamaño no debe parar la carga (el freno real es el despliegue)."""
    if kb is None:
        return 'ok'
    return 'lleno' if kb >= LLENO_KB else 'aviso' if kb >= AVISO_KB else 'ok'


def pendientes(root: Path) -> list[Path]:
    """Portadas que aún viven en el repositorio y no están en el manifiesto."""
    folder = root / LOCAL
    known = store.names(root)
    return sorted(p for p in folder.iterdir() if p.is_file() and store.NAME.fullmatch(p.name) and p.name not in known) if folder.is_dir() else []


def migrar(root: Path, directory: Path) -> int:
    """Copia y registra en el almacén activo; no borra nada (eso lo hace verificar cuando Pages ya las sirve)."""
    os.environ[store.STORE_DIR_ENV] = str(directory)
    moved = 0
    for path in pendientes(root):
        content = path.read_bytes()
        target = directory / path.name
        if target.is_file() and target.read_bytes() != content:
            raise ValueError(f'{path.name}: el almacén ya tiene otro fichero con ese nombre')
        shutil.copyfile(path, target)
        store.register(root, path.name, store.digest(content))
        moved += 1
    if moved:
        store.flush(f'Migración de {moved} portadas desde web-escritor', root=root)
    return moved


def _responde(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'web-escritor-almacen'})
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status == 200
    except Exception:
        return False


def verificar(root: Path, *, borrar: bool = False, probe=_responde, workers: int = 16) -> tuple[int, list[str]]:
    """Devuelve (borradas, fallidas). Solo se borra la copia local cuyo almacén ya sirve esos mismos bytes registrados."""
    data = store.load(root)
    folder = root / LOCAL
    local = [n for n in data['archivos'] if (folder / n).is_file()]
    with ThreadPoolExecutor(workers) as pool:
        ok = list(pool.map(lambda n: probe(f'{store.url_of(data, n)}/{n}'), local))
    failed = [n for n, good in zip(local, ok) if not good]
    removed = 0
    if borrar:
        for name, good in zip(local, ok):
            if good and store.digest((folder / name).read_bytes()) == data['sha256'][name]:
                (folder / name).unlink()
                removed += 1
    return removed, failed


def nuevo(n: int, *, repo: str = f'{OWNER}/web-escritor', run=subprocess.run) -> str:
    """Abre el almacén N y deja la carga apuntando a él (requiere gh con permisos de administrador)."""
    name = f'web-escritor-portadas-{n}'
    full = f'{OWNER}/{name}'
    gh = lambda *a, **k: run(['gh', *a], check=True, text=True, **k)
    gh('repo', 'create', full, '--public', '--description', 'Portadas del catálogo de lecturas (almacén de Pages)')
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / 'repo'
        work.mkdir()
        run(['git', 'init', '-q', '-b', 'main', str(work)], check=True)
        (work / '.nojekyll').write_text('', encoding='utf-8')
        (work / 'README.md').write_text(f'# {name}\n\nPortadas servidas por Pages para davidportodiaz.com.\n', encoding='utf-8')
        for args in (['add', '.'], ['-c', 'user.name=almacen', '-c', 'user.email=almacen@users.noreply.github.com', 'commit', '-qm', 'Almacén nuevo'],
                     ['push', '-q', f'https://github.com/{full}.git', 'main']):
            run(['git', '-C', str(work), *args], check=True)
        key = Path(tmp) / 'key'
        run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', f'{name}-deploy', '-f', str(key)], check=True)
        gh('api', '--method', 'POST', f'repos/{full}/pages', '-f', 'source[branch]=main', '-f', 'source[path]=/')
        gh('repo', 'deploy-key', 'add', str(key) + '.pub', '--repo', full, '--allow-write', '--title', 'carga nocturna')
        gh('secret', 'set', 'COVERS_STORE_DEPLOY_KEY', '--repo', repo, input=key.read_text(encoding='utf-8'))
    gh('variable', 'set', 'READING_COVERS_STORE_REPO', '--repo', repo, '--body', name)
    return f'https://{OWNER}.github.io/{name}'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('cupo').add_argument('kb', nargs='?', default='')
    sub.add_parser('migrar').add_argument('dir', type=Path)
    sub.add_parser('verificar').add_argument('--borrar', action='store_true')
    sub.add_parser('nuevo').add_argument('n', type=int)
    args = parser.parse_args(argv)
    if args.cmd == 'cupo':
        print(cupo(int(args.kb) if str(args.kb).strip().isdigit() else None))
    elif args.cmd == 'migrar':
        print(f'migradas: {migrar(store.ROOT, args.dir)}')
    elif args.cmd == 'verificar':
        removed, failed = verificar(store.ROOT, borrar=args.borrar)
        print(f'borradas: {removed}; sin responder: {len(failed)}')
        for name in failed[:20]:
            print(f'  {name}')
        return 1 if failed else 0
    else:
        print(nuevo(args.n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
