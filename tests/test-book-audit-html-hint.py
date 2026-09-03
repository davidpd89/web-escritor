#!/usr/bin/env python3
"""Regresion: el campo "Codigo HTML de la pagina" del auditor de pagina de
libro debe explicar como obtener ese HTML (Ver codigo fuente / Ctrl+U) en un
tool-field-hint PERSISTENTE, no solo en el placeholder.

Bug real encontrado (item 12 de la ronda de auditoria 2026-09): la unica
explicacion de como conseguir el HTML vivia dentro del atributo placeholder,
que desaparece en cuanto el campo deja de estar vacio -- si el usuario pega
algo, lo borra y vuelve a intentarlo mas tarde sin recordar el atajo, no
tenia donde volver a leerlo en la pagina. El resto de campos de formato
libre en el sitio (p. ej. pov-distribucion) ya usan un tool-field-hint
persistente ligado con aria-describedby para esto mismo.

Uso:
  python tests/test-book-audit-html-hint.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "herramientas" / "auditor-pagina-libro" / "index.html"

text = PAGE.read_text(encoding="utf-8")
failures: list[str] = []


def check(condition: bool, label: str) -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


check(
    'id="book-audit-html-hint"' in text and "Ver código fuente de la página" in text,
    "existe un tool-field-hint persistente con la instrucción de Ver código fuente",
)
check(
    'aria-describedby="book-audit-html-hint"' in text,
    "el textarea liga el hint via aria-describedby",
)

print(f"tests/test-book-audit-html-hint: {'OK' if not failures else f'{len(failures)} FALLO(S)'}")
raise SystemExit(1 if failures else 0)
