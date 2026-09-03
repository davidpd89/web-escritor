#!/usr/bin/env python3
"""Regresion: el contenedor de resultados de cada herramienta de
herramientas/*/index.html debe llevar aria-live (o vivir dentro de un
ancestro que ya lo declare), para que un lector de pantalla anuncie el
cambio de "vacio/oculto" a "resultado real" sin que el usuario tenga que
ir a buscarlo manualmente.

Bug real encontrado: 13 de 16 herramientas con contenedor .tool-results
no llevaban aria-live en absoluto (solo 3 -- dialogo, dialogo-convenciones,
nombres-personajes -- lo tenian), confirmado en vivo: al enviar el
formulario de contador-palabras, el contenedor de resultados pasaba de
hidden a visible con el conteo real, pero sin aria-live no habria
anuncio automatico para un lector de pantalla.

Uso:
  python tests/test-tool-results-aria-live.py
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

RESULTS_TAG_RE = re.compile(
    r'<(section|div)\s+class="tool-results"[^>]*\bdata-[a-z-]*results[a-z-]*\b[^>]*\bhidden\b[^>]*>',
    re.IGNORECASE,
)

tracked = subprocess.run(
    ["git", "ls-files", "herramientas/*/index.html"], cwd=ROOT, capture_output=True, text=True, check=True
).stdout.splitlines()

failures: list[str] = []
checked = 0
for rel in tracked:
    rel = rel.strip()
    if not rel:
        continue
    text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    m = RESULTS_TAG_RE.search(text)
    if not m:
        continue
    checked += 1
    tag = m.group(0)
    if "aria-live" not in tag:
        failures.append(f"{rel}: .tool-results container has no aria-live: {tag[:120]!r}")

print(f"tests/test-tool-results-aria-live: checked {checked} tool page(s) with a .tool-results container")
if failures:
    for f in failures:
        print(f"  FAIL {f}")
    print(f"tests/test-tool-results-aria-live: {len(failures)} FALLO(S)")
else:
    print("  ok   every .tool-results container declares aria-live")
    print("tests/test-tool-results-aria-live: OK")
raise SystemExit(1 if failures else 0)
