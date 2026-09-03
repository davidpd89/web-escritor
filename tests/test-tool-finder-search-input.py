#!/usr/bin/env python3
"""Regresion: el input type="search" dentro de un .tool-finder (la barra de
filtros compartida por editoriales, convocatorias-escritores, etc.) debe
llevar autocomplete="off" y enterkeyhint="search", igual que ya lo hace
editoriales/index.html.

Bug real encontrado: convocatorias-escritores/index.html y
recursos/herramientas-para-escritores/index.html reutilizan el mismo
componente .tool-finder pero su input de busqueda no llevaba ninguno de los
dos atributos -- en movil el teclado no ofrece necesariamente la accion
"buscar" y el campo puede mostrar sugerencias de autocompletado del
navegador que no tienen sentido en un filtro en vivo (sin <form>, sin envio).

Uso:
  python tests/test-tool-finder-search-input.py
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

FINDER_RE = re.compile(r'class="tool-finder"', re.IGNORECASE)
SEARCH_INPUT_RE = re.compile(r'<input\b[^>]*\btype="search"[^>]*>', re.IGNORECASE)

tracked = subprocess.run(
    ["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True
).stdout.splitlines()

failures: list[str] = []
checked = 0
for rel in tracked:
    rel = rel.strip()
    if not rel:
        continue
    text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    if not FINDER_RE.search(text):
        continue
    m = SEARCH_INPUT_RE.search(text)
    if not m:
        continue
    checked += 1
    tag = m.group(0)
    missing = [attr for attr in ("autocomplete=", "enterkeyhint=") if attr not in tag]
    if missing:
        failures.append(f"{rel}: search input in .tool-finder missing {missing}: {tag[:140]!r}")

print(f"tests/test-tool-finder-search-input: checked {checked} .tool-finder search input(s)")
if failures:
    for f in failures:
        print(f"  FAIL {f}")
    print(f"tests/test-tool-finder-search-input: {len(failures)} FALLO(S)")
else:
    print("  ok   every .tool-finder search input declares autocomplete + enterkeyhint")
    print("tests/test-tool-finder-search-input: OK")
raise SystemExit(1 if failures else 0)
