#!/usr/bin/env python3
"""Regresion (item 43 de la ronda 2026-09): todo <button> dentro de un
<form> debe declarar type="button|submit|reset" explicitamente.

Por que importa: el valor por defecto de <button> sin type es "submit",
asi que un boton de copiar texto, anadir un personaje o abrir ayuda que
viva dentro de un <form> sin type="button" enviaria el formulario por
accidente en vez de ejecutar su propia accion.

Estado encontrado: limpio. 107 <button> dentro de <form> en 78 paginas,
todos con type explicito.

Uso:
  python tests/test-button-type-in-forms.py
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
EXCLUDED_PREFIXES = ("lab/", "tests/", "data/", "qa/")

FORM_RE = re.compile(r'<form\b.*?</form>', re.DOTALL)
BUTTON_RE = re.compile(r'<button\b([^>]*)>')
TYPE_RE = re.compile(r'\btype\s*=\s*"([^"]*)"', re.IGNORECASE)

tracked = subprocess.run(
    ["git", "-c", "core.quotepath=false", "ls-files", "-z", "*.html"],
    cwd=ROOT, capture_output=True, check=True,
).stdout.decode("utf-8").split("\0")
html_files = [t for t in tracked if t and not t.startswith(EXCLUDED_PREFIXES)]

failures: list[str] = []
total_buttons = 0
for rel in html_files:
    text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
    for form_match in FORM_RE.finditer(text):
        for btn_match in BUTTON_RE.finditer(form_match.group(0)):
            total_buttons += 1
            attrs = btn_match.group(1)
            type_match = TYPE_RE.search(attrs)
            if not type_match:
                failures.append(f"{rel}: <button> inside <form> has no type attribute (defaults to submit): {btn_match.group(0)[:120]!r}")
            elif type_match.group(1).lower() not in ("button", "submit", "reset"):
                failures.append(f"{rel}: <button type=\"{type_match.group(1)}\"> is not a valid button type")

print(f"tests/test-button-type-in-forms: checked {total_buttons} <button> element(s) inside <form> across {len(html_files)} page(s)")
if failures:
    for f in failures[:40]:
        print(f"  FAIL {f}")
    print(f"tests/test-button-type-in-forms: {len(failures)} FALLO(S)")
else:
    print("  ok   every <button> inside a <form> declares an explicit type")
    print("tests/test-button-type-in-forms: OK")
raise SystemExit(1 if failures else 0)
