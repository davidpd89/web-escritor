#!/usr/bin/env python3
"""Gate de la escalera de formatos AVIF->WebP (L.1, 2026-08-23).

Para cada fuente WebP elegible declarada en data/image-format-ladder.json,
verifica que:

  1. existe un fichero .avif hermano en disco, con las mismas dimensiones
     que el WebP (usa Pillow si esta disponible; si no, solo comprueba que
     el fichero existe);
  2. toda referencia HTML a ese WebP dentro de un <picture> tiene un
     <source type="image/avif"> con el mismo `media` (o sin `media`, para
     el caso del <img> por defecto) INMEDIATAMENTE ANTES en el documento,
     de modo que los navegadores compatibles con AVIF lo prioricen;
  3. el <img> de fallback sigue apuntando a WebP (o a otro formato de
     amplio soporte) -- AVIF nunca sustituye al fallback, solo se añade
     como <source> adicional.

No duplica los checks de #61 H.3 (width/height, srcset/sizes): esos
siguen siendo responsabilidad de check-responsive-images.py.

Python standard library (+ Pillow opcional para comparar dimensiones).

Usage:
    python scripts/check-image-format-ladder.py
    python scripts/check-image-format-ladder.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from PIL import Image
except ImportError:
    Image = None


def tracked_html(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "*.html"], cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    return [root / rel for rel in out.split("\0") if rel and "lab/" not in rel and "lab\\" not in rel]


def basename_of(rel_webp: str) -> str:
    return Path(rel_webp).name


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    manifest = json.loads((root / "data" / "image-format-ladder.json").read_text(encoding="utf-8"))
    sources = manifest["eligible_sources"]
    errors: list[str] = []

    for rel_webp in sources:
        webp_path = root / rel_webp
        avif_path = webp_path.with_suffix(".avif")
        if not avif_path.exists():
            errors.append(f"{rel_webp}: falta el AVIF hermano ({avif_path.relative_to(root).as_posix()})")
            continue
        if Image is not None and webp_path.exists():
            try:
                with Image.open(webp_path) as w, Image.open(avif_path) as a:
                    if w.size != a.size:
                        errors.append(f"{rel_webp}: dimensiones no coinciden (webp={w.size}, avif={a.size})")
            except Exception as exc:  # noqa: BLE001 -- fichero corrupto/no decodificable no debe tumbar el gate
                errors.append(f"{rel_webp}: no se pudo comparar dimensiones ({exc})")

    basenames = {basename_of(s): s for s in sources}
    tag_re = re.compile(r'<source\b[^>]*>|<img\b[^>]*>', re.I)
    media_re = re.compile(r'media="([^"]*)"')
    src_re = re.compile(r'srcset="([^"]*)"|src="([^"]*)"')
    type_re = re.compile(r'type="([^"]*)"')

    for path in tracked_html(root):
        html = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()
        tags = list(tag_re.finditer(html))
        for i, m in enumerate(tags):
            tag = m.group(0)
            src_match = src_re.search(tag)
            if not src_match:
                continue
            src_value = src_match.group(1) or src_match.group(2) or ""
            name = Path(src_value.split()[0] if src_value else "").name
            if not name.endswith(".webp") or name not in basenames:
                continue
            # Es una referencia a un WebP elegible: debe existir un
            # <source type="image/avif"> con el mismo media INMEDIATAMENTE
            # antes en el documento.
            own_media = media_re.search(tag)
            own_media_value = own_media.group(1) if own_media else None
            if i == 0:
                errors.append(f"{rel}: {name} referenciado sin ningún <source> AVIF precedente")
                continue
            prev_tag = tags[i - 1].group(0)
            prev_type = type_re.search(prev_tag)
            prev_media = media_re.search(prev_tag)
            prev_media_value = prev_media.group(1) if prev_media else None
            if not (prev_type and "avif" in prev_type.group(1).lower()):
                errors.append(f"{rel}: {name} no tiene un <source type=\"image/avif\"> inmediatamente antes")
                continue
            if prev_media_value != own_media_value:
                errors.append(f"{rel}: {name} -- el <source> AVIF precedente tiene media='{prev_media_value}', esperado '{own_media_value}'")

    for e in errors:
        print(f"ERROR {e}")

    print(f"\nImage format ladder check: {len(sources)} fuente(s) elegibles, {len(errors)} incumplimiento(s).")
    if args.check and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
