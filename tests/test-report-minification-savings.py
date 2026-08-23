#!/usr/bin/env python3
"""Verifica que minify_css() en scripts/report-minification-savings.py no
rompe construcciones delicadas de CSS real (calc(), url() con comillas,
media queries, comentarios) antes de fiarse de sus numeros.

Uso:
  python tests/test-report-minification-savings.py
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
_spec = importlib.util.spec_from_file_location("rms", ROOT / "scripts" / "report-minification-savings.py")
rms = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = rms
_spec.loader.exec_module(rms)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def run() -> None:
    # Los comentarios desaparecen sin dejar residuo pegado al selector siguiente.
    out = rms.minify_css("/* comentario */\n.a { color: red; }")
    check(".a{color:red}" in out.replace(" ", "").replace(";}", "}"), "comentario eliminado sin romper el selector")

    # calc() conserva sus espacios internos (removerlos cambiaria el resultado).
    out = rms.minify_css(".b { width: calc(100% - 20px); }")
    check("calc(100% - 20px)" in out, "calc() conserva sus espacios internos", out)

    # url() con comillas y espacios internos no se toca.
    out = rms.minify_css('.c { background: url("a b.png"); }')
    check('url("a b.png")' in out, "url() con espacios en comillas no se corrompe", out)

    # Selectores separados por coma conservan un unico espacio (no se fusionan).
    out = rms.minify_css("h1,\nh2,\nh3 { margin: 0; }")
    check("h1,h2,h3" in out.replace(" ", ""), "selectores multiples separados por coma se conservan", out)

    # Media queries conservan su estructura anidada.
    out = rms.minify_css("@media (min-width: 40em) { .d { color: blue; } }")
    check("@media" in out and ".d{color:blue}" in out.replace(" ", "").replace(";}", "}"), "media query conserva su bloque anidado", out)

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-report-minification-savings: OK")


if __name__ == "__main__":
    run()
