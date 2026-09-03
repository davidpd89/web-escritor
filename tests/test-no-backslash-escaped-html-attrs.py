#!/usr/bin/env python3
"""Regresion: ningun atributo HTML debe contener comillas escapadas con
backslash (\\" en vez de &quot;).

Bug real encontrado en produccion: herramientas/dialogo-convenciones/index.html
tenia placeholder="...&#10;&#10;\"No tardes\", anadio ella." -- un backslash
NO es un escape valido dentro de un atributo HTML entre comillas dobles, asi
que el parser real del navegador cierra el atributo en la comilla literal que
sigue al backslash, dejando el resto del texto (No tardes\", anadio ella.")
como atributos basura del propio tag (confirmado en vivo: el <textarea> real
llevaba no="", 'tardes\",'="", anadio="", 'ella."'="" como atributos, y el
placeholder mostrado al usuario quedaba truncado). El fix es HTML-escapar la
comilla como &quot;, no con backslash (que es sintaxis JSON/JS, no HTML).

Uso:
  python tests/test-no-backslash-escaped-html-attrs.py
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

# Un atributo con comilla escapada por backslash: ="...algo\" -- la comilla
# de cierre real es la que sigue al backslash, asi que el patron busca un
# backslash inmediatamente antes de una comilla que NO sea la de apertura
# (heuristica: backslash seguido de comilla doble, dentro de lo que ya es
# territorio de atributo tras un "=\"").
SUSPECT_RE = re.compile(r'="[^"]*\\"')

tracked = subprocess.run(
    ["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True
).stdout.splitlines()

failures: list[str] = []
checked = 0
for rel in tracked:
    rel = rel.strip()
    if not rel or rel.startswith(("lab/", "qa/", "tests/", "data/")):
        continue
    path = ROOT / rel
    text = path.read_text(encoding="utf-8", errors="ignore")
    checked += 1
    for m in SUSPECT_RE.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        failures.append(f"{rel}:{line_no}: backslash-escaped quote inside an HTML attribute: {m.group(0)[:80]!r}")

print(f"tests/test-no-backslash-escaped-html-attrs: checked {checked} real page(s)")
if failures:
    for f in failures:
        print(f"  FAIL {f}")
    print(f"tests/test-no-backslash-escaped-html-attrs: {len(failures)} FALLO(S)")
else:
    print("  ok   no backslash-escaped quotes found in any attribute")
    print("tests/test-no-backslash-escaped-html-attrs: OK")
raise SystemExit(1 if failures else 0)
