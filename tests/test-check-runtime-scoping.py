#!/usr/bin/env python3
"""Verifica scripts/check-runtime-scoping.py contra un repo git de fixture
aislado: confirma que detecta cada una de las 3 violaciones que existian
antes de H.1 (2026-08-23) y que un repo correctamente scoped pasa limpio.

Uso:
  python tests/test-check-runtime-scoping.py
"""
from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("crs", ROOT / "scripts" / "check-runtime-scoping.py")
crs = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = crs
_spec.loader.exec_module(crs)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def git_init(tmp: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "fixture"],
        cwd=tmp, check=True,
    )


def base_pages(tmp: Path) -> None:
    (tmp / "script.js").write_text("console.log('core');\n", encoding="utf-8")
    (tmp / "cuaderno").mkdir()
    (tmp / "recomendaciones").mkdir()
    (tmp / "libros").mkdir()
    (tmp / "index.html").write_text('<html><body></body></html>', encoding="utf-8")


def run() -> None:
    # Caso 1: todo correctamente scoped -> PASS.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        base_pages(tmp)
        (tmp / "cuaderno" / "index.html").write_text(
            '<html><body><script src="/script.js"></script>'
            '<script src="/assets/newsletter-popup.js"></script>'
            '<link href="/assets/newsletter-popup.css">'
            '</body></html>', encoding="utf-8",
        )
        (tmp / "libros" / "index.html").write_text(
            '<html><body><button data-buy-modal></button>'
            '<script src="/assets/samuel-buy-modal.js"></script>'
            '</body></html>', encoding="utf-8",
        )
        git_init(tmp)
        pages = crs.tracked_html(tmp)
        errors = crs.check_script_js(tmp) + crs.check_buy_modal_scope(tmp, pages) + crs.check_popup_scope(tmp, pages)
        check(errors == [], "repo correctamente scoped no reporta errores", str(errors))

    # Caso 2: popup reimplementado dentro de script.js -> detectado.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        base_pages(tmp)
        (tmp / "script.js").write_text('overlay.id = "nl-popup-overlay";\n', encoding="utf-8")
        git_init(tmp)
        errors = crs.check_script_js(tmp)
        check(any("popup" in e for e in errors), "popup reimplementado en script.js se detecta")

    # Caso 3: modal de Samuel reimplementado dentro de script.js -> detectado.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        base_pages(tmp)
        (tmp / "script.js").write_text('d.id = "buy-dialog";\n', encoding="utf-8")
        git_init(tmp)
        errors = crs.check_script_js(tmp)
        check(any("Samuel" in e for e in errors), "modal de Samuel reimplementado en script.js se detecta")

    # Caso 4: pagina con [data-buy-modal] pero SIN cargar samuel-buy-modal.js -> detectado.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        base_pages(tmp)
        (tmp / "libros" / "index.html").write_text(
            '<html><body><button data-buy-modal></button></body></html>', encoding="utf-8",
        )
        git_init(tmp)
        pages = crs.tracked_html(tmp)
        errors = crs.check_buy_modal_scope(tmp, pages)
        check(any("no carga" in e for e in errors), "trigger sin script del modal se detecta")

    # Caso 5: pagina fuera de ambito cargando el popup de mas -> detectado.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        base_pages(tmp)
        (tmp / "index.html").write_text(
            '<html><body><script src="/script.js"></script>'
            '<script src="/assets/newsletter-popup.js"></script>'
            '</body></html>', encoding="utf-8",
        )
        git_init(tmp)
        pages = crs.tracked_html(tmp)
        errors = crs.check_popup_scope(tmp, pages)
        check(any("fuera de ambito" in e for e in errors), "popup cargado fuera de ambito se detecta")

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-runtime-scoping: OK")


if __name__ == "__main__":
    run()
