#!/usr/bin/env python3
"""Build the horizontal (1200x630) Open Graph card for /al-otro-lado/.

La portada de la antología es vertical (840x1192). Servida tal cual como
og:image en una tarjeta summary_large_image, los clientes la recortan por el
centro y se pierden el título y el sello del editor. Esta tarjeta hace lo
mismo que build-manecillas-social-card.py y build-home-social-card.py: fondo
desenfocado derivado de la propia portada, la portada nítida a la derecha sin
recortar, y el texto del premio a la izquierda con las fuentes del sitio.

JPEG, no WEBP: el crawler de vistas previas de WhatsApp no renderiza
og:image en WEBP de forma fiable (misma razón documentada en las otras dos
tarjetas del repositorio).

Usage:
  python scripts/build-al-otro-lado-social-card.py
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
COVER = ROOT / "assets" / "al-otro-lado-antologia-letras-como-espada-portada.webp"
OUT = ROOT / "assets" / "og-al-otro-lado-microrrelato-ganador.jpg"

FONT_SERIF = ROOT / "assets" / "fonts" / "cg-normal-latin.woff2"  # Cormorant Garamond
FONT_SANS = ROOT / "assets" / "fonts" / "inter-normal-latin.woff2"  # Inter

W, H = 1200, 630

TINTA = (0x17, 0x12, 0x0B)
BRONCE = (0x93, 0x66, 0x31)
ORO = (0xCF, 0x92, 0x46)
MARFIL = (0xF2, 0xE8, 0xD8)
HUMO = (0xB6, 0xA8, 0x94)

COVER_H = 470
MARGIN_RIGHT = 80


def make_background(cover: Image.Image) -> Image.Image:
    bg = ImageOps.fit(cover, (W * 2, H * 2), method=Image.LANCZOS, centering=(0.5, 0.35))
    bg = bg.filter(ImageFilter.GaussianBlur(55))
    bg = Image.blend(bg, Image.new("RGB", bg.size, TINTA), 0.66)
    return ImageOps.fit(bg, (W, H), method=Image.LANCZOS)


def paste_cover(bg: Image.Image, cover: Image.Image) -> tuple[Image.Image, int]:
    """Portada completa, sin recortar: es el objeto del que habla la pagina."""
    cover_w = round(COVER_H * cover.width / cover.height)
    panel = cover.resize((cover_w, COVER_H), Image.LANCZOS)
    x = W - MARGIN_RIGHT - cover_w
    y = (H - COVER_H) // 2

    shadow = Image.new("L", (cover_w + 60, COVER_H + 60), 0)
    ImageDraw.Draw(shadow).rectangle([30, 30, cover_w + 29, COVER_H + 29], fill=150)
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    bg.paste(Image.new("RGB", shadow.size, (0, 0, 0)), (x - 30, y - 22), shadow)

    bg.paste(panel, (x, y))
    ImageDraw.Draw(bg).rectangle([x, y, x + cover_w - 1, y + COVER_H - 1], outline=(0x3A, 0x30, 0x25), width=1)
    return bg, x


def add_scrim(bg: Image.Image, text_right: int) -> Image.Image:
    """Velo en la mitad izquierda para que el texto se lea sobre cualquier
    zona de la portada desenfocada."""
    scrim = Image.new("L", (text_right, 1), 0)
    for x in range(text_right):
        scrim.putpixel((x, 0), int(190 * (1 - (x / text_right) ** 2.2)))
    scrim = scrim.resize((text_right, H))
    bg.paste(Image.new("RGB", (text_right, H), TINTA), (0, 0), scrim)
    return bg


def wrap(draw, text, font, max_w):
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= max_w or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_text(im: Image.Image, cover_x: int) -> Image.Image:
    draw = ImageDraw.Draw(im)
    left = 72
    max_w = cover_x - left - 56

    eyebrow_font = ImageFont.truetype(str(FONT_SANS), 19)
    title_font = ImageFont.truetype(str(FONT_SERIF), 92)
    author_font = ImageFont.truetype(str(FONT_SANS), 25)
    meta_font = ImageFont.truetype(str(FONT_SANS), 19)

    y = 168
    draw.text((left, y), "MICRORRELATO GANADOR · 2026", font=eyebrow_font, fill=ORO)
    y += 44
    draw.text((left, y), "Al otro lado", font=title_font, fill=MARFIL)
    y += title_font.size + 30
    draw.line([(left, y), (left + 96, y)], fill=BRONCE, width=2)
    y += 22
    draw.text((left, y), "David Porto Díaz", font=author_font, fill=MARFIL)
    y += 38
    for line in wrap(draw, "XII Certamen de Microrrelatos «De amor» · Letras Como Espada", meta_font, max_w):
        draw.text((left, y), line, font=meta_font, fill=HUMO)
        y += 26
    return im


def main() -> None:
    cover = Image.open(COVER).convert("RGB")
    bg = make_background(cover)
    bg, cover_x = paste_cover(bg, cover)
    bg = add_scrim(bg, cover_x - 40)
    bg, _ = paste_cover(bg, cover)  # repintar la portada sobre el velo
    final = draw_text(bg, cover_x)

    for quality in (88, 84, 80, 76):
        final.save(OUT, "JPEG", quality=quality, optimize=True)
        size = OUT.stat().st_size
        if size <= 300 * 1024:
            print(f"Saved {OUT} at quality={quality}: {size} bytes ({size / 1024:.1f} KiB)")
            return
    print(f"WARNING: no baja de 300 KiB ni a quality=76 ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
