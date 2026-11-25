"""Almacén externo de portadas: las portadas nuevas viven en otro repositorio con Pages, no en este.

Un único lugar sabe qué portadas están fuera (`data/reading-covers-store.json`) y cómo se llega a ellas:
- El resto del código sigue hablando de rutas lógicas `/assets/reading-covers/<nombre>`; así los datos, los
  contratos y las pruebas no cambian y un libro puede pasar de local a almacén sin tocar su ficha.
- El artefacto publicado se reescribe una sola vez (`apply_to_dist`): cada referencia a una portada del almacén
  pasa a su URL externa y la política CSP de las páginas admite ese host de imágenes.
- Quien necesita los bytes (refresco, Telegram, Pinterest) usa `read_bytes`/`exists`, que miran primero el disco
  y después el almacén.

Con el manifiesto vacío todo es un no-op: activar el almacén es dar de alta nombres en el manifiesto.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'data/reading-covers-store.json'
LOGICAL_PREFIX = '/assets/reading-covers/'
SITE = 'https://davidportodiaz.com'
NAME = re.compile(r'[a-z0-9][a-z0-9-]*\.(?:webp|jpg|jpeg|png)')
TEXT_SUFFIXES = {'.html', '.json', '.js', '.mjs', '.xml', '.txt', '.css', '.webmanifest', '.rss'}
DIGEST = re.compile(r'[0-9a-f]{64}')
IMG_SRC = re.compile(r"(img-src[^;\"]*?)(?=;|\"|$)")


_LEIDOS: dict = {}  # ruta del manifiesto -> (firma del fichero, manifiesto validado, nombres)


def _leer(root: Path = ROOT) -> tuple[dict, frozenset]:
    """Manifiesto validado y sus nombres, leído una vez por versión del fichero (ruta, mtime_ns, tamaño, inodo).

    La validación del catálogo lo consulta una vez por libro y la cuarentena repite la validación por cada libro que
    aparta: releerlo y recorrerlo cada vez hacía el coste cuadrático (42 s por validación con 7.900 libros, caso 11 de
    la revisión GPT, 25/11). Cualquier escritura cambia la firma y se vuelve a leer. Solo para consultas: quien vaya a
    cambiarlo usa load(), que devuelve una copia."""
    path = root / MANIFEST
    try:
        st = path.stat()
    except OSError:
        return {'base_url': '', 'archivos': [], 'sha256': {}}, frozenset()
    clave, firma = str(path), (st.st_mtime_ns, st.st_size, st.st_ino)
    hecho = _LEIDOS.get(clave)
    if hecho and hecho[0] == firma:
        return hecho[1], hecho[2]
    data = _validar(json.loads(path.read_text(encoding='utf-8')))
    _LEIDOS[clave] = (firma, data, frozenset(data['archivos']))
    return data, _LEIDOS[clave][2]


def load(root: Path = ROOT) -> dict:
    data = _leer(root)[0]
    return {'base_url': data['base_url'], 'archivos': list(data['archivos']), 'sha256': dict(data['sha256'])}


def _validar(data: dict) -> dict:
    base = str(data.get('base_url', '')).rstrip('/')
    names = data.get('archivos', [])
    digests = data.get('sha256', {})
    if names and not (urlparse(base).scheme == 'https' and urlparse(base).netloc):
        raise ValueError(f'{MANIFEST}: base_url debe ser una URL https si hay archivos')
    bad = [n for n in names if not isinstance(n, str) or not NAME.fullmatch(n)]
    if bad:
        raise ValueError(f'{MANIFEST}: nombres no válidos: {bad[:3]}')
    # Cada portada del almacén lleva la huella de sus bytes: sin ella la validación no podría comprobar duplicados
    # ni que el fichero publicado sea el que se validó al darlo de alta.
    if not isinstance(digests, dict) or any(not isinstance(digests.get(n), str) or not DIGEST.fullmatch(digests[n]) for n in names):
        raise ValueError(f'{MANIFEST}: cada archivo necesita su sha256')
    unique = sorted(set(names))
    return {'base_url': base, 'archivos': unique, 'sha256': {n: digests[n] for n in unique}}


def names(root: Path = ROOT) -> set[str]:
    return set(_leer(root)[1])


def _name(path: str) -> str | None:
    if isinstance(path, str) and path.startswith(LOGICAL_PREFIX) and '/' not in path[len(LOGICAL_PREFIX):]:
        return path[len(LOGICAL_PREFIX):]
    return None


def is_stored(path: str, root: Path = ROOT) -> bool:
    name = _name(path)
    return bool(name) and name in _leer(root)[1]


def public_url(path: str, root: Path = ROOT, *, site: str = '') -> str:
    """URL pública de una portada: la del almacén si está allí; si no, la ruta del sitio (con `site` delante)."""
    data, nombres = _leer(root)
    name = _name(path)
    if name and name in nombres:
        return f"{data['base_url']}/{name}"
    return site + path


def exists(path: str, root: Path = ROOT) -> bool:
    """La portada existe en disco o está dada de alta en el almacén."""
    return (root / path.lstrip('/')).is_file() or is_stored(path, root)


def read_bytes(path: str, root: Path = ROOT, *, get=None) -> bytes:
    """Bytes de una portada: del disco, o descargados del almacén con `get(url) -> bytes`."""
    local = root / path.lstrip('/')
    if local.is_file():
        return local.read_bytes()
    if not is_stored(path, root):
        raise FileNotFoundError(path)
    if get is None:
        import requests
        response = requests.get(public_url(path, root), timeout=30)
        response.raise_for_status()
        return response.content
    return get(public_url(path, root))


def rewrite_text(text: str, data: dict) -> str:
    """Sustituye en un texto cada referencia (ruta del sitio o URL completa) a una portada del almacén."""
    base, stored = data['base_url'], set(data['archivos'])
    if not stored:
        return text
    pattern = re.compile(r'(?:' + re.escape(SITE) + r')?' + re.escape(LOGICAL_PREFIX) + r'([a-z0-9][a-z0-9-]*\.(?:webp|jpg|jpeg|png))')
    return pattern.sub(lambda m: f'{base}/{m.group(1)}' if m.group(1) in stored else m.group(0), text)


def allow_img_host(text: str, data: dict) -> str:
    """Añade el host del almacén a las directivas img-src de las políticas CSP incrustadas."""
    host = urlparse(data['base_url']).scheme + '://' + urlparse(data['base_url']).netloc
    if not data['archivos'] or not host.startswith('https://'):
        return text

    def widen(match):
        directive = match.group(1)
        return directive if host in directive else directive + ' ' + host
    return IMG_SRC.sub(widen, text)


def apply_to_dist(out_dir: Path, root: Path = ROOT) -> int:
    """Reescribe el artefacto publicado. Devuelve cuántos ficheros cambió (0 con el almacén vacío)."""
    data = load(root)
    if not data['archivos']:
        return 0
    changed = 0
    base = out_dir.resolve()
    for path in out_dir.rglob('*'):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if not path.resolve().is_relative_to(base):
            continue
        try:
            original = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        text = rewrite_text(original, data)
        if path.suffix.lower() == '.html':
            text = allow_img_host(text, data)
        if text != original:
            path.write_text(text, encoding='utf-8', newline='')
            changed += 1
    return changed


# --- Escritura: la carga deja las portadas nuevas en una copia del repositorio del almacén y la sube con `flush`.
STORE_DIR_ENV = 'READING_COVERS_STORE_DIR'


def store_dir() -> Path | None:
    """Copia local del repositorio del almacén; sin ella (variable sin definir) todo se escribe en este repo."""
    value = os.environ.get(STORE_DIR_ENV, '').strip()
    return Path(value) if value else None


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def stored_digest(path: str, root: Path = ROOT) -> str | None:
    """Huella registrada de una portada del almacén (None si no está en el almacén)."""
    name = _name(path)
    return _leer(root)[0]['sha256'].get(name) if name else None


def owner_of_bytes(content: bytes, root: Path = ROOT, *, exclude: str = '') -> str | None:
    """Nombre de una portada principal del almacén con exactamente estos bytes (las -320 no cuentan)."""
    wanted, skip = digest(content), _name(exclude)
    for name, value in _leer(root)[0]['sha256'].items():
        if value == wanted and name != skip and not name.endswith('-320.webp'):
            return name
    return None


def local_file(path: str, root: Path = ROOT) -> Path | None:
    """Fichero con los bytes de una portada si están a mano: el del repo o el de la copia local del almacén."""
    local = root / path.lstrip('/')
    if local.is_file():
        return local
    directory, name = store_dir(), _name(path)
    if directory and name and is_stored(path, root) and (directory / name).is_file():
        return directory / name
    return None


def register(root: Path, name: str, sha256: str) -> None:
    path = root / MANIFEST
    data = load(root)
    if data['sha256'].get(name) == sha256:
        return
    data['archivos'] = sorted({*data['archivos'], name})
    data['sha256'][name] = sha256
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8', newline='')


def goes_to_store(root: Path, path: str) -> bool:
    """¿`put` escribiría esta ruta en el almacén? Sí con el almacén activo si la portada es nueva o ya está allí."""
    name = _name(path)
    return bool(store_dir() and name and (name in names(root) or not (root / path.lstrip('/')).exists()))


def put(root: Path, path: str, content: bytes) -> Path:
    """Guarda una portada. Con almacén activo, una portada nueva (sin fichero en este repo) va allí y se da de alta
    en el manifiesto con su huella; una portada local existente se sigue escribiendo en su sitio.

    El almacén es de solo añadir: un nombre ya dado de alta no cambia nunca de bytes (ValueError). Así deshacer un
    cambio del catálogo (reversión del mercado, cuarentena, recuperación) basta para volver a la imagen vieja, que
    sigue intacta; una portada sustituida recibe un nombre nuevo (`fresh_name`)."""
    target = root / path.lstrip('/')
    directory, name = store_dir(), _name(path)
    if directory and name and goes_to_store(root, path):
        value = digest(content)
        known = load(root)['sha256'].get(name)
        if known and known != value:
            raise ValueError(f'{name}: el almacén no sobrescribe portadas dadas de alta; usar un nombre nuevo')
        directory.mkdir(parents=True, exist_ok=True)
        (directory / name).write_bytes(content)
        register(root, name, value)
        return directory / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


VERSION = re.compile(r'-v[0-9a-f]{8}$')


def fresh_name(path: str, content: bytes) -> str:
    """Ruta nueva para sustituir una portada del almacén: el mismo nombre con la huella de los bytes nuevos."""
    stem, dot, ext = path.rpartition('.')
    return f'{VERSION.sub("", stem)}-v{digest(content)[:8]}{dot}{ext}'


def _store_git(directory: Path):
    def git(*args, check=True):
        return subprocess.run(['git', '-C', str(directory), *args], capture_output=True, text=True, check=check, encoding='utf-8')
    return git


def _commit_registered(git, directory: Path, root: Path, message: str) -> None:
    """Commit con las portadas del manifiesto que estén en la copia local (los huérfanos se quedan fuera)."""
    from git_estado import preparar  # rutas por stdin y literales: la regla de todos los publicadores
    preparar(directory, sorted(n for n in names(root) if (directory / n).is_file()))
    if git('diff', '--cached', '--quiet', check=False).returncode:
        git('-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com',
            'commit', '-q', '-m', message)


def _push_once(git) -> int | None:
    """Un intento de subida. Devuelve los ficheros publicados (0 si no había nada) o None si el push fue rechazado."""
    if git('ls-remote', '--exit-code', '--heads', 'origin', 'main', check=False).returncode == 2:
        # origin aún sin rama main (almacén nuevo): se publica tal cual
        pending = [line for line in git('ls-tree', '-r', '--name-only', 'HEAD').stdout.splitlines() if line.strip()]
    else:
        git('fetch', '--quiet', 'origin', 'main')
        if git('rev-list', '--count', 'origin/main..HEAD').stdout.strip() == '0':
            return 0
        if git('rebase', '--quiet', 'origin/main', check=False).returncode:
            git('rebase', '--abort', check=False)
            raise RuntimeError('Almacén de portadas: el rebase sobre origin/main choca; no se sube nada')
        pending = [line for line in git('diff', '--name-only', 'origin/main', 'HEAD').stdout.splitlines() if line.strip()]
    return None if git('push', '--quiet', 'origin', 'HEAD:main', check=False).returncode else len(pending)


def flush(message: str = 'Portadas de la carga', root: Path = ROOT) -> int:
    """Sube al almacén las portadas del manifiesto escritas con `put`. Devuelve cuántos ficheros publicó.

    Solo sube nombres dados de alta en el manifiesto actual: lo que una reversión quitó de él se queda fuera. Un
    commit de un intento anterior que no llegó a subirse se vuelve a intentar; si el rebase choca, se aborta y
    falla (nunca se da por subido lo que no está en origin)."""
    directory = store_dir()
    if not directory:
        return 0
    git = _store_git(directory)
    _commit_registered(git, directory, root, message)
    if git('rev-parse', '--verify', '--quiet', 'HEAD', check=False).returncode:
        _check_published(set(), root)  # almacén recién creado y sin nada que subir
        return 0
    for _ in range(3):
        published = _push_once(git)
        if published is not None:
            git('fetch', '--quiet', 'origin', 'main')
            _check_published(set(git('ls-tree', '-r', '--name-only', 'FETCH_HEAD').stdout.splitlines()), root)
            return published
    raise RuntimeError('Almacén de portadas: no se pudo subir tras 3 intentos')


def _check_published(remote: set[str], root: Path) -> None:
    """Caso 9 de la ronda 2 GPT (25/11): el manifiesto es lo que decide la URL pública, y `_commit_registered` deja
    fuera los nombres sin fichero en la copia local. Un nombre dado de alta que no está en origin sería una portada
    404 en la web: se para aquí, antes de que la rama de datos con ese manifiesto se suba."""
    missing = sorted(names(root) - remote)
    if missing:
        raise RuntimeError(f'Almacén de portadas: {len(missing)} portadas del manifiesto no están en origin '
                           f'(darían 404): {", ".join(missing[:10])}')


if __name__ == '__main__':
    import sys
    # `python3 scripts/reading_cover_store.py apply <dir>`: la misma reescritura que el despliegue, para las
    # comprobaciones que leen el checkout (enlaces): así verifican la URL real del almacén, no un fichero que no
    # está en el repo.
    if len(sys.argv) != 3 or sys.argv[1] != 'apply':
        raise SystemExit('uso: reading_cover_store.py apply <directorio>')
    print(f'Almacén de portadas: {apply_to_dist(Path(sys.argv[2]))} ficheros reescritos')
