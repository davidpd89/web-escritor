#!/usr/bin/env python3
"""Build the horizontal (1200x630, ~1.91:1) Open Graph social card for
Las manecillas del recuerdo.

Per WEB DAVID PORTO nuevas ideas/26_DISENOS_MANECILLAS_CON_PORTADA_REAL.md
("Assets que si hacen falta" > "1. Open Graph horizontal"):
  - cubierta real a la derecha, sin deformar;
  - titulo y autor como texto vectorial (real fonts), no generacion IA;
  - fondo creado a partir de una ampliacion desenfocada de la propia cubierta;
  - menos de 300 KiB.

This never asks an image-generation model to touch the cover or invent
text: the cover pixels are used exactly as published, and the background
is a purely local blur/tint transform of those same pixels (Pillow only,
no network call). Title/author/editorial text is drawn with the site's
own bundled fonts (assets/fonts/*.woff2 - Pillow can rasterize woff2
directly via FreeType).

Usage:
  python scripts/build-manecillas-social-card.py
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
# Versioned input: the same 1024x1536 cover already tracked in git and used
# sitewide (index.html, /libros/, etc.), NOT the gitignored lossless PNG
# master under assets/manecillas/source/ — that master is a local-only
# convenience copy, so building from it would make this script
# non-reproducible from a clean checkout. Versioned input + this builder
# = reproducible output, per project convention.
COVER = ROOT / "assets" / "portada-las-manecillas-del-recuerdo-1024.webp"
OUT = ROOT / "assets" / "og-manecillas.webp"

FONT_SERIF = ROOT / "assets" / "fonts" / "cg-normal-latin.woff2"  # Cormorant Garamond
FONT_SANS = ROOT / "assets" / "fonts" / "inter-normal-latin.woff2"  # Inter

W, H = 1200, 630

# Palette from 26_DISENOS_MANECILLAS_CON_PORTADA_REAL.md
TINTA = (0x17, 0x12, 0x0B)
NOGAL = (0x4C, 0x35, 0x1A)
BRONCE = (0x93, 0x66, 0x31)
COBRE = (0xC2, 0x79, 0x37)
ORO = (0xCF, 0x92, 0x46)
MARFIL = (0xF2, 0xE8, 0xD8)


def make_background() -> Image.Image:
    """Blurred, tinted enlargement of the cover itself - no AI, no new
    objects, no text, no reinterpretation - per the documented technique."""
    cover = Image.open(COVER).convert("RGB")
    # Fill-crop cover to the card's aspect ratio, then scale well past
    # target size before blurring for a soft, non-pixelated result.
    bg = ImageOps.fit(cover, (W * 2, H * 2), method=Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(46))
    bg = bg.resize((W, H), Image.LANCZOS)

    # Tint toward the documented palette (Tinta -> Nogal diagonal) so the
    # background reads as an abstract editorial surface, not a legible
    # miniature of the cover competing with the real cover on the right.
    tint = Image.new("RGB", (W, H), TINTA)
    grad = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(grad)
    for x in range(W):
        # left = darker (more Tinta), right = slightly warmer (more Nogal)
        gd.line([(x, 0), (x, H)], fill=int(70 + 90 * (x / W)))
    tint2 = Image.new("RGB", (W, H), NOGAL)
    tint = Image.composite(tint2, tint, grad)
    bg = Image.blend(bg, tint, 0.62)

    # Darken further on the left two-thirds so the title/author text has
    # guaranteed contrast, and vignette the edges slightly for an
    # editorial, non-flat surface.
    dark_mask = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(dark_mask)
    for x in range(W):
        v = 150 if x < W * 0.62 else int(150 * max(0, 1 - (x - W * 0.62) / (W * 0.38)))
        dm.line([(x, 0), (x, H)], fill=v)
    dark_layer = Image.new("RGB", (W, H), TINTA)
    bg = Image.composite(dark_layer, bg, dark_mask)

    return bg


def paste_cover(bg: Image.Image) -> Image.Image:
    cover = Image.open(COVER).convert("RGB")
    target_h = H - 70  # top/bottom margin
    target_w = round(target_h * (cover.width / cover.height))
    cover_r = cover.resize((target_w, target_h), Image.LANCZOS)

    # Soft drop shadow behind the cover (code-drawn, not AI).
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    margin_right = 56
    cx = W - margin_right - target_w
    cy = (H - target_h) // 2
    sd.rounded_rectangle(
        [cx - 10, cy - 6, cx + target_w + 18, cy + target_h + 18],
        radius=6, fill=(0, 0, 0, 130),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    bg = bg.convert("RGBA")
    bg.alpha_composite(shadow)

    # Thin bronze edge line, code-drawn (per the "componentes de codigo, no
    # imagenes" rule: borde fino de bronce is a CSS/code element even here).
    bg.paste(cover_r, (cx, cy))
    draw = ImageDraw.Draw(bg)
    draw.rectangle([cx, cy, cx + target_w - 1, cy + target_h - 1], outline=BRONCE + (200,), width=2)

    return bg.convert("RGB"), cx


def draw_text(im: Image.Image, cover_x: int) -> Image.Image:
    draw = ImageDraw.Draw(im)
    left = 70
    max_text_w = cover_x - 40 - left

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
    draw.text((left, 96), "NUEVA NOVELA · DAVID PORTO DÍAZ", font=eyebrow_font, fill=ORO)

    # Title: two lines, Cormorant Garamond, marfil.
    title_font = fit_font(FONT_SERIF, "Las manecillas del recuerdo", 68, 40, max_text_w)
    line1, line2 = "Las manecillas", "del recuerdo"
    draw.text((left, 140), line1, font=title_font, fill=MARFIL)
    draw.text((left, 140 + title_font.size + 6), line2, font=title_font, fill=MARFIL)

    # Thin bronze rule under the title.
    rule_y = 140 + (title_font.size + 6) * 2 + 20
    draw.line([(left, rule_y), (left + 96, rule_y)], fill=BRONCE, width=2)

    # Author.
    author_font = ImageFont.truetype(str(FONT_SANS), 27)
    draw.text((left, rule_y + 22), "David Porto Díaz", font=author_font, fill=MARFIL)

    # Editorial / date line.
    meta_font = ImageFont.truetype(str(FONT_SANS), 21)
    draw.text((left, rule_y + 22 + 38), "Monza Ediciones · Septiembre de 2026", font=meta_font, fill=(0xB6, 0xA8, 0x94))

    return im


def main() -> None:
    bg = make_background()
    composed, cover_x = paste_cover(bg)
    final = draw_text(composed, cover_x)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    for q in (86, 82, 78, 74):
        final.save(OUT, "WEBP", quality=q, method=6)
        size = OUT.stat().st_size
        if size <= 300 * 1024:
            print(f"Saved {OUT} at quality={q}: {size} bytes ({size/1024:.1f} KiB)")
            return
    print(f"WARNING: could not get under 300 KiB even at quality=74 ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
