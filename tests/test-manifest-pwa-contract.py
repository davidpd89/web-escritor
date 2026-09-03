#!/usr/bin/env python3
"""Regresion (item 48 de la ronda 2026-09): auditoria del manifest.json de
la PWA -- campos obligatorios, iconos que existen de verdad con el tamano
declarado, y que cada pagina enlaza el manifest con la misma ruta absoluta.

Bug real encontrado: index.html enlazaba el manifest con una ruta
relativa (href="manifest.json") mientras las otras 77 paginas usan la
ruta absoluta (href="/manifest.json"). Como index.html vive en la raiz
ambas resuelven al mismo sitio hoy, asi que no rompia nada -- pero es una
inconsistencia real que se convertiria en un enlace roto (buscando
/alguna-ruta/manifest.json) si alguna vez se copia ese <head> a una
pagina que no este en la raiz.

Uso:
  python tests/test-manifest-pwa-contract.py
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PREFIXES = ("lab/", "tests/", "data/", "qa/", "scripts/")

failures: list[str] = []


def check(condition: bool, label: str) -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


# --- manifest.json content ---
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
for field in ("name", "short_name", "start_url", "display", "background_color", "theme_color", "icons"):
    check(bool(manifest.get(field)), f"manifest.json has required field '{field}'")

icons = manifest.get("icons", [])
check(any(i.get("purpose") == "any" for i in icons), "manifest.json has at least one icon with purpose=any")
check(any("512x512" in i.get("sizes", "") for i in icons), "manifest.json has at least one 512x512 icon")

try:
    from PIL import Image
    for icon in icons:
        src = icon["src"].lstrip("/")
        path = ROOT / src
        check(path.exists(), f"icon file exists on disk: {src}")
        if path.exists():
            with Image.open(path) as img:
                declared = icon.get("sizes", "")
                actual = f"{img.width}x{img.height}"
                check(actual == declared, f"{src}: declared size {declared!r} matches actual {actual!r}")
except ImportError:
    print("  (Pillow not available -- skipping icon dimension checks)")

# --- every real page links the manifest the same way ---
tracked = subprocess.run(
    ["git", "-c", "core.quotepath=false", "ls-files", "-z", "*.html"],
    cwd=ROOT, capture_output=True, check=True,
).stdout.decode("utf-8").split("\0")
html_files = [t for t in tracked if t and not t.startswith(EXCLUDED_PREFIXES)]

link_variants: dict[str, list[str]] = {}
for rel in html_files:
    text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    if 'rel="manifest"' not in text:
        continue
    import re
    m = re.search(r'rel="manifest"\s+href="([^"]+)"', text)
    if m:
        link_variants.setdefault(m.group(1), []).append(rel)

check(len(link_variants) == 1, f"every page links the manifest the same way (found variants: {list(link_variants.keys())})")

# --- favicons: same relative-vs-absolute href consistency bug class ---
import re as _re
icon_variants: dict[str, list[str]] = {}
touch_icon_variants: dict[str, list[str]] = {}
for rel in html_files:
    text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    m = _re.search(r'rel="icon"\s+type="image/png"\s+href="([^"]+)"', text)
    if m:
        icon_variants.setdefault(m.group(1), []).append(rel)
    m2 = _re.search(r'rel="apple-touch-icon"\s+href="([^"]+)"', text)
    if m2:
        touch_icon_variants.setdefault(m2.group(1), []).append(rel)

check(len(icon_variants) == 1, f"every page links the PNG favicon the same way (found variants: {list(icon_variants.keys())})")
check(len(touch_icon_variants) == 1, f"every page links the apple-touch-icon the same way (found variants: {list(touch_icon_variants.keys())})")

favicon_ico = ROOT / "favicon.ico"
check(favicon_ico.exists(), "favicon.ico (legacy browser-default fallback) exists at the root")

print(f"tests/test-manifest-pwa-contract: {'OK' if not failures else f'{len(failures)} FALLO(S)'}")
raise SystemExit(1 if failures else 0)
