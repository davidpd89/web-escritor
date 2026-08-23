#!/usr/bin/env python3
"""Verifica scripts/check-no-stale-contact-email.py con fixtures aislados
(2026-08-23).

Uso:
  python tests/test-check-no-stale-contact-email.py
"""
from __future__ import annotations

import io
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-no-stale-contact-email.py"

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def run_checker(tmp: Path, html: str) -> str:
    (tmp / "page.html").write_text(html, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp)
    subprocess.run(["git", "add", "-A"], cwd=tmp)
    subprocess.run(["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "x"], cwd=tmp)
    result = subprocess.run([sys.executable, str(CHECKER), "--root", str(tmp), "--check"], capture_output=True, text=True)
    return result.stdout


def run() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)

        # Negativo: email correcto -> sin error.
        out = run_checker(tmp, '<a href="mailto:davidportodiaz@gmail.com">davidportodiaz@gmail.com</a>')
        check("0 incumplimiento" in out, "email vigente no genera error", out)

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        # Positivo: texto visible con entidad HTML -> se detecta.
        out = run_checker(tmp, '<a href="mailto:davidportodiaz@gmail.com">samuelentremundos&#64;gmail.com</a>')
        check("samuelentremundos" in out, "email obsoleto con entidad HTML se detecta", out)

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        # Positivo: data-n con el local-part obsoleto -> se detecta (bug funcional real).
        out = run_checker(tmp, '<a href="mailto:davidportodiaz@gmail.com" data-n="samuelentremundos" data-d="gmail.com">Contactar</a>')
        check("samuelentremundos" in out, "data-n con local-part obsoleto se detecta", out)

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-no-stale-contact-email: OK")


if __name__ == "__main__":
    run()
