#!/usr/bin/env python3
"""Build the horizontal (1200x630) Open Graph social card for the home page,
using the author's own portrait instead of the book cover -- more personal
for a bare-domain share, where the book-specific card reads oddly.

Same technique as build-manecillas-social-card.py: real photo pixels used
as published (no AI redraw), background is a local blur/tint of the same
photo, title/author text drawn with the site's own bundled fonts. JPEG,
not WEBP -- WhatsApp's link-preview crawler doesn't reliably render WEBP
og:image thumbnails.

Usage:
  python scripts/build-home-social-card.py
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PORTRAIT = ROOT / "assets" / "david-porto-sol.jpg"
OUT = ROOT / "assets" / "og-david-porto-sol.jpg"

FONT_SERIF = ROOT / "assets" / "fonts" / "cg-normal-latin.woff2"  # Cormorant Garamond
FONT_SANS = ROOT / "assets" / "fonts" / "inter-normal-latin.woff2"  # Inter

W, H = 1200, 630
PORTRAIT_W = 520  # right-hand photo panel

TINTA = (0x17, 0x12, 0x0B)
BRONCE = (0x93, 0x66, 0x31)
ORO = (0xCF, 0x92, 0x46)
MARFIL = (0xF2, 0xE8, 0xD8)


def make_background(portrait: Image.Image) -> Image.Image:
    """Blurred, tinted enlargement of the portrait itself -- same technique
    as the Manecillas card's cover-derived background."""
    bg = ImageOps.fit(portrait, (W * 2, H * 2), method=Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    tint = Image.new("RGB", bg.size, TINTA)
    bg = Image.blend(bg, tint, 0.72)
    bg = ImageOps.fit(bg, (W, H), method=Image.LANCZOS)
    return bg


def paste_portrait(bg: Image.Image, portrait: Image.Image) -> int:
    """Fit-crop the real portrait into the right-hand panel, full bleed to
    the card's top/bottom/right edges. Returns the panel's left edge x."""
    px = W - PORTRAIT_W
    panel = ImageOps.fit(portrait, (PORTRAIT_W, H), method=Image.LANCZOS)
    bg.paste(panel, (px, 0))
    # Soft gradient seam so the photo doesn't hard-cut against the text panel.
    seam_w = 90
    seam = Image.new("L", (seam_w, H), 0)
    for x in range(seam_w):
        seam.putpixel((x, 0), int(255 * (x / seam_w)))
    seam = seam.resize((seam_w, H))
    dark = Image.new("RGB", (seam_w, H), TINTA)
    bg.paste(dark, (px - seam_w // 2, 0), seam.point(lambda v: 255 - v))
    return px


def draw_text(im: Image.Image, panel_x: int) -> Image.Image:
    draw = ImageDraw.Draw(im)
    left = 70
    max_text_w = panel_x - 40 - left

    def fit_font(path, text, start_size, min_size, max_w):
        size = start_size
        while size > min_size:
            f = ImageFont.truetype(str(path), size)
            w = draw.textbbox((0, 0), text, font=f)[2]
            if w <= max_w:
                return f
            size -= 2
        return ImageFont.truetype(str(path), min_size)

    eyebrow_font = ImageFont.truetype(str(FONT_SANS), 21)
    draw.text((left, 150), "ESCRITOR", font=eyebrow_font, fill=ORO)

    title_font = fit_font(FONT_SERIF, "David Porto Díaz", 72, 44, max_text_w)
    draw.text((left, 190), "David Porto Díaz", font=title_font, fill=MARFIL)

    rule_y = 190 + title_font.size + 34
    draw.line([(left, rule_y), (left + 96, rule_y)], fill=BRONCE, width=2)

    book_font = ImageFont.truetype(str(FONT_SANS), 25)
    draw.text((left, rule_y + 22), "Las manecillas del recuerdo", font=book_font, fill=MARFIL)

    meta_font = ImageFont.truetype(str(FONT_SANS), 21)
    draw.text((left, rule_y + 22 + 34), "Monza Ediciones · 3 de septiembre de 2026", font=meta_font, fill=(0xB6, 0xA8, 0x94))

    return im


def main() -> None:
    portrait = Image.open(PORTRAIT).convert("RGB")
    bg = make_background(portrait)
    panel_x = paste_portrait(bg, portrait)
    final = draw_text(bg, panel_x)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    for q in (88, 84, 80, 76):
        final.save(OUT, "JPEG", quality=q, optimize=True)
        size = OUT.stat().st_size
        if size <= 300 * 1024:
            print(f"Saved {OUT} at quality={q}: {size} bytes ({size/1024:.1f} KiB)")
            return
    print(f"WARNING: could not get under 300 KiB even at quality=76 ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
