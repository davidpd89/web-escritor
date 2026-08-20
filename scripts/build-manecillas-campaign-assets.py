#!/usr/bin/env python3
"""Build the launch-campaign image assets for Las manecillas del recuerdo,
per WEB DAVID PORTO nuevas ideas/26_DISENOS_MANECILLAS_CON_PORTADA_REAL.md
("Assets que si hacen falta" > 2. Lanzamiento 4:5, 3. Stories/reels).

No AI generation: same deterministic approach as
scripts/build-manecillas-social-card.py — the real, versioned cover
composited unmodified, a Pillow blur/tint of that same cover as
background, real bundled fonts for any added text. Nothing is drawn
inside the cover artwork itself.

Produces:
  assets/manecillas-social-4x5-aviso.webp       (1080x1350) - "coming soon"
  assets/manecillas-social-4x5-disponible.webp  (1080x1350) - prepared for
      after the 2026-09-03 launch. NOT linked from any page yet — do not
      publish before the book is actually out.
  assets/manecillas-social-story-9x16.webp      (1080x1920) - stories/reels,
      cover kept out of the top/bottom safe-area bands reserved for
      platform UI.

Usage:
  python scripts/build-manecillas-campaign-assets.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
COVER = ROOT / "assets" / "portada-las-manecillas-del-recuerdo-1024.webp"
FONT_SERIF = ROOT / "assets" / "fonts" / "cg-normal-latin.woff2"
FONT_SANS = ROOT / "assets" / "fonts" / "inter-normal-latin.woff2"

TINTA = (0x17, 0x12, 0x0B)
NOGAL = (0x4C, 0x35, 0x1A)
BRONCE = (0x93, 0x66, 0x31)
ORO = (0xCF, 0x92, 0x46)
MARFIL = (0xF2, 0xE8, 0xD8)
MUTED = (0xB6, 0xA8, 0x94)


def blurred_bg(w: int, h: int) -> Image.Image:
    cover = Image.open(COVER).convert("RGB")
    bg = ImageOps.fit(cover, (w * 2, h * 2), method=Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(60))
    bg = bg.resize((w, h), Image.LANCZOS)
    tint = Image.new("RGB", (w, h), TINTA)
    grad = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(grad)
    for y in range(h):
        gd.line([(0, y), (w, y)], fill=int(60 + 90 * (y / h)))
    tint2 = Image.new("RGB", (w, h), NOGAL)
    tint = Image.composite(tint2, tint, grad)
    return Image.blend(bg, tint, 0.66)


def paste_cover_centered(bg: Image.Image, target_w: int, top: int) -> tuple[Image.Image, int, int]:
    cover = Image.open(COVER).convert("RGB")
    target_h = round(target_w * (cover.height / cover.width))
    cover_r = cover.resize((target_w, target_h), Image.LANCZOS)
    cx = (bg.width - target_w) // 2

    shadow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([cx - 12, top - 8, cx + target_w + 12, top + target_h + 22], radius=6, fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    bg = bg.convert("RGBA")
    bg.alpha_composite(shadow)
    bg.paste(cover_r, (cx, top))
    draw = ImageDraw.Draw(bg)
    draw.rectangle([cx, top, cx + target_w - 1, top + target_h - 1], outline=BRONCE + (200,), width=3)
    return bg.convert("RGB"), cx, target_h


def center_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, cx: int, y: int, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text((cx - w / 2, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]


def save(im: Image.Image, out: Path, cap_kib: int = 320) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    for q in (86, 82, 78, 74, 70):
        im.save(out, "WEBP", quality=q, method=6)
        size = out.stat().st_size
        if size <= cap_kib * 1024:
            print(f"{out.name}: {im.size} quality={q} {size / 1024:.1f} KiB")
            return
    print(f"{out.name}: {im.size} quality=70 {out.stat().st_size / 1024:.1f} KiB (over target, kept lowest tried)")


def build_4x5(variant: str) -> None:
    W, H = 1080, 1350
    bg = blurred_bg(W, H)
    cover_w = round(W * 0.50)  # cover occupies ~50% width -> within the documented 45-52%
    top = 150
    composed, cx, cover_h = paste_cover_centered(bg, cover_w, top)
    draw = ImageDraw.Draw(composed)
    center = W / 2

    eyebrow_font = ImageFont.truetype(str(FONT_SANS), 30)
    if variant == "aviso":
        eyebrow = "NUEVA NOVELA"
    else:
        eyebrow = "YA DISPONIBLE"
    center_text(draw, eyebrow, eyebrow_font, center, 62, ORO)

    title_font = ImageFont.truetype(str(FONT_SERIF), 64)
    y = top + cover_h + 48
    y += center_text(draw, "Las manecillas del recuerdo", title_font, center, y, MARFIL) + 14

    author_font = ImageFont.truetype(str(FONT_SANS), 34)
    y += 10
    y += center_text(draw, "David Porto Díaz", author_font, center, y, MARFIL) + 10

    meta_font = ImageFont.truetype(str(FONT_SANS), 26)
    meta_text = "Monza Ediciones · 3 de septiembre de 2026" if variant == "aviso" else "Monza Ediciones · Ya en librerías"
    center_text(draw, meta_text, meta_font, center, y, MUTED)

    out = ROOT / "assets" / f"manecillas-social-4x5-{variant}.webp"
    save(composed, out)


def build_story() -> None:
    W, H = 1080, 1920
    bg = blurred_bg(W, H)
    # Safe areas: keep essential content out of the top ~250px and bottom
    # ~260px, which platform UI (profile/reply bar) typically covers.
    cover_w = round(W * 0.62)
    top = 560
    composed, cx, cover_h = paste_cover_centered(bg, cover_w, top)
    draw = ImageDraw.Draw(composed)
    center = W / 2

    eyebrow_font = ImageFont.truetype(str(FONT_SANS), 34)
    center_text(draw, "NUEVA NOVELA · DAVID PORTO DÍAZ", eyebrow_font, center, 300, ORO)

    title_font = ImageFont.truetype(str(FONT_SERIF), 70)
    y = 380
    y += center_text(draw, "Las manecillas", title_font, center, y, MARFIL) + 10
    y += center_text(draw, "del recuerdo", title_font, center, y, MARFIL) + 10

    meta_font = ImageFont.truetype(str(FONT_SANS), 32)
    y2 = top + cover_h + 60
    center_text(draw, "Monza Ediciones", meta_font, center, y2, MARFIL)
    center_text(draw, "3 de septiembre de 2026", meta_font, center, y2 + 46, MUTED)

    out = ROOT / "assets" / "manecillas-social-story-9x16.webp"
    save(composed, out)


def main() -> None:
    build_4x5("aviso")
    build_4x5("disponible")
    build_story()


if __name__ == "__main__":
    main()
