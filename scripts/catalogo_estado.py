#!/usr/bin/env python3
"""Estado persistente de la ingesta Amazon (scripts/catalogo_amazon.py) entre ejecuciones de Actions.

Vive en la rama `catalogo-estado` (sin reglas, fuera de main): cola de semillas, pendientes, sellos
aprendidos, pendientes de creación, descartes y la última foto de revisión. Solo los ficheros pequeños;
los crudos del día se regeneran. Cada guardado es un commit nuevo encima del anterior (historial auditable,
nunca --force). La ingesta guarda el estado solo después de dejar los libros a salvo en una rama de datos,
de modo que un fallo intermedio nunca da por consumidas semillas cuyos libros no llegaron a ninguna parte.

  python scripts/catalogo_estado.py restaurar
  python scripts/catalogo_estado.py guardar --mensaje "..."
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.local/catalogo'
BRANCH = 'catalogo-estado'
FILES = ('semillas.json', 'pendientes.json', 'sellos.json', 'rendimiento-sellos.json',
         'pendientes-creacion.json', 'descartados.jsonl')


def git(*args, env=None, data=None, check=True):
    return subprocess.run(['git', *args], cwd=ROOT, check=check, capture_output=True, input=data,
                          env={**os.environ, **(env or {})})


def remote_head():
    out = git('ls-remote', '--heads', 'origin', BRANCH).stdout.decode().split()
    return out[0] if out else None


def restaurar():
    """Trae el último estado. Sin rama (primera vez) no hay nada que traer y la ingesta empieza de cero."""
    head = remote_head()
    if not head:
        print('Estado: sin rama ' + BRANCH + ', se empieza de cero', flush=True)
        return 0
    git('fetch', '--quiet', '--no-tags', 'origin', f'+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}')
    names = git('ls-tree', '-r', '--name-only', head).stdout.decode().splitlines()
    for name in names:
        target = WORK / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(git('show', f'{head}:{name}').stdout)
    print(f'Estado restaurado de {BRANCH}@{head[:12]}: {len(names)} ficheros', flush=True)
    return len(names)


def latest_photo():
    photos = sorted((WORK / 'revision').glob('foto-*.json'))
    return photos[-1:] if photos else []


def guardar(message):
    """Commit con los ficheros de estado encima del último de la rama; si otro lo movió entretanto, reintenta."""
    paths = [WORK / name for name in FILES if (WORK / name).exists()] + latest_photo()
    if not paths:
        print('Estado: nada que guardar', flush=True)
        return None
    for attempt in range(3):
        parent = remote_head()
        with tempfile.TemporaryDirectory() as tmp:
            env = {'GIT_INDEX_FILE': str(Path(tmp) / 'index')}
            for path in paths:
                blob = git('hash-object', '-w', '--', str(path)).stdout.decode().strip()
                name = path.relative_to(WORK).as_posix()
                git('update-index', '--add', '--cacheinfo', f'100644,{blob},{name}', env=env)
            tree = git('write-tree', env=env).stdout.decode().strip()
        if parent:
            git('fetch', '--quiet', '--no-tags', 'origin', f'+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}')
            if git('rev-parse', parent + '^{tree}').stdout.decode().strip() == tree:
                print('Estado sin cambios', flush=True)
                return parent
        identity = {'GIT_AUTHOR_NAME': 'github-actions[bot]', 'GIT_COMMITTER_NAME': 'github-actions[bot]',
                    'GIT_AUTHOR_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com',
                    'GIT_COMMITTER_EMAIL': '41898282+github-actions[bot]@users.noreply.github.com'}
        commit = git('commit-tree', tree, *(['-p', parent] if parent else []), '-m', message,
                     env=identity).stdout.decode().strip()
        if git('push', '--quiet', 'origin', f'{commit}:refs/heads/{BRANCH}', check=False).returncode == 0:
            print(f'Estado guardado en {BRANCH}@{commit[:12]}', flush=True)
            return commit
        print(f'Estado: la rama cambió durante el guardado (intento {attempt + 1})', flush=True)
    raise RuntimeError('No se pudo guardar el estado en ' + BRANCH)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('accion', choices=['restaurar', 'guardar'])
    parser.add_argument('--mensaje', default='Estado de la ingesta')
    args = parser.parse_args(argv)
    if args.accion == 'restaurar':
        restaurar()
    else:
        guardar(args.mensaje)
    return 0


if __name__ == '__main__':
    sys.exit(main())
