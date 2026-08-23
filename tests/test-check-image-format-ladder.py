#!/usr/bin/env python3
"""Verifica scripts/check-image-format-ladder.py con fixtures aislados
(L.1, 2026-08-23).

Uso:
  python tests/test-check-image-format-ladder.py
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
CHECKER = ROOT / "scripts" / "check-image-format-ladder.py"

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def make_repo(tmp: Path, html: str, with_avif: bool = True) -> None:
    from PIL import Image

    (tmp / "data").mkdir(exist_ok=True)
    (tmp / "assets").mkdir(exist_ok=True)
    (tmp / "data" / "image-format-ladder.json").write_text(
        json.dumps({"eligible_sources": ["assets/foto-320.webp"]}), encoding="utf-8",
    )
    Image.new("RGB", (4, 4), "red").save(tmp / "assets" / "foto-320.webp", format="WEBP")
    avif_path = tmp / "assets" / "foto-320.avif"
    if with_avif:
        Image.new("RGB", (4, 4), "red").save(avif_path, format="AVIF")
    elif avif_path.exists():
        avif_path.unlink()
    (tmp / "page.html").write_text(html, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp)
    subprocess.run(["git", "add", "-A"], cwd=tmp)
    subprocess.run(["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "x"], cwd=tmp)


def run_checker(tmp: Path) -> str:
    result = subprocess.run([sys.executable, str(CHECKER), "--root", str(tmp), "--check"], capture_output=True, text=True)
    return result.stdout


def run() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)

        # Negativo: AVIF existe y el <source> AVIF precede correctamente -> sin error.
        # (Sigue el patron real del sitio: un <source avif> con media antes del
        # <source webp> con el mismo media, y otro <source avif> sin media
        # justo antes del <img> de fallback.)
        html_ok = (
            '<picture>'
            '<source type="image/avif" media="(max-width:420px)" srcset="assets/foto-320.avif">'
            '<source media="(max-width:420px)" srcset="assets/foto-320.webp">'
            '<source type="image/avif" srcset="assets/foto-320.avif">'
            '<img src="assets/foto-320.webp">'
            '</picture>'
        )
        make_repo(tmp, html_ok)
        out = run_checker(tmp)
        check("0 incumplimiento" in out, "AVIF presente y bien ordenado no genera error", out)

        # Positivo: falta el fichero AVIF en disco -> se detecta.
        make_repo(tmp, html_ok, with_avif=False)
        out = run_checker(tmp)
        check("falta el AVIF hermano" in out, "AVIF ausente en disco se detecta", out)

        # Positivo: el WebP se referencia sin ningún <source> AVIF precedente -> se detecta.
        html_missing_source = '<picture><source media="(max-width:420px)" srcset="assets/foto-320.webp"><img src="assets/foto-320.webp"></picture>'
        make_repo(tmp, html_missing_source)
        out = run_checker(tmp)
        check("sin ningún" in out or "no tiene un" in out, "WebP sin <source> AVIF precedente se detecta", out)

        # Positivo: el <source> AVIF precedente tiene un media distinto -> se detecta.
        html_wrong_media = '<picture><source type="image/avif" media="(max-width:999px)" srcset="assets/foto-320.avif"><source media="(max-width:420px)" srcset="assets/foto-320.webp"><img src="assets/foto-320.webp"></picture>'
        make_repo(tmp, html_wrong_media)
        out = run_checker(tmp)
        check("media='" in out, "media distinto entre AVIF y WebP se detecta", out)

        # Positivo: dimensiones AVIF/WebP distintas -> se detecta.
        from PIL import Image
        make_repo(tmp, html_ok)
        Image.new("RGB", (8, 8), "blue").save(tmp / "assets" / "foto-320.avif", format="AVIF")
        out = run_checker(tmp)
        check("dimensiones no coinciden" in out, "dimensiones AVIF/WebP distintas se detectan", out)

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-image-format-ladder: OK")


if __name__ == "__main__":
    run()
