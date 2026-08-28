#!/usr/bin/env python3
"""Build the horizontal (1200x630) Open Graph social card for the home page,
using the author's own portrait instead of the book cover -- more personal
for a bare-domain share, where the book-specific card reads oddly.

Full-bleed photo, not a side panel: the face sits centered in the frame with
text on a bottom gradient scrim. A previous version confined the photo to a
520px right-hand panel, which meant WhatsApp's own (much tighter, roughly
square) preview crop -- unlike Facebook/Twitter's wider crop -- showed mostly
the blurred left panel and cut the face off. A centered, full-bleed photo
survives any reasonable crop window instead of only the 1.91:1 one.

Same technique as build-manecillas-social-card.py: real photo pixels used
as published (no AI redraw), title/author text drawn with the site's own
bundled fonts. JPEG, not WEBP -- WhatsApp's link-preview crawler doesn't
reliably render WEBP og:image thumbnails.

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

TINTA = (0x17, 0x12, 0x0B)
BRONCE = (0x93, 0x66, 0x31)
ORO = (0xCF, 0x92, 0x46)
MARFIL = (0xF2, 0xE8, 0xD8)


def make_background(portrait: Image.Image) -> Image.Image:
    """Blurred, tinted enlargement of the portrait itself, as atmosphere
    behind the sharp centered photo -- same technique as the Manecillas
    card's cover-derived background."""
    bg = ImageOps.fit(portrait, (W * 2, H * 2), method=Image.LANCZOS, centering=(0.5, 0.3))
    bg = bg.filter(ImageFilter.GaussianBlur(50))
    tint = Image.new("RGB", bg.size, TINTA)
    bg = Image.blend(bg, tint, 0.6)
    bg = ImageOps.fit(bg, (W, H), method=Image.LANCZOS)
    return bg


def paste_portrait(bg: Image.Image, portrait: Image.Image) -> Image.Image:
    """Sharp portrait, centered horizontally, feathered into the blurred
    background -- not confined to a side panel, so the face is centered in
    the frame and survives any crop window (WhatsApp's tight square
    included), unlike the wide 1.91:1-only layout this replaces."""
    photo_h = 560
    photo_w = round(photo_h * portrait.width / portrait.height)
    panel = ImageOps.fit(portrait, (photo_w, photo_h), method=Image.LANCZOS, centering=(0.5, 0.22))
    px = (W - photo_w) // 2

    feather = 60
    mask = Image.new("L", (photo_w, photo_h), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rectangle([feather, feather, photo_w - 1 - feather, photo_h - 1 - feather], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(feather / 2))

    bg.paste(panel, (px, 0), mask)
    return bg


def add_scrim(bg: Image.Image) -> Image.Image:
    """Bottom gradient scrim for text legibility, without hiding the face."""
    scrim_h = 320
    gradient = Image.new("L", (1, scrim_h), 0)
    for y in range(scrim_h):
        gradient.putpixel((0, y), int(235 * (y / scrim_h) ** 1.4))
    gradient = gradient.resize((W, scrim_h))
    dark = Image.new("RGB", (W, scrim_h), TINTA)
    bg.paste(dark, (0, H - scrim_h), gradient)
    return bg


def draw_text(im: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(im)
    left = 70

    def fit_font(path, text, start_size, min_size, max_w):
        size = start_size
        while size > min_size:
            f = ImageFont.truetype(str(path), size)
            w = draw.textbbox((0, 0), text, font=f)[2]
            if w <= max_w:
                return f
            size -= 2
        return ImageFont.truetype(str(path), min_size)

    max_text_w = W - left - 60

    eyebrow_font = ImageFont.truetype(str(FONT_SANS), 20)
    eyebrow_y = H - 232
    draw.text((left, eyebrow_y), "ESCRITOR", font=eyebrow_font, fill=ORO)

    title_font = fit_font(FONT_SERIF, "David Porto Díaz", 62, 40, max_text_w)
    title_y = eyebrow_y + 32
    draw.text((left, title_y), "David Porto Díaz", font=title_font, fill=MARFIL)

    rule_y = title_y + title_font.size + 26
    draw.line([(left, rule_y), (left + 96, rule_y)], fill=BRONCE, width=2)

    book_font = ImageFont.truetype(str(FONT_SANS), 24)
    draw.text((left, rule_y + 18), "Las manecillas del recuerdo", font=book_font, fill=MARFIL)

    meta_font = ImageFont.truetype(str(FONT_SANS), 20)
    draw.text((left, rule_y + 18 + 32), "Monza Ediciones · 3 de septiembre de 2026", font=meta_font, fill=(0xB6, 0xA8, 0x94))

    return im


def main() -> None:
    portrait = Image.open(PORTRAIT).convert("RGB")
    bg = make_background(portrait)
    bg = paste_portrait(bg, portrait)
    bg = add_scrim(bg)
    final = draw_text(bg)

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
