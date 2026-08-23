#!/usr/bin/env python3
"""Verifica scripts/check-assistant-copy.py con fixtures aislados
(L.2, 2026-08-23).

Uso:
  python tests/test-check-assistant-copy.py
"""
from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("cac", ROOT / "scripts" / "check-assistant-copy.py")
cac = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = cac
_spec.loader.exec_module(cac)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


COPY = {"heroTitle": "¿Qué buscas?", "placeholder": "Escribe tu pregunta…"}


def run() -> None:
    # Negativo: JS usa ASSISTANT_COPY, sin literales sueltos -> sin error.
    js_ok = 'import { ASSISTANT_COPY } from "x"; heroTitle.textContent = ASSISTANT_COPY.heroTitle;'
    errors = cac.check_js_uses_authority(js_ok, COPY)
    check(errors == [], "JS que usa ASSISTANT_COPY no genera error")

    # Positivo: JS vuelve a hardcodear un literal de la autoridad -> se detecta.
    js_bad = 'import { ASSISTANT_COPY } from "x"; heroTitle.textContent = "¿Qué buscas?";'
    errors = cac.check_js_uses_authority(js_bad, COPY)
    check(any("heroTitle" in e for e in errors), "JS que hardcodea un literal de la autoridad se detecta")

    # Positivo: JS ni siquiera importa ASSISTANT_COPY -> se detecta.
    js_missing = 'heroTitle.textContent = "algo distinto";'
    errors = cac.check_js_uses_authority(js_missing, COPY)
    check(any("no importa" in e for e in errors), "JS que no usa ASSISTANT_COPY en absoluto se detecta")

    # Negativo: HTML coincide con la autoridad -> sin error.
    html_ok = '<h1>¿Qué buscas?</h1><h2 id="assistant-title">Escribe tu pregunta</h2><label for="assistant-query">Escribe tu pregunta</label><textarea placeholder="Escribe tu pregunta…"></textarea><button aria-label="Enviar pregunta"></button><button aria-label="Detener respuesta"></button>'
    full_copy = {
        "heroTitle": "¿Qué buscas?", "heroLead": "x", "queryLabel": "Escribe tu pregunta",
        "placeholder": "Escribe tu pregunta…", "submitAriaLabel": "Enviar pregunta", "stopAriaLabel": "Detener respuesta",
    }
    html_ok_full = html_ok.replace("</h2>", f"</h2><p>{full_copy['heroLead']}</p>")
    errors = cac.check_html_matches_authority(html_ok_full, full_copy)
    check(errors == [], "HTML consistente con la autoridad no genera error", str(errors))

    # Positivo: HTML diverge del H1 esperado -> se detecta.
    html_bad = html_ok_full.replace("¿Qué buscas?</h1>", "Pregunta a esta web.</h1>")
    errors = cac.check_html_matches_authority(html_bad, full_copy)
    check(any("heroTitle" in e for e in errors), "HTML con H1 divergente se detecta")

    # Positivo: HTML con placeholder divergente -> se detecta.
    html_bad2 = html_ok_full.replace("Escribe tu pregunta…", "Por ejemplo: algo distinto")
    errors = cac.check_html_matches_authority(html_bad2, full_copy)
    check(any("placeholder" in e for e in errors), "HTML con placeholder divergente se detecta")

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-assistant-copy: OK")


if __name__ == "__main__":
    run()
