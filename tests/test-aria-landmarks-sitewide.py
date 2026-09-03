#!/usr/bin/env python3
"""Regresion (item 38 de la ronda 2026-09): cada pagina real debe tener
exactamente un <main>, y cuando hay mas de un <nav> en la misma pagina,
cada uno debe llevar un nombre accesible (aria-label/aria-labelledby)
distinto para que un lector de pantalla pueda diferenciarlos.

Excluye explicitamente los stubs de redireccion legacy
(<meta http-equiv="refresh">, p. ej. samuel-entre-mundos.html): son
paginas de una linea que reenvian a la URL real y no llevan contenido
propio, asi que no tener <main> ahi es correcto, no un fallo.

Estado encontrado: limpio. 78 paginas reales comprobadas (menos los
stubs de redireccion), todas con exactamente un <main> y navs
correctamente nombrados.

Uso:
  python tests/test-aria-landmarks-sitewide.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PREFIXES = ("lab/", "tests/", "data/", "qa/", "scripts/")
# video-ios-test/index.html: a deliberately bare-bones, noindex,nofollow
# real-device diagnostic page for isolating a hero-video playback bug --
# confirmed not deployed (404 in production), not linked from anywhere,
# and not meant for real visitors, so it has no semantic content to wrap
# in a landmark.
EXCLUDED_FILES = {"video-ios-test/index.html"}

MAIN_RE = re.compile(r'<main\b')
NAV_RE = re.compile(r'<nav\b([^>]*)>')
ARIA_LABEL_RE = re.compile(r'aria-label(?:ledby)?="([^"]*)"')
META_REFRESH_RE = re.compile(r'<meta\s+http-equiv="refresh"', re.IGNORECASE)

tracked = subprocess.run(
    ["git", "-c", "core.quotepath=false", "ls-files", "-z", "*.html"],
    cwd=ROOT, capture_output=True, check=True,
).stdout.decode("utf-8").split("\0")
html_files = [t for t in tracked if t and not t.startswith(EXCLUDED_PREFIXES) and t not in EXCLUDED_FILES]

failures: list[str] = []
checked = 0
for rel in html_files:
    text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    if META_REFRESH_RE.search(text):
        continue  # legacy redirect stub, not a real content page
    checked += 1

    main_count = len(MAIN_RE.findall(text))
    if main_count != 1:
        failures.append(f"{rel}: {main_count} <main> element(s) (expected exactly 1)")

    navs = NAV_RE.findall(text)
    names = []
    unnamed = 0
    for attrs in navs:
        m = ARIA_LABEL_RE.search(attrs)
        (names.append(m.group(1)) if m else None)
        if not m:
            unnamed += 1
    if len(navs) > 1 and unnamed > 0:
        failures.append(f"{rel}: {len(navs)} <nav> elements, {unnamed} without an accessible name")
    dup_names = {n for n in names if names.count(n) > 1}
    if dup_names:
        failures.append(f"{rel}: multiple <nav> share the same accessible name: {sorted(dup_names)}")

print(f"tests/test-aria-landmarks-sitewide: checked {checked} real page(s)")
if failures:
    for f in failures[:40]:
        print(f"  FAIL {f}")
    print(f"tests/test-aria-landmarks-sitewide: {len(failures)} FALLO(S)")
else:
    print("  ok   every page has exactly one <main>, every multi-nav page names each nav")
    print("tests/test-aria-landmarks-sitewide: OK")
raise SystemExit(1 if failures else 0)
