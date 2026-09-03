#!/usr/bin/env python3
"""Regresion (item 37 de la ronda 2026-09): cada href que termina en
#fragmento (en la misma pagina o apuntando a otra) debe resolver a un id
real en la pagina de destino.

Por que importa: un enlace muerto de este tipo (href="/pagina/#faq" donde
esa pagina ya no tiene id="faq") sigue devolviendo HTTP 200 -- el checker
de enlaces del CI (Lychee) valida el status code de la URL base, no si el
fragmento existe dentro del documento, asi que este tipo de rotura escapa
por completo a esa red de seguridad.

Estado encontrado: limpio. 152 enlaces #fragmento en la misma pagina y 172
enlaces cruzados pagina->#fragmento, todos resueltos correctamente.

Uso:
  python tests/test-fragment-links-resolve.py
"""
from __future__ import annotations

import html
import io
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PREFIXES = ("lab/", "tests/", "data/", "qa/")

HREF_RE = re.compile(r'href="([^"]+)"')
ID_RE = re.compile(r'\bid="([^"]+)"')
NAME_RE = re.compile(r'<a\b[^>]*\bname="([^"]+)"')


def load_html_files() -> list[str]:
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "-z", "*.html"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8").split("\0")
    return [t for t in out if t and not t.startswith(EXCLUDED_PREFIXES)]


def path_to_file(path: str) -> Path | None:
    path = path.lstrip("/")
    if path == "":
        return ROOT / "index.html"
    if path.endswith("/"):
        return ROOT / path / "index.html"
    if path.endswith(".html"):
        return ROOT / path
    for candidate in (ROOT / f"{path}/index.html", ROOT / f"{path}.html"):
        if candidate.exists():
            return candidate
    return None


html_files = load_html_files()
id_cache: dict[str, set[str] | None] = {}


def ids_for(path: str) -> set[str] | None:
    if path in id_cache:
        return id_cache[path]
    f = path_to_file(path)
    if f is None or not f.exists():
        id_cache[path] = None
        return None
    text = f.read_text(encoding="utf-8", errors="ignore")
    ids = set(ID_RE.findall(text)) | set(NAME_RE.findall(text))
    id_cache[path] = ids
    return ids


failures: list[str] = []
same_page_checked = 0
cross_page_checked = 0

for rel in html_files:
    text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    page_ids = ids_for("/" + rel[:-len("index.html")] if rel.endswith("index.html") else "/" + rel[:-5]) or set()

    for raw_href in HREF_RE.findall(text):
        href = html.unescape(raw_href)
        if href.startswith(("http://", "https://", "mailto:", "tel:", "javascript:")):
            continue
        if href.startswith("#"):
            same_page_checked += 1
            frag = href[1:]
            if frag == "":
                continue
            if frag not in page_ids:
                failures.append(f"{rel}: href=\"#{frag}\" has no matching id/name on the same page")
            continue
        parsed = urlsplit(href)
        if not parsed.fragment:
            continue
        cross_page_checked += 1
        ids = ids_for(parsed.path)
        if ids is None:
            failures.append(f"{rel}: href=\"{href}\" -> target page {parsed.path!r} not found locally")
        elif parsed.fragment not in ids:
            failures.append(f"{rel}: href=\"{href}\" -> #{parsed.fragment} has no matching id on {parsed.path}")

print(f"tests/test-fragment-links-resolve: checked {same_page_checked} same-page + {cross_page_checked} cross-page fragment link(s) across {len(html_files)} page(s)")
if failures:
    for f in failures[:40]:
        print(f"  FAIL {f}")
    print(f"tests/test-fragment-links-resolve: {len(failures)} FALLO(S)")
else:
    print("  ok   every #fragment link resolves to a real id on its target page")
    print("tests/test-fragment-links-resolve: OK")
raise SystemExit(1 if failures else 0)
