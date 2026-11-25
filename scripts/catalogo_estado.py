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
FILES = ('semillas.json', 'pendientes.json', 'sellos.json', 'rendimiento-sellos.json', 'recorrido-sellos.json',
         'pendientes-creacion.json', 'descartados.jsonl', 'salud.json',
         'altas-por-dia.json')
# Escritos por otros procesos en la misma rama: guardar() los conserva tal como están en el remoto.
AJENOS = ('noche.json',)


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
    # Un fichero de estado que el remoto ya no tiene no puede sobrevivir en local de un intento anterior del mismo
    # runner (segundo ciclo tras el código 75; git clean no toca .local): guardar() lo resucitaría (R3-07 de GPT).
    for name in set(FILES) - set(names):
        (WORK / name).unlink(missing_ok=True)
    print(f'Estado restaurado de {BRANCH}@{head[:12]}: {len(names)} ficheros', flush=True)
    return len(names)


def leer(name):
    """Contenido de un fichero de la rama tal como está en el remoto ahora, o None si no existe."""
    head = remote_head()
    if not head:
        return None
    git('fetch', '--quiet', '--no-tags', 'origin', f'+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}')
    shown = git('show', f'{head}:{name}', check=False)
    return shown.stdout if shown.returncode == 0 else None


def _commit(entries, message, keep_parent, rehacer=None):
    """Commit encima de la cabeza de la rama con `entries` (nombre -> bytes). Con `keep_parent` se parte del árbol
    anterior y solo se sustituyen esos nombres; sin él, el árbol es exactamente `entries` más los ficheros AJENOS
    del anterior (los escribe otro proceso y no se pueden perder). Reintenta si otro movió la rama.

    `rehacer` (nombre -> función(bytes|None) -> bytes) recalcula ese fichero sobre su contenido en la cabeza de cada
    intento: sin él, un reintento volvía a subir bytes calculados sobre una lectura vieja y pisaba lo que el otro
    proceso acababa de escribir (caso 13 de la revisión GPT, 25/11: el segador y el abrir de la siguiente carga)."""
    rehacer = rehacer or {}
    for attempt in range(3):
        parent = remote_head()
        if parent:
            git('fetch', '--quiet', '--no-tags', 'origin', f'+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}')
        with tempfile.TemporaryDirectory() as tmp:
            env = {'GIT_INDEX_FILE': str(Path(tmp) / 'index')}
            if parent and keep_parent:
                git('read-tree', parent, env=env)
            elif parent:
                for name in AJENOS:
                    if name not in entries:
                        line = git('ls-tree', parent, '--', name).stdout.decode().split()
                        if line:
                            git('update-index', '--add', '--cacheinfo', f'100644,{line[2]},{name}', env=env)
            for name, cambio in rehacer.items():
                anterior = git('show', f'{parent}:{name}', check=False) if parent else None
                entries[name] = cambio(anterior.stdout if anterior is not None and anterior.returncode == 0 else None)
            for name, data in entries.items():
                blob = git('hash-object', '-w', '--stdin', data=data).stdout.decode().strip()
                git('update-index', '--add', '--cacheinfo', f'100644,{blob},{name}', env=env)
            tree = git('write-tree', env=env).stdout.decode().strip()
        if parent and git('rev-parse', parent + '^{tree}').stdout.decode().strip() == tree:
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


def escribir(name, data, message, rehacer=None):
    """Sustituye un solo fichero de la rama y conserva el resto (el libro de la noche, scripts/noche.py). Con
    `rehacer`, `data` se recalcula sobre el contenido remoto en cada intento (compare-and-swap)."""
    return _commit({name: data}, message, keep_parent=True, rehacer={name: rehacer} if rehacer else None)


def latest_photo():
    photos = sorted((WORK / 'revision').glob('foto-*.json'))
    return photos[-1:] if photos else []


def guardar(message):
    """Commit con los ficheros de estado encima del último de la rama; si otro lo movió entretanto, reintenta.
    Los ficheros AJENOS (el libro de la noche) se toman del remoto, nunca de la copia local restaurada."""
    paths = [WORK / name for name in FILES if (WORK / name).exists()] + latest_photo()
    if not paths:
        print('Estado: nada que guardar', flush=True)
        return None
    return _commit({path.relative_to(WORK).as_posix(): path.read_bytes() for path in paths}, message,
                   keep_parent=False)


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
