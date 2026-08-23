#!/usr/bin/env python3
"""Pipeline de escalera de formatos AVIF -> WebP (L.1, 2026-08-23).

Convierte, para las imagenes raster PUBLICAS ELEGIBLES declaradas en
data/image-format-ladder.json, un WebP existente en su AVIF equivalente
(mismo nombre base, extension .avif), preservando dimensiones exactas.
No genera WebP: el WebP de origen ya es el fallback obligatorio.

Politica de elegibilidad (ver tambien docs/formato-imagenes-avif-webp.md):
  - Solo superficies explicitamente listadas en
    data/image-format-ladder.json ("eligible_sources"). No se convierte
    /assets/ de forma indiscriminada.
  - Excluye por diseno: assets sociales/OG (deben mantener una URL WebP/PNG
    estable para compatibilidad de scrapers externos que no soportan
    AVIF), materiales de trabajo, imagenes no publicadas.
  - AVIF NUNCA sustituye al WebP: siempre se añade como <source> adicional
    con prioridad, con el <img> WebP existente intacto como fallback.

Usage:
    python scripts/build-image-format-ladder.py           # genera los que falten
    python scripts/build-image-format-ladder.py --check   # no escribe; falla si falta alguno
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from PIL import Image
except ImportError:
    Image = None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true", help="no escribe; falla si falta algun AVIF")
    ap.add_argument("--quality", type=int, default=60, help="calidad AVIF (0-100)")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    manifest = json.loads((root / "data" / "image-format-ladder.json").read_text(encoding="utf-8"))
    sources = manifest["eligible_sources"]

    missing: list[str] = []
    generated: list[str] = []

    for rel_webp in sources:
        webp_path = root / rel_webp
        avif_path = webp_path.with_suffix(".avif")
        if avif_path.exists():
            continue
        if not webp_path.exists():
            missing.append(f"{rel_webp}: fuente WebP no existe")
            continue
        if args.check:
            missing.append(f"{rel_webp}: falta {avif_path.relative_to(root).as_posix()}")
            continue
        if Image is None:
            missing.append(f"{rel_webp}: Pillow no disponible para generar AVIF")
            continue
        with Image.open(webp_path) as im:
            im = im.convert("RGB") if im.mode in ("P", "CMYK") else im
            im.save(avif_path, format="AVIF", quality=args.quality)
        generated.append(avif_path.relative_to(root).as_posix())

    for g in generated:
        print(f"GENERATED {g}")
    for m in missing:
        print(f"ERROR {m}")

    print(f"\nFormat ladder: {len(sources)} fuente(s) elegibles, {len(generated)} generado(s), {len(missing)} pendiente(s)/error(es).")
    if missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
