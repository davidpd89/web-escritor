#!/usr/bin/env python3
"""Servidor estático de QA: `python -m http.server` más las portadas del almacén.

Las portadas viven en el repo de portadas (data/reading-covers-store.json), no en el árbol. Un
servidor estático plano devuelve 404 para ellas y la QA de navegador mide páginas sin imágenes
(texto alternativo desbordado, CLS, etc.). Este servidor sirve el árbol igual que http.server y,
si una ruta /assets/reading-covers/<x> no está en disco pero sí en el almacén, entrega sus bytes
con el mismo origen (la CSP `img-src 'self'` de las páginas no se toca). Las descargas se guardan
en una caché temporal para no repetirlas.

Uso (mismos argumentos que http.server): qa_static_server.py [PUERTO] [--bind H] [--directory D]
"""
from __future__ import annotations

import argparse
import functools
import mimetypes
import re
import sys
import tempfile
import threading
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reading_cover_store as cover_store  # noqa: E402

CACHE = Path(tempfile.gettempdir()) / 'qa-covers-store-cache'
_lock = threading.Lock()
mimetypes.add_type('image/webp', '.webp')
# Solo nombres planos de imagen: nada de rutas, «..» ni otros tipos (el servidor nunca sirve HTML del almacén).
STORE_NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*\.(webp|jpg|jpeg|png|avif)')
IMAGE_TYPES = {'webp': 'image/webp', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'avif': 'image/avif'}


def _get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 (URL https del manifiesto)
        return response.read()


def store_bytes(path: str, served: Path, root: Path = cover_store.ROOT, *, get=_get) -> bytes | None:
    """Bytes de una portada del almacén que no está en `served`; None si no es del almacén.

    El manifiesto se lee del repo (`root`), no del directorio servido: un dist no lo lleva."""
    if not path.startswith(cover_store.LOGICAL_PREFIX):
        return None
    name = path[len(cover_store.LOGICAL_PREFIX):]
    if not STORE_NAME.fullmatch(name) or not cover_store.is_stored(path, root):
        return None
    if (served / 'assets/reading-covers' / name).is_file():
        return None
    cached = CACHE / name
    if cached.is_file():
        return cached.read_bytes()
    content = cover_store.read_bytes(path, root, get=get)
    with _lock:
        CACHE.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(content)
    return content


class Handler(SimpleHTTPRequestHandler):
    def _store(self) -> bytes | None:
        try:
            return store_bytes(unquote(urlsplit(self.path).path), Path(self.directory))
        except Exception as error:  # una portada que no baja es un 404, como antes
            self.log_message('almacén: %s (%s)', self.path, error)
            return None

    def _send_store(self, head: bool) -> bool:
        content = self._store()
        if content is None:
            return False
        self.send_response(200)
        # store_bytes solo admite nombres de imagen: el tipo sale de su extensión y el navegador no lo reinterpreta.
        self.send_header('Content-Type', IMAGE_TYPES[unquote(urlsplit(self.path).path).rsplit('.', 1)[-1].lower()])
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        if not head:
            self.wfile.write(content)
        return True

    def do_GET(self):  # noqa: N802
        if not self._send_store(False):
            super().do_GET()

    def do_HEAD(self):  # noqa: N802
        if not self._send_store(True):
            super().do_HEAD()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('port', nargs='?', type=int, default=8000)
    parser.add_argument('--bind', '-b', default='127.0.0.1')
    parser.add_argument('--directory', '-d', default='.')
    args = parser.parse_args(argv)
    handler = functools.partial(Handler, directory=str(Path(args.directory).resolve()))
    with ThreadingHTTPServer((args.bind, args.port), handler) as server:
        print(f'Serving HTTP on {args.bind} port {args.port} (con almacén de portadas)', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
