#!/usr/bin/env python3
"""Build the home hero background (assets/manecillas-hero-bg.webp): a
heavily blurred, darkened, desaturated abstraction of the real Manecillas
cover. No AI generation, no legible text or recognizable objects, and
fully reproducible from a versioned input (the same tracked
1024x1536 cover every other Manecillas asset uses).

Usage:
  python scripts/build-manecillas-hero-bg.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
COVER = ROOT / "assets" / "portada-las-manecillas-del-recuerdo-1024.webp"
OUT = ROOT / "assets" / "manecillas-hero-bg.webp"
W, H = 1920, 1080


def main() -> None:
    cover = Image.open(COVER).convert("RGB")
    bg = ImageOps.fit(cover, (W * 2, H * 2), method=Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(70))
    bg = bg.resize((W, H), Image.LANCZOS)
    bg = ImageEnhance.Color(bg).enhance(0.82)
    bg = ImageEnhance.Brightness(bg).enhance(0.62)
    bg.save(OUT, quality=82, method=6)
    print(f"{OUT.name}: {bg.size} {OUT.stat().st_size / 1024:.1f} KiB")


if __name__ == "__main__":
    main()
