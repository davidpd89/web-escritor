#!/usr/bin/env python3
"""Verifica scripts/check-noveris-magic-quarantine.py con fixtures
aislados (K.4, 2026-08-23).

Uso:
  python tests/test-check-noveris-magic-quarantine.py
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
_spec = importlib.util.spec_from_file_location("cnq", ROOT / "scripts" / "check-noveris-magic-quarantine.py")
cnq = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = cnq
_spec.loader.exec_module(cnq)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def write_page(tmp: Path, html: str) -> None:
    d = tmp / "cuaderno" / "sistema-de-magia-noveris"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(html, encoding="utf-8")


def run() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)

        # Negativo: pagina neutralizada y noindex -> 0 errores.
        write_page(tmp, '<meta name="robots" content="noindex, follow"><p>En revisión.</p>')
        errors_count = _run_and_count(tmp)
        check(errors_count == 0, "pagina neutralizada y noindex no genera error")

        # Positivo: deja de ser noindex -> se detecta.
        write_page(tmp, '<meta name="robots" content="index, follow"><p>En revisión.</p>')
        errors_count = _run_and_count(tmp)
        check(errors_count >= 1, "perder noindex mientras sigue en cuarentena se detecta")

        # Positivo: reaparece una afirmacion conflictiva conocida -> se detecta.
        write_page(tmp, '<meta name="robots" content="noindex, follow"><p>Cada canalización consume esa historia residual de forma irreversible.</p>')
        errors_count = _run_and_count(tmp)
        check(errors_count >= 1, "reaparicion de una afirmacion conflictiva conocida se detecta")

        # Positivo: reaparece FAQPage -> se detecta.
        write_page(tmp, '<meta name="robots" content="noindex, follow"><script>{"@type": "FAQPage"}</script>')
        errors_count = _run_and_count(tmp)
        check(errors_count >= 1, "reaparicion de FAQPage se detecta")

        # Positivo: URL en cuarentena aparece en sitemap.xml -> se detecta.
        write_page(tmp, '<meta name="robots" content="noindex, follow"><p>En revisión.</p>')
        (tmp / "sitemap.xml").write_text(
            "<urlset><url><loc>https://x/cuaderno/sistema-de-magia-noveris/</loc></url></urlset>", encoding="utf-8",
        )
        errors_count = _run_and_count(tmp)
        check(errors_count >= 1, "aparicion en sitemap.xml se detecta")

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-noveris-magic-quarantine: OK")


def _run_and_count(tmp: Path) -> int:
    import subprocess
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check-noveris-magic-quarantine.py"), "--root", str(tmp)],
        capture_output=True, text=True,
    )
    return result.stdout.count("ERROR ")


if __name__ == "__main__":
    run()
