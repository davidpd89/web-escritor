#!/usr/bin/env python3
"""Genera `assets/page-order.generated.js`: el orden de las fichas hermanas de cada familia.

`assets/v1-editorial-interior-v4.js` lo lee para pintar al final de cada ficha un
pie «Anterior · Índice · Siguiente» (editoriales, libros y autores recomendados,
herramientas, Cuaderno, Atlas literario). Es un script estático y no un JSON porque la CSP de las fichas es
`connect-src 'none'` (no permite fetch) pero sí scripts propios. Las páginas no cambian cuando se añade una ficha, solo este índice, y una ficha que
todavía no figura en él simplemente no muestra el pie.

Orden: alfabético por título donde no hay un orden editorial (editoriales,
libros, autores) y el orden del propio índice de la familia donde sí lo hay
(herramientas, Cuaderno, Atlas).

Uso:
  python scripts/build-page-order.py           # escribe assets/page-order.generated.js
  python scripts/build-page-order.py --check   # falla si el fichero no está al día
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "page-order.generated.js"
PREFIX = "/* Generado por scripts/build-page-order.py: no editar a mano. */\nwindow.DP_PAGE_ORDER="
SUFFIX = ";\n"

# prefix, hub label, order ("alpha" | "hub"), pages that are sub-hubs and not siblings
FAMILIES = (
    ("/editoriales/", "Editoriales", "alpha", ()),
    ("/recomendaciones/libros/", "Libros recomendados", "alpha", ()),
    ("/recomendaciones/autores/", "Autores recomendados", "alpha", ()),
    ("/recomendaciones/editoriales/", "Editoriales de los libros", "alpha", ()),
    ("/herramientas/", "Herramientas", "hub", ()),
    ("/cuaderno/", "Cuaderno", "hub", ("temas",)),
    ("/atlas-literario/", "Atlas literario", "hub", ()),
)
H1 = re.compile(r"<h1\b[^>]*>([\s\S]*?)</h1>", re.I)
TAG = re.compile(r"<[^>]+>")
NOINDEX = re.compile(r'<meta[^>]+name="robots"[^>]+content="[^"]*noindex', re.I)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", text))).strip()


def sort_key(title: str) -> str:
    plain = "".join(c for c in unicodedata.normalize("NFD", title.casefold()) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", "", plain).strip()


def family_pages(prefix: str, skip: tuple[str, ...]) -> dict[str, str]:
    base = ROOT / prefix.strip("/")
    pages: dict[str, str] = {}
    for folder in sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []:
        index = folder / "index.html"
        if folder.name in skip or not index.is_file():
            continue
        text = index.read_text(encoding="utf-8")
        match = H1.search(text)
        if NOINDEX.search(text) or not match or not clean(match.group(1)):
            continue
        pages[f"{prefix}{folder.name}/"] = clean(match.group(1))
    return pages


def hub_order(prefix: str) -> list[str]:
    hub = ROOT / prefix.strip("/") / "index.html"
    if not hub.is_file():
        return []
    seen: list[str] = []
    for href in re.findall(r'href="([^"#?]+)', hub.read_text(encoding="utf-8")):
        if href.startswith(prefix) and href != prefix and href not in seen:
            seen.append(href if href.endswith("/") else href + "/")
    return seen


def build() -> dict:
    families = []
    for prefix, label, order, skip in FAMILIES:
        pages = family_pages(prefix, skip)
        if len(pages) < 2:
            continue
        if order == "hub":
            ranked = [h for h in hub_order(prefix) if h in pages]
            ranked += sorted((h for h in pages if h not in ranked), key=lambda h: sort_key(pages[h]))
        else:
            ranked = sorted(pages, key=lambda h: (sort_key(pages[h]), h))
        families.append({"prefix": prefix, "hub": {"href": prefix if prefix != "/recomendaciones/libros/" else "/recomendaciones/", "label": label},
                         "items": [[href, pages[href]] for href in ranked]})
    return {"schema_version": 1, "families": families}


def render(data: dict) -> str:
    return PREFIX + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + SUFFIX


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="No escribe: falla si el fichero no está al día")
    args = parser.parse_args()
    text = render(build())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != text:
            print("FAIL: assets/page-order.generated.js no está al día; ejecuta python scripts/build-page-order.py", file=sys.stderr)
            return 1
        print("CHECK: assets/page-order.generated.js al día")
        return 0
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"GENERATED: {OUTPUT.relative_to(ROOT)} ({len(text) // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
