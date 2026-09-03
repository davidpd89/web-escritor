#!/usr/bin/env python3
"""Regresion (item 21 de la ronda 2026-09): toda referencia local a un
asset (src, href, poster, srcset, imagesrcset, url() en CSS) debe coincidir
EXACTAMENTE en mayusculas/minusculas con el nombre real del archivo en git.

Por que importa: Windows y macOS (por defecto) tienen sistema de archivos
insensible a mayusculas, asi que una referencia mal escrita como
"Foo.webp" cuando el archivo real es "foo.webp" funciona sin problema en
el entorno de desarrollo y en el propio `git status` (que no la marca como
cambio), pero GitHub Pages/Linux en produccion la serviria como 404 real.
El checker de enlaces del CI (Lychee, sobre ubuntu-latest) ya cubre esto
para href/src basicos; este test añade cobertura para srcset/imagesrcset
y url() de CSS, que un link-checker generico normalmente no analiza.

Estado encontrado: limpio. 4507 referencias locales comprobadas en 78
paginas HTML + 88 hojas de estilo, cero discrepancias de mayusculas.

Uso:
  python tests/test-case-sensitive-asset-references.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_HTML_PREFIXES = ("lab/", "tests/", "data/", "qa/")

REF_RE = re.compile(r'(?:src|href|poster|imagesrcset|srcset)\s*=\s*"([^"]+)"', re.IGNORECASE)
CSS_URL_RE = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)')


def load_tracked() -> list[str]:
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "-z"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout.decode("utf-8").split("\0")
    return [t for t in out if t]


def resolve(ref: str, source_file: str) -> list[str]:
    ref = ref.strip()
    if not ref or ref.startswith(("http://", "https://", "mailto:", "tel:", "data:", "//", "#", "javascript:")):
        return []
    rels = []
    for cand in (c.strip().split(" ")[0] for c in ref.split(",") if c.strip()):
        path = unquote(urlsplit(cand).path)
        if not path or path.startswith("http") or path.endswith("/"):
            continue
        if path.startswith("/"):
            rel = path.lstrip("/")
        else:
            parts: list[str] = []
            for seg in (str((Path(source_file).parent / path).as_posix())).split("/"):
                if seg == "..":
                    if parts:
                        parts.pop()
                elif seg != ".":
                    parts.append(seg)
            rel = "/".join(parts)
        if rel:
            rels.append(rel)
    return rels


tracked = load_tracked()
real_paths = set(tracked)
lower_to_real: dict[str, list[str]] = {}
for t in tracked:
    lower_to_real.setdefault(t.lower(), []).append(t)

html_files = [t for t in tracked if t.endswith(".html") and not t.startswith(EXCLUDED_HTML_PREFIXES)]
css_files = [t for t in tracked if t.endswith(".css") and not t.startswith("lab/")]

failures: list[str] = []
checked = 0

for f in html_files:
    text = (ROOT / f).read_text(encoding="utf-8", errors="ignore")
    for m in REF_RE.finditer(text):
        for rel in resolve(m.group(1), f):
            checked += 1
            if rel in real_paths:
                continue
            matches = lower_to_real.get(rel.lower())
            if matches:
                failures.append(f"{f}: references {m.group(1)!r} (resolved {rel!r}) but the real file is {matches}")

for f in css_files:
    text = (ROOT / f).read_text(encoding="utf-8", errors="ignore")
    for m in CSS_URL_RE.finditer(text):
        for rel in resolve(m.group(1), f):
            checked += 1
            if rel in real_paths:
                continue
            matches = lower_to_real.get(rel.lower())
            if matches:
                failures.append(f"{f}: url({m.group(1)!r}) (resolved {rel!r}) but the real file is {matches}")

print(f"tests/test-case-sensitive-asset-references: checked {checked} local reference(s) across {len(html_files)} HTML + {len(css_files)} CSS file(s)")
if failures:
    for f in failures[:40]:
        print(f"  FAIL {f}")
    print(f"tests/test-case-sensitive-asset-references: {len(failures)} FALLO(S)")
else:
    print("  ok   every local reference matches the real file's casing exactly")
    print("tests/test-case-sensitive-asset-references: OK")
raise SystemExit(1 if failures else 0)
