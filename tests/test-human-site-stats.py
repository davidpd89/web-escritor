#!/usr/bin/env python3
"""Fixture del propio documento 60 (seccion "QA"), verificado contra el motor real.

El documento dice haber probado: 2 libros indexables + 1 noindex, 3 articulos
indexables + 1 noindex, 2 herramientas, 1 bloque data-public-sample, y una
canonical duplicada como caso de error. Nada de eso tenia un test hasta ahora.

De paso, esta es la pieza que descubrio que la clasificacion "PENDIENTE/
HUERFANO — nunca conectado a un output visible" del catalogo de docs de
20/08/2026 era un falso negativo: autor.html SI tiene los marcadores
`human-site-stats:start/end` y el CSS enlazado. Solo estaba desactualizado
(generado el 19/08 con 13 herramientas; el 21/08 ya hay 15 paginas
indexables bajo /herramientas/*/). No estaba huerfano, estaba parado.

Uso:
  python tests/test-human-site-stats.py
"""
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "build_human_site_stats", ROOT / "scripts" / "build-human-site-stats.py"
)
bhs = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = bhs  # @dataclass necesita el modulo ya registrado
_spec.loader.exec_module(bhs)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def page(rel: str, canonical: str, noindex: bool = False, extra: str = "") -> tuple[str, str]:
    robots = '<meta name="robots" content="noindex,nofollow">' if noindex else ""
    return rel, (
        f'<!doctype html><html><head><link rel="canonical" href="{canonical}">'
        f"{robots}</head><body>{extra}</body></html>"
    )


print("tests/test-human-site-stats")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    pages = [
        page("libros/uno/index.html", "https://davidportodiaz.com/libros/uno/"),
        page("libros/dos/index.html", "https://davidportodiaz.com/libros/dos/"),
        page("libros/tres/index.html", "https://davidportodiaz.com/libros/tres/", noindex=True),
        page("cuaderno/a/index.html", "https://davidportodiaz.com/cuaderno/a/"),
        page("cuaderno/b/index.html", "https://davidportodiaz.com/cuaderno/b/"),
        page("cuaderno/c/index.html", "https://davidportodiaz.com/cuaderno/c/"),
        page("cuaderno/d/index.html", "https://davidportodiaz.com/cuaderno/d/", noindex=True),
        page("herramientas/x/index.html", "https://davidportodiaz.com/herramientas/x/"),
        page(
            "herramientas/y/index.html",
            "https://davidportodiaz.com/herramientas/y/",
            extra='<p>Antes.</p><div data-public-sample>Cinco palabras de muestra aqui.</div><p>Despues, no cuenta.</p>',
        ),
    ]
    for rel, content in pages:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    items = bhs.stats(root)
    by_key = {i["key"]: i["value"] for i in items}
    check(by_key.get("books") == 2, "2 libros indexables cuentan, el noindex no", str(by_key))
    check(by_key.get("articles") == 3, "3 articulos indexables cuentan, el noindex no", str(by_key))
    check(by_key.get("tools") == 2, "2 herramientas cuentan", str(by_key))
    # "Cinco palabras de muestra aqui." = 5 palabras; el texto fuera del bloque
    # data-public-sample ("Antes."/"Despues, no cuenta.") no debe sumarse.
    check(
        by_key.get("sample_words") == 5,
        "solo las palabras dentro de data-public-sample cuentan",
        str(by_key),
    )

    fragment = bhs.render(items, "2026-08-21")
    check("<script" not in fragment.lower(), "el fragmento no lleva JavaScript (doc 60: sin JS en cliente)")

# Canonical duplicada: caso de error explicito del documento.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    dup = "https://davidportodiaz.com/libros/uno/"
    for rel in ("libros/uno/index.html", "libros/otro/index.html"):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f'<html><head><link rel="canonical" href="{dup}"></head><body></body></html>', encoding="utf-8")
    try:
        bhs.stats(root)
        check(False, "una canonical duplicada debe rechazar el build")
    except ValueError as exc:
        check("duplicad" in str(exc), "una canonical duplicada debe rechazar el build", str(exc))

print("tests/test-human-site-stats: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
