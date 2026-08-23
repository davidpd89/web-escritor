#!/usr/bin/env python3
"""Verifica scripts/check-analytics-taxonomy.py con fixtures aislados
(I.1, 2026-08-23).

Uso:
  python tests/test-check-analytics-taxonomy.py
"""
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("cat", ROOT / "scripts" / "check-analytics-taxonomy.py")
cat = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = cat
_spec.loader.exec_module(cat)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


REGISTRY = {
    "events": [{"name": "leer-fragmento-samuel", "action": "sample_open", "context": "samuel", "note": "x"}],
    "article_bridge": {"names_by_module": {"assets/tool.js": ["known_event"]}},
}


def run() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        (tmp / "assets").mkdir()

        # Positivo: evento _gcEvent registrado -> sin error.
        (tmp / "script.js").write_text('_gcEvent("leer-fragmento-samuel", "x");', encoding="utf-8")
        errors = cat.check_gc_events([tmp / "script.js"], tmp, {e["name"] for e in REGISTRY["events"]})
        check(errors == [], "evento _gcEvent registrado no genera error")

        # Positivo: evento _gcEvent NO registrado -> se detecta.
        (tmp / "script.js").write_text('_gcEvent("evento-inventado", "x");', encoding="utf-8")
        errors = cat.check_gc_events([tmp / "script.js"], tmp, {e["name"] for e in REGISTRY["events"]})
        check(any("evento-inventado" in e for e in errors), "evento _gcEvent NO registrado se detecta")

        # Positivo: data-gc no registrado -> se detecta.
        (tmp / "script.js").write_text('el.dataset.gc; d.innerHTML = \'<a data-gc="cta-nueva">x</a>\';', encoding="utf-8")
        errors = cat.check_gc_events([tmp / "script.js"], tmp, {e["name"] for e in REGISTRY["events"]})
        check(any("cta-nueva" in e for e in errors), "data-gc no registrado se detecta")

        # Positivo: dp:analytics con nombre no registrado en su modulo -> se detecta.
        (tmp / "assets" / "tool.js").write_text(
            "function emit(event){document.dispatchEvent(new CustomEvent('dp:analytics',{detail:{event}}));}\n"
            "emit('nombre_no_registrado');\n",
            encoding="utf-8",
        )
        errors = cat.check_article_bridge([tmp / "assets" / "tool.js"], tmp, REGISTRY["article_bridge"]["names_by_module"])
        check(any("nombre_no_registrado" in e for e in errors), "nombre dp:analytics no registrado se detecta")

        # Negativo: dp:analytics con nombre SI registrado -> sin error.
        (tmp / "assets" / "tool.js").write_text(
            "function emit(event){document.dispatchEvent(new CustomEvent('dp:analytics',{detail:{event}}));}\n"
            "emit('known_event');\n",
            encoding="utf-8",
        )
        errors = cat.check_article_bridge([tmp / "assets" / "tool.js"], tmp, REGISTRY["article_bridge"]["names_by_module"])
        check(errors == [], "nombre dp:analytics registrado no genera error")

        # Positivo: fichero nuevo dispara dp:analytics sin estar en el registro -> se detecta.
        (tmp / "assets" / "otro.js").write_text(
            "document.dispatchEvent(new CustomEvent('dp:analytics', {detail:{event:'x'}}));\n", encoding="utf-8",
        )
        errors = cat.check_article_bridge([tmp / "assets" / "otro.js"], tmp, REGISTRY["article_bridge"]["names_by_module"])
        check(any("otro.js" in e for e in errors), "fichero nuevo con dp:analytics sin registrar se detecta")

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-analytics-taxonomy: OK")


if __name__ == "__main__":
    run()
