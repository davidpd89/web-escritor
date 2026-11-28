#!/usr/bin/env python3
"""Gestión de los almacenes de portadas (repositorios de Pages aparte, 1 GB cada uno).

  cupo KB                 estado del almacén activo según su tamaño en KB (lo usa la carga): ok, aviso o lleno
  migrar DIR URL          copia las portadas locales al almacén clonado en DIR, las registra y las sube
  verificar [--borrar]    comprueba que cada portada migrada responde en Pages y, con --borrar, quita la copia local
  nuevo N                 crea el almacén web-escritor-portadas-N con Pages, deploy key, secreto y variable
  auto                    abre el siguiente si el activo pasa de 700 MB (tarea diaria: install-covers-store-task.ps1)

Ninguna portada cambia de almacén: cuando el activo se llena se abre otro y las siguientes van allí
(ver el bloque de varios almacenes en reading_cover_store.py).
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reading_cover_store as store  # noqa: E402

AVISO_KB = 800 * 1024   # quedan ~100 MB (~4.000 portadas a ~24 KB): tiempo de abrir otro
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


def migrar(root: Path, directory: Path, url: str) -> int:
    """Copia y registra en el almacén clonado en `directory`, cuya URL de Pages es `url`; no borra nada (eso lo hace
    verificar cuando Pages ya las sirve). La URL es obligatoria: sin ella las altas apuntarían al primer almacén
    aunque los ficheros se subieran a otro (404 en la web)."""
    if not store._https(url.rstrip('/')):
        raise ValueError(f'migrar necesita la URL https del almacén de destino, no {url!r}')
    os.environ[store.STORE_DIR_ENV] = str(directory)
    os.environ[store.STORE_URL_ENV] = url.rstrip('/')
    moved, kept = 0, []
    for path in pendientes(root):
        content = path.read_bytes()
        target = directory / path.name
        if target.is_file() and target.read_bytes() != content:
            # El almacén no cambia bytes de un nombre: esta portada se sigue sirviendo desde el repo (no aborta).
            kept.append(path.name)
            continue
        shutil.copyfile(path, target)
        store.register(root, path.name, store.digest(content))
        moved += 1
    # Siempre: si un flush anterior falló tras registrar, repetir migrar sin pendientes debe volver a subir.
    store.flush(f'Migración de {moved} portadas desde web-escritor', root=root)
    if kept:
        print(f'{len(kept)} portadas se quedan en el repo (el almacén tiene otros bytes con ese nombre): {", ".join(kept[:5])}')
    return moved


def _get(url: str, sha: str) -> bool:
    """Pages sirve esos mismos bytes (un 200 con otro contenido no autoriza a borrar la copia local)."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'web-escritor-almacen'})
        with urllib.request.urlopen(req, timeout=30) as res:
            return res.status == 200 and store.digest(res.read()) == sha
    except Exception:
        return False


def _responde(url: str, sha: str, *, intentos: int = 3, get=_get, espera=time.sleep) -> bool:
    """Pages corta a veces miles de peticiones seguidas: un fallo suelto no es una portada ausente."""
    for i in range(intentos):
        if get(url, sha):
            return True
        if i + 1 < intentos:
            espera(2 * (i + 1))
    return False


def verificar(root: Path, *, borrar: bool = False, probe=_responde, workers: int = 16) -> tuple[int, list[str]]:
    """Devuelve (borradas, fallidas). Solo se borra la copia local cuyo almacén ya sirve los bytes registrados y que
    sigue siendo esos mismos bytes."""
    data = store.load(root)
    folder = root / LOCAL
    local = [n for n in data['archivos'] if (folder / n).is_file()]
    with ThreadPoolExecutor(workers) as pool:
        ok = list(pool.map(lambda n: probe(f'{store.url_of(data, n)}/{n}', data['sha256'][n]), local))
    failed = [n for n, good in zip(local, ok) if not good]
    removed = 0
    if borrar:
        for name, good in zip(local, ok):
            if good and store.digest((folder / name).read_bytes()) == data['sha256'][name]:
                (folder / name).unlink()
                removed += 1
    return removed, failed


def _existe(run, *args) -> bool:
    """La consulta de gh responde (no lanza): sirve para saltar los pasos de `nuevo` que ya se hicieron."""
    try:
        return run(['gh', *args], check=True, text=True, capture_output=True).returncode == 0
    except (subprocess.CalledProcessError, OSError):
        return False


