#!/usr/bin/env python3
"""Puente importable hacia scripts/build-site-shell.py.

El builder del shell se llama con guiones, así que no se puede importar con un
`import` normal. Este módulo hace el rodeo una sola vez y expone lo único que
los builders de páginas necesitan: `inject_shell_auto`.

Por qué existe: editoriales, convocatorias y los temas del Cuaderno generan
páginas completas y cada uno llevaba su propia copia literal de la cabecera, el
diálogo Explorar y el pie dentro de una cadena de Python. Eran tres copias más
del shell, mantenidas a mano, además de las 59 páginas escritas. En cuanto el
shell pasó a generarse desde data/navigation.json, esas tres copias se quedaron
atrás y sus tests de paridad empezaron a fallar: dos builders escribiendo el
mismo fichero y discrepando.

Ahora los tres piden el bloque aquí, así que el `--check` de cada builder y el
de build-site-shell.py coinciden por construcción en vez de por disciplina.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "build_site_shell", _ROOT / "scripts" / "build-site-shell.py"
)
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE  # @dataclass necesita el módulo ya registrado
_SPEC.loader.exec_module(_MODULE)

inject_shell = _MODULE.inject_shell


def rel_path_from_canonical(canonical: str) -> str:
    """`https://davidportodiaz.com/editoriales/` -> `editoriales/index.html`."""
    path = urlparse(canonical).path or "/"
    if path.endswith("/"):
        return (path.lstrip("/") + "index.html") or "index.html"
    return path.lstrip("/")


def inject_shell_auto(html: str) -> str:
    """Inyecta el shell deduciendo la ruta del propio canonical de la página.

    Se apoya en el canonical y no en la ruta de escritura a propósito: los tests
    de paridad generan a un directorio temporal, y lo que decide qué extras de
    pie lleva una página es su ruta pública, no dónde se escriba el fichero.
    """
    match = _MODULE.CANONICAL_RE.search(html)
    if not match:
        raise ValueError("no se puede inyectar el shell: la página no declara canonical")
    return inject_shell(html, rel_path_from_canonical(match.group(1)))
