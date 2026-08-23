#!/usr/bin/env python3
"""Gate de coherencia de microcopy del asistente (L.2, 2026-08-23).

assets/assistant-copy.js es la autoridad unica de las cadenas visibles del
asistente. Antes de esta PR, asistente/index.html declaraba una
experiencia y assets/assistant.js la reescribia por otra en tiempo de
ejecucion sin ningun contrato compartido. Este checker parsea ambos
ficheros de forma estatica (sin ejecutar JS) y falla si:

  - assistant.js usa un literal hardcodeado para un campo que deberia
    venir de ASSISTANT_COPY (regresion: alguien vuelve a hardcodear en vez
    de usar la autoridad);
  - el HTML estatico de asistente/index.html no coincide, campo a campo,
    con los valores de ASSISTANT_COPY (regresion: el estado pre-JS/no-JS
    vuelve a divergir del runtime).

Python standard library only.

Usage:
    python scripts/check-assistant-copy.py
    python scripts/check-assistant-copy.py --check
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COPY_FIELD_RE = re.compile(r'(\w+):\s*"((?:[^"\\]|\\.)*)"')


def load_copy(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    return {k: v.encode().decode("unicode_escape") if "\\" in v else v for k, v in COPY_FIELD_RE.findall(text)}


def check_js_uses_authority(js_text: str, copy: dict[str, str]) -> list[str]:
    errors = []
    # Si alguno de los valores literales de la autoridad vuelve a aparecer
    # como STRING LITERAL suelto en assistant.js (fuera de
    # assistant-copy.js), es que alguien ha vuelto a hardcodear en vez de
    # usar ASSISTANT_COPY.<campo>.
    for field, value in copy.items():
        literal = f'"{value}"'
        if literal in js_text:
            errors.append(f"assets/assistant.js: usa el literal hardcodeado de '{field}' en vez de ASSISTANT_COPY.{field}")
    if "ASSISTANT_COPY" not in js_text:
        errors.append("assets/assistant.js: no importa/usa ASSISTANT_COPY en absoluto")
    return errors


def check_html_matches_authority(html_text: str, copy: dict[str, str]) -> list[str]:
    errors = []
    checks = [
        ("heroTitle", rf'<h1>{re.escape(copy["heroTitle"])}</h1>'),
        ("heroLead", re.escape(copy["heroLead"])),
        ("queryLabel", rf'<h2 id="assistant-title">{re.escape(copy["queryLabel"])}</h2>'),
        ("queryLabel (label)", rf'<label for="assistant-query">{re.escape(copy["queryLabel"])}</label>'),
        ("placeholder", rf'placeholder="{re.escape(copy["placeholder"])}"'),
        ("submitAriaLabel", rf'aria-label="{re.escape(copy["submitAriaLabel"])}"'),
        ("stopAriaLabel", rf'aria-label="{re.escape(copy["stopAriaLabel"])}"'),
    ]
    for label, pattern in checks:
        if not re.search(pattern, html_text):
            errors.append(f"asistente/index.html: no contiene el valor esperado para '{label}' (autoridad: assets/assistant-copy.js)")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    copy_path = root / "assets" / "assistant-copy.js"
    js_path = root / "assets" / "assistant.js"
    html_path = root / "asistente" / "index.html"

    if not (copy_path.exists() and js_path.exists() and html_path.exists()):
        print("AVISO: faltan ficheros del asistente; nada que verificar.")
        return 0

    copy = load_copy(copy_path)
    errors: list[str] = []
    errors += check_js_uses_authority(js_path.read_text(encoding="utf-8"), copy)
    errors += check_html_matches_authority(html_path.read_text(encoding="utf-8"), copy)

    for e in errors:
        print(f"ERROR {e}")

    print(f"\nAssistant copy check: {len(errors)} incumplimiento(s).")
    if args.check and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
