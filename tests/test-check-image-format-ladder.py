#!/usr/bin/env python3
"""Mutation tests del contrato AVIF/WebP de #67 (L.1, 2026-08-23).

Prueba procedencia por contenido, regeneracion y diagnosticos sin asumir
mtime ni dimensiones como señal de frescura.
"""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import PIL
from PIL import Image

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-image-format-ladder.py"
BUILDER = ROOT / "scripts" / "build-image-format-ladder.py"
QUALITY = 60
failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def html_ok(avif_name: str = "foto-320.avif") -> str:
    return (
        '<picture>'
        f'<source type="image/avif" media="(max-width:420px)" srcset="assets/{avif_name}">'
        '<source media="(max-width:420px)" srcset="assets/foto-320.webp">'
        f'<source type="image/avif" srcset="assets/{avif_name}">'
        '<img src="assets/foto-320.webp">'
        '</picture>'
    )


def write_manifest(tmp: Path) -> None:
    source = tmp / "assets" / "foto-320.webp"
    derivative = tmp / "assets" / "foto-320.avif"
    manifest = {
        "schema_version": 2,
        "encoder": {
            "format": "AVIF",
            "quality": QUALITY,
            "pillow_version": PIL.__version__,
        },
        "eligible_sources": [
            {
                "source": "assets/foto-320.webp",
                "derivative": "assets/foto-320.avif",
                "source_sha256": sha256_file(source),
                "derivative_sha256": sha256_file(derivative),
            }
        ],
    }
    (tmp / "data" / "image-format-ladder.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def make_repo(tmp: Path, html: str | None = None) -> None:
    (tmp / "data").mkdir(parents=True, exist_ok=True)
    (tmp / "assets").mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), "red").save(tmp / "assets" / "foto-320.webp", format="WEBP")
    Image.open(tmp / "assets" / "foto-320.webp").save(
        tmp / "assets" / "foto-320.avif", format="AVIF", quality=QUALITY
    )
    write_manifest(tmp)
    (tmp / "page.html").write_text(html or html_ok(), encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "-q", "-m", "fixture"],
        cwd=tmp,
        check=True,
    )


def run_tool(tool: Path, tmp: Path, check_only: bool = True) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(tool), "--root", str(tmp)]
    if check_only:
        command.append("--check")
    return subprocess.run(command, capture_output=True, text=True)


def run() -> None:
    # CASO A: fuente y derivada sincronizadas -> PASS.
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        make_repo(tmp)
        result = run_tool(CHECKER, tmp)
        check(result.returncode == 0 and "0 incumplimiento" in result.stdout, "A: pareja sincronizada pasa", result.stdout)
        build_check = run_tool(BUILDER, tmp)
        check(build_check.returncode == 0 and "0 error(es)" in build_check.stdout, "A: builder --check confirma frescura", build_check.stdout)

    # CASOS B/C: cambia el contenido del WebP manteniendo EXACTAMENTE 8x8.
    # B debe fallar por hash; C regenera solo esa derivada y vuelve a PASS.
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        make_repo(tmp)
        original_avif_hash = sha256_file(tmp / "assets" / "foto-320.avif")
        Image.new("RGB", (8, 8), "blue").save(tmp / "assets" / "foto-320.webp", format="WEBP")
        with Image.open(tmp / "assets" / "foto-320.webp") as image:
            check(image.size == (8, 8), "B: mutacion conserva dimensiones exactas")
        stale = run_tool(CHECKER, tmp)
        check(stale.returncode != 0 and "source_sha256 no coincide" in stale.stdout, "B: WebP mutado mismo tamaño falla por procedencia", stale.stdout)
        stale_builder = run_tool(BUILDER, tmp)
        check(stale_builder.returncode != 0 and "source_sha256 obsoleto" in stale_builder.stdout, "B: builder --check tambien bloquea fuente obsoleta", stale_builder.stdout)

        regenerated = run_tool(BUILDER, tmp, check_only=False)
        check(regenerated.returncode == 0 and "REGENERATED assets/foto-320.avif" in regenerated.stdout, "C: regeneracion corrige la pareja", regenerated.stdout)
        check(sha256_file(tmp / "assets" / "foto-320.avif") != original_avif_hash, "C: AVIF realmente cambia tras regenerar")
        fresh = run_tool(CHECKER, tmp)
        check(fresh.returncode == 0 and "0 incumplimiento" in fresh.stdout, "C: pareja regenerada vuelve a PASS", fresh.stdout)

    # CASO D1: falta fallback WebP -> diagnostico explicito.
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        make_repo(tmp)
        (tmp / "assets" / "foto-320.webp").unlink()
        result = run_tool(CHECKER, tmp)
        check(result.returncode != 0 and "fuente WebP no existe" in result.stdout, "D1: fallback WebP ausente se diagnostica", result.stdout)

    # CASO D2: falta derivada AVIF -> diagnostico explicito.
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        make_repo(tmp)
        (tmp / "assets" / "foto-320.avif").unlink()
        result = run_tool(CHECKER, tmp)
        check(result.returncode != 0 and "falta el AVIF hermano" in result.stdout, "D2: AVIF ausente se diagnostica", result.stdout)

    # Mutacion adicional: AVIF reemplazado por otro contenido con mismo 8x8.
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        make_repo(tmp)
        Image.new("RGB", (8, 8), "green").save(tmp / "assets" / "foto-320.avif", format="AVIF", quality=QUALITY)
        result = run_tool(CHECKER, tmp)
        check(result.returncode != 0 and "derivative_sha256 no coincide" in result.stdout, "AVIF reemplazado mismo tamaño falla por hash", result.stdout)

    # La escalera debe apuntar al hermano correspondiente, no a cualquier AVIF.
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        make_repo(tmp, html=html_ok("otro-320.avif"))
        Image.new("RGB", (8, 8), "red").save(tmp / "assets" / "otro-320.avif", format="AVIF", quality=QUALITY)
        result = run_tool(CHECKER, tmp)
        check(result.returncode != 0 and "AVIF precedente que no corresponde" in result.stdout, "AVIF de otra variante no satisface la escalera", result.stdout)

    # Mantener checks estructurales previos: media y dimensiones.
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        wrong_media = (
            '<picture><source type="image/avif" media="(max-width:999px)" srcset="assets/foto-320.avif">'
            '<source media="(max-width:420px)" srcset="assets/foto-320.webp">'
            '<source type="image/avif" srcset="assets/foto-320.avif"><img src="assets/foto-320.webp"></picture>'
        )
        make_repo(tmp, html=wrong_media)
        result = run_tool(CHECKER, tmp)
        check(result.returncode != 0 and "media='" in result.stdout, "media distinto AVIF/WebP se detecta", result.stdout)

    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        make_repo(tmp)
        Image.new("RGB", (16, 16), "red").save(tmp / "assets" / "foto-320.avif", format="AVIF", quality=QUALITY)
        result = run_tool(CHECKER, tmp)
        check(result.returncode != 0 and "dimensiones no coinciden" in result.stdout, "dimensiones de formatos distintas se detectan", result.stdout)

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-image-format-ladder: OK")


if __name__ == "__main__":
    run()
