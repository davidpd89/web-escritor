#!/usr/bin/env python3
"""Regresion (item 18 de la ronda 2026-09): ninguna imagen JPG/PNG/WebP
PUBLICADA debe llevar EXIF ni chunks de texto (tEXt/iTXt) -- GPS, marca y
modelo de camara, software, nombre de usuario del equipo o rutas locales
son datos que un lector no espera que vengan pegados a una foto de una
web publica.

Estado encontrado: limpio. Solo 2 archivos en todo el repositorio llevan
EXIF (resolution unit/orientation basicos, sin GPS ni software), y ambos
viven en assets/no usadas/, una carpeta explicitamente excluida del build
publico (scripts/build-public-dist.py) y confirmada con 404 en produccion.
Este test excluye esa carpeta a proposito -- lo que protege es que ninguna
imagen que SI se publique lleve metadata, no que el archivo fuente interno
este completamente vacio de EXIF.

Uso:
  python tests/test-no-image-metadata.py
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PREFIXES = ("lab/", "assets/no usadas/", "tests/", "data/", "scripts/", ".claude/")

# Format-mechanics keys Pillow surfaces via .info that are not embedded
# human-readable metadata -- these are universal to the JPEG/PNG formats
# themselves (JFIF header fields every basic JPEG has, the PNG sRGB
# rendering-intent chunk) or are non-identifying tool-version boilerplate
# (ffmpeg's libavcodec COM segment on JPEGs extracted from a video frame,
# confirmed to contain only "Lavc62.28.102\x00" -- no path, no username, no
# camera/GPS data). None of this is what item 18 is checking for.
BENIGN_INFO_KEYS = {
    "dpi", "transparency", "gamma", "aspect", "loop", "duration", "background", "icc_profile",
    "jfif", "jfif_version", "jfif_unit", "jfif_density", "srgb",
}
# A JPEG COM segment naming only the encoder (e.g. ffmpeg's libavcodec) is
# fine; one containing anything else (a path, a username, a real comment)
# is exactly what this test should catch.
BENIGN_COMMENT_RE = re.compile(rb"^Lavc[\d.]+\x00?$")

tracked = subprocess.run(
    ["git", "-c", "core.quotepath=false", "ls-files", "-z", "*.jpg", "*.jpeg", "*.png", "*.webp"],
    cwd=ROOT, capture_output=True, check=True,
).stdout.decode("utf-8").split("\0")

failures: list[str] = []
checked = 0
for rel in tracked:
    rel = rel.strip()
    if not rel or rel.startswith(EXCLUDED_PREFIXES):
        continue
    path = ROOT / rel
    try:
        with Image.open(path) as img:
            checked += 1
            exif = img.getexif()
            if exif and len(exif) > 0:
                failures.append(f"{rel}: carries EXIF data ({len(exif)} tag(s))")
            leaked_info = {k: v for k, v in img.info.items() if k not in BENIGN_INFO_KEYS}
            comment = leaked_info.pop("comment", None)
            if comment is not None and not BENIGN_COMMENT_RE.match(comment if isinstance(comment, bytes) else str(comment).encode()):
                failures.append(f"{rel}: JPEG comment is not the known-benign encoder tag: {comment!r}")
            if leaked_info:
                failures.append(f"{rel}: carries text metadata: {list(leaked_info.keys())}")
    except Exception as exc:  # noqa: BLE001 - report and continue
        failures.append(f"{rel}: could not open ({exc})")

print(f"tests/test-no-image-metadata: checked {checked} published image(s)")
if failures:
    for f in failures:
        print(f"  FAIL {f}")
    print(f"tests/test-no-image-metadata: {len(failures)} FALLO(S)")
else:
    print("  ok   no published image carries EXIF or text metadata")
    print("tests/test-no-image-metadata: OK")
raise SystemExit(1 if failures else 0)