def nuevo(n: int, *, repo: str = f'{OWNER}/web-escritor', run=subprocess.run) -> str:
    """Abre el almacén N y deja la carga apuntando a él (requiere gh con permisos de administrador).

    Se puede repetir: un intento cortado a medias (sin red, sin Pages todavía) se completa en el siguiente sin
    crear dos veces el repo ni el sitio. La clave de despliegue sí se renueva siempre: la privada solo vive en el
    secreto, así que no hay otra forma de saber que la que hay corresponde a este almacén."""
    name = f'web-escritor-portadas-{n}'
    full = f'{OWNER}/{name}'
    gh = lambda *a, **k: run(['gh', *a], check=True, text=True, **k)
    if not _existe(run, 'repo', 'view', full, '--json', 'name'):
        gh('repo', 'create', full, '--public', '--description', 'Portadas del catálogo de lecturas (almacén de Pages)')
    with tempfile.TemporaryDirectory() as tmp:
        if not _existe(run, 'api', f'repos/{full}/commits/main', '-q', '.sha'):
            work = Path(tmp) / 'repo'
            work.mkdir()
            run(['git', 'init', '-q', '-b', 'main', str(work)], check=True)
            (work / '.nojekyll').write_text('', encoding='utf-8')
            (work / 'README.md').write_text(f'# {name}\n\nPortadas servidas por Pages para davidportodiaz.com.\n', encoding='utf-8')
            for args in (['add', '.'], ['-c', 'user.name=almacen', '-c', 'user.email=almacen@users.noreply.github.com', 'commit', '-qm', 'Almacén nuevo'],
                         ['push', '-q', f'https://github.com/{full}.git', 'main']):
                run(['git', '-C', str(work), *args], check=True)
        if not _existe(run, 'api', f'repos/{full}/pages', '-q', '.url'):
            gh('api', '--method', 'POST', f'repos/{full}/pages', '-f', 'source[branch]=main', '-f', 'source[path]=/')
        key = Path(tmp) / 'key'
        run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', f'{name}-deploy', '-f', str(key)], check=True)
        gh('repo', 'deploy-key', 'add', str(key) + '.pub', '--repo', full, '--allow-write', '--title', f'carga nocturna {time.strftime("%Y-%m-%d %H%M%S")}')
        gh('secret', 'set', 'COVERS_STORE_DEPLOY_KEY', '--repo', repo, input=key.read_text(encoding='utf-8'))
    gh('variable', 'set', 'READING_COVERS_STORE_REPO', '--repo', repo, '--body', name)
    return f'https://{OWNER}.github.io/{name}'


PREPARAR_KB = 700 * 1024  # `auto` abre el siguiente aquí: ~8 noches de margen antes del aviso de la carga


def numero(name: str) -> int:
    """web-escritor-portadas es el 1; web-escritor-portadas-N, el N."""
    tail = name.rsplit('-', 1)[-1]
    return int(tail) if name.startswith('web-escritor-portadas-') and tail.isdigit() else 1


def auto(*, repo: str = f'{OWNER}/web-escritor', run=subprocess.run, umbral: int = PREPARAR_KB) -> str:
    """Lo ejecuta una tarea diaria con el gh del dueño (una App no puede crear repos en una cuenta personal).
    Si el almacén activo pasa del umbral, abre el siguiente; si no, no toca nada. Devuelve qué hizo."""
    out = lambda *a: run(['gh', *a], check=True, text=True, capture_output=True).stdout.strip()
    try:
        active = out('variable', 'get', 'READING_COVERS_STORE_REPO', '--repo', repo) or 'web-escritor-portadas'
    except subprocess.CalledProcessError as exc:
        # Solo «no existe» significa el primero; cualquier otro fallo (red, 5xx, permisos) no puede abrir un almacén
        # a partir de uno viejo: se reintenta al día siguiente sin tocar la configuración.
        if not re.search(r'not found|404', f'{exc.stderr or ""}{exc.stdout or ""}', re.I):
            raise
        active = 'web-escritor-portadas'
    kb = out('api', f'repos/{OWNER}/{active}', '-q', '.size')
    if not kb.isdigit() or int(kb) < umbral:
        return f'{active}: {kb or "?"} KB, sin cambios'
    url = nuevo(numero(active) + 1, repo=repo, run=run)
    return f'{active}: {kb} KB, abierto {url}'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('cupo').add_argument('kb', nargs='?', default='')
    m = sub.add_parser('migrar')
    m.add_argument('dir', type=Path)
    m.add_argument('url', help='URL de Pages del almacén clonado en DIR')
    sub.add_parser('verificar').add_argument('--borrar', action='store_true')
    sub.add_parser('nuevo').add_argument('n', type=int)
    sub.add_parser('auto')
    args = parser.parse_args(argv)
    if args.cmd == 'cupo':
        print(cupo(int(args.kb) if str(args.kb).strip().isdigit() else None))
    elif args.cmd == 'migrar':
        print(f'migradas: {migrar(store.ROOT, args.dir, args.url)}')
    elif args.cmd == 'verificar':
        removed, failed = verificar(store.ROOT, borrar=args.borrar)
        print(f'borradas: {removed}; sin responder: {len(failed)}')
        for name in failed[:20]:
            print(f'  {name}')
        return 1 if failed else 0
    elif args.cmd == 'auto':
        print(time.strftime('%Y-%m-%d %H:%M'), auto())
    else:
        print(nuevo(args.n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
