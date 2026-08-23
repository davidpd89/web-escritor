#!/usr/bin/env python3
"""Verifica scripts/check-recommendations-evidence.py con fixtures
aislados (K.1, 2026-08-23).

Uso:
  python tests/test-check-recommendations-evidence.py
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-recommendations-evidence.py"

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


EVIDENCE = {
    "works": [
        {"isbn": "1111111111", "title": "Libro registrado", "author": "X", "evidenceStatus": "verificado", "verifiedDate": "2026-08-23", "editionSource": "y", "factsSource": "z"},
        {"isbn": "2222222222", "title": "Obra propia", "author": "David Porto Díaz", "evidenceStatus": "leido", "verifiedDate": "2026-08-23", "editionSource": "y", "factsSource": "z"},
    ]
}


def make_repo(tmp: Path, guide_html: str, evidence: dict = EVIDENCE) -> None:
    (tmp / "data").mkdir(exist_ok=True)
    (tmp / "data" / "recommendations-evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    d = tmp / "recomendaciones" / "guia-test"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(guide_html, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp)
    subprocess.run(["git", "add", "-A"], cwd=tmp)
    subprocess.run(["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "x"], cwd=tmp)


def run_checker(tmp: Path) -> str:
    result = subprocess.run([sys.executable, str(CHECKER), "--root", str(tmp), "--check"], capture_output=True, text=True)
    return result.stdout


def run() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)

        # Negativo: ISBN registrado, sin contradicciones -> 0 errores.
        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">ISBN 1111111111</li>')
        out = run_checker(tmp)
        check("0 incumplimiento" in out, "entrada registrada y consistente no genera error", out)

        # Positivo: ISBN sin entrada en la autoridad -> se detecta.
        make_repo(tmp, '<li class="rec-item" data-isbn="9999999999">ISBN 9999999999</li>')
        out = run_checker(tmp)
        check("sin entrada" in out, "ISBN no registrado en la autoridad se detecta", out)

        # Positivo: HTML afirma "verificada" para un ISBN que la autoridad no respalda -> se detecta.
        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">Edición pendiente</li>', {
            "works": [{"isbn": "1111111111", "title": "x", "author": "y", "evidenceStatus": "pendiente"}]
        })
        out = run_checker(tmp)
        check("0 incumplimiento" in out, "estado pendiente sin afirmar verificado no genera error", out)

        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">Edición en español verificada</li>', {
            "works": [{"isbn": "1111111111", "title": "x", "author": "y", "evidenceStatus": "pendiente"}]
        })
        out = run_checker(tmp)
        check("afirma una edición verificada" in out, "HTML afirma verificado sin respaldo de la autoridad se detecta", out)

        # Positivo: rec-item--self sin evidenceStatus=leido -> se detecta.
        make_repo(tmp, '<li class="rec-item rec-item--self" data-isbn="1111111111">x</li>')
        out = run_checker(tmp)
        check("marcado como obra propia" in out, "obra propia sin evidenceStatus=leido se detecta", out)

        # Positivo: enlaces de afiliado sin affiliate-disclosure -> se detecta.
        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">ISBN 1111111111</li><a rel="nofollow sponsored">x</a>')
        out = run_checker(tmp)
        check("affiliate-disclosure" in out and "sin declarar" not in out, "afiliado sin affiliate-disclosure se detecta", out)

        # Positivo: evidenceStatus invalido en la autoridad -> se detecta.
        make_repo(tmp, '<li class="rec-item" data-isbn="1111111111">x</li>', {
            "works": [{"isbn": "1111111111", "title": "x", "author": "y", "evidenceStatus": "seguro-que-si"}]
        })
        out = run_checker(tmp)
        check("evidenceStatus inválido" in out, "evidenceStatus fuera del enum se detecta", out)

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-recommendations-evidence: OK")


if __name__ == "__main__":
    run()
