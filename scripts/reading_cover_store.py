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

import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'data/reading-covers-store.json'
LOGICAL_PREFIX = '/assets/reading-covers/'
SITE = 'https://davidportodiaz.com'
NAME = re.compile(r'[a-z0-9][a-z0-9-]*\.(?:webp|jpg|jpeg|png)')
TEXT_SUFFIXES = {'.html', '.json', '.js', '.mjs', '.xml', '.txt', '.css', '.webmanifest', '.rss'}
IMG_SRC = re.compile(r"(img-src[^;\"]*?)(?=;|\"|$)")


def load(root: Path = ROOT) -> dict:
    path = root / MANIFEST
    if not path.is_file():
        return {'base_url': '', 'archivos': []}
    data = json.loads(path.read_text(encoding='utf-8'))
    base = str(data.get('base_url', '')).rstrip('/')
    names = data.get('archivos', [])
    if names and not (urlparse(base).scheme == 'https' and urlparse(base).netloc):
        raise ValueError(f'{MANIFEST}: base_url debe ser una URL https si hay archivos')
    bad = [n for n in names if not isinstance(n, str) or not NAME.fullmatch(n)]
    if bad:
        raise ValueError(f'{MANIFEST}: nombres no válidos: {bad[:3]}')
    return {'base_url': base, 'archivos': sorted(set(names))}


def names(root: Path = ROOT) -> set[str]:
    return set(load(root)['archivos'])


def _name(path: str) -> str | None:
    if isinstance(path, str) and path.startswith(LOGICAL_PREFIX) and '/' not in path[len(LOGICAL_PREFIX):]:
        return path[len(LOGICAL_PREFIX):]
    return None


def is_stored(path: str, root: Path = ROOT) -> bool:
    name = _name(path)
    return bool(name) and name in names(root)


def public_url(path: str, root: Path = ROOT, *, site: str = '') -> str:
    """URL pública de una portada: la del almacén si está allí; si no, la ruta del sitio (con `site` delante)."""
    data = load(root)
    name = _name(path)
    if name and name in data['archivos']:
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
