"""Genera los avatares de los canales (Telegram y Discord) en assets/community-avatars/.

Solo tipografía: el nombre del género en grande, un color por canal con la misma
luminosidad (OKLCH) y «davidportodiaz.com» en pequeño. Pensados para recorte circular
y legibles a 48 px.

    python scripts/build-community-avatars.py            # escribe los .webp
    python scripts/build-community-avatars.py --preview  # además, una hoja de contacto
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "community-avatars"
FONT = "C:/Windows/Fonts/bahnschrift.ttf"
SIZE = 512
INK = (255, 247, 232)

# id → (líneas, tono OKLCH en grados). El tono se reparte por la rueda con la misma L y C.
AVATARS = {
    "novedades": (["NOVEDADES"], 15),
    "terror": (["TERROR"], 25),
    "comic": (["CÓMIC"], 40),
    "resumen": (["RESUMEN", "DEL DÍA"], 58),
    "humor": (["HUMOR"], 112),
    "aventuras": (["AVENTURAS"], 138),
    "economia": (["ECONOMÍA"], 162),
    "biografias": (["BIOGRAFÍAS"], 188),
    "desarrollo-personal": (["DESARROLLO", "PERSONAL"], 210),
    "arte-ocio": (["ARTE", "Y OCIO"], 343),
    "historica": (["HISTÓRICA"], 78),
    "narrativa": (["NARRATIVA"], 98),
    "cocina": (["COCINA"], 125),
    "infantil-juvenil": (["INFANTIL", "JUVENIL"], 150),
    "ensayo": (["ENSAYO"], 175),
    "proximos": (["PRÓXIMOS"], 200),
    "ciencia-ficcion": (["CIENCIA", "FICCIÓN"], 222),
    "todos": (["TODOS"], 242),
    "thriller": (["THRILLER"], 262),
    "discord": (["CLUB", "LECTOR"], 278),
    "religion": (["ESPIRITUAL"], 295),
    "fantasia": (["FANTASÍA"], 312),
    "poesia": (["POESÍA"], 332),
    "romantica": (["ROMÁNTICA"], 355),
}
# Terror y thriller más oscuros: se distinguen de sus vecinos y encajan con el género.
LIGHTNESS = {"terror": 0.32, "thriller": 0.32, "historica": 0.42, "narrativa": 0.42}


def oklch(l: float, c: float, h: float) -> tuple[int, int, int]:
    a, b = c * math.cos(math.radians(h)), c * math.sin(math.radians(h))
    l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (l - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )

    def gamma(x: float) -> int:
        x = min(max(x, 0.0), 1.0)
        x = 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
        return round(x * 255)

    return tuple(gamma(x) for x in rgb)  # type: ignore[return-value]


def font(size: int, style: bytes = b"Bold Condensed") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_name(style)
    return f


def fit(text: str, width: int, max_height: int) -> ImageFont.FreeTypeFont:
    """El mayor tamaño cuyo texto cabe en el ancho y no supera la altura de mayúscula."""
    lo, hi = 10, 400
    while lo < hi:
        mid = (lo + hi + 1) // 2
        box = font(mid).getbbox(text)
        if box[2] - box[0] <= width and font(mid).getbbox("H")[3] - font(mid).getbbox("H")[1] <= max_height:
            lo = mid
        else:
            hi = mid - 1
    return font(lo)


def render(lines: list[str], hue: float, l: float) -> Image.Image:
    bg = oklch(l, 0.13, hue)
    img = Image.new("RGB", (SIZE, SIZE), bg)
    d = ImageDraw.Draw(img)
    # Aro fino: el sello común de todos los canales, dentro del recorte circular.
    d.ellipse((26, 26, SIZE - 26, SIZE - 26), outline=INK, width=5)
    # Zona útil dentro del aro: ancho 70 % para una línea, 66 % para dos.
    one = len(lines) == 1
    width = int(SIZE * (0.70 if one else 0.66))
    cap = 150 if one else 118
    gap = 22
    fonts = [fit(t, width, cap) for t in lines]
    # Todas las líneas con el mismo tamaño (el menor) para que el bloque sea uniforme.
    f = min(fonts, key=lambda x: x.size)
    caps = [f.getbbox("H") for _ in lines]
    cap_h = caps[0][3] - caps[0][1]
    block = cap_h * len(lines) + gap * (len(lines) - 1)
    top = SIZE * 0.47 - block / 2
    for i, t in enumerate(lines):
        w = f.getlength(t)
        y = top + i * (cap_h + gap) - caps[0][1]
        d.text(((SIZE - w) / 2, y), t, font=f, fill=INK)
    # Filete fino y firma.
    rule_y = int(top + block + 34)
    d.line([(SIZE / 2 - 34, rule_y), (SIZE / 2 + 34, rule_y)], fill=INK, width=4)
    sig = font(30, b"SemiBold")
    s = "davidportodiaz.com"
    d.text(((SIZE - sig.getlength(s)) / 2, rule_y + 18), s, font=sig, fill=INK)
    return img


def banner() -> Image.Image:
    """Banner del servidor de Discord (960×540): mismo sistema, franja de colores de los canales."""
    w, h = 960, 540
    img = Image.new("RGB", (w, h), oklch(0.30, 0.10, 278))
    d = ImageDraw.Draw(img)
    hues = [hue for _, hue in AVATARS.values()]
    band = w / len(hues)
    for i, hue in enumerate(sorted(hues)):
        d.rectangle((round(i * band), h - 46, round((i + 1) * band), h), fill=oklch(0.50, 0.13, hue))
    title = fit("CLUB DE LECTURA", int(w * 0.80), 120)
    tw = title.getlength("CLUB DE LECTURA")
    top = title.getbbox("H")
    d.text(((w - tw) / 2, 150 - top[1]), "CLUB DE LECTURA", font=title, fill=INK)
    y = 150 + (top[3] - top[1]) + 40
    d.line([(w / 2 - 50, y), (w / 2 + 50, y)], fill=INK, width=4)
    sub = font(40, b"SemiBold")
    for text, dy in (("Novedades y recomendaciones por género", 30), ("davidportodiaz.com", 90)):
        d.text(((w - sub.getlength(text)) / 2, y + dy), text, font=sub, fill=INK)
    return img


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=Path, help="hoja de contacto PNG (512 y 48 px, recorte circular)")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    images = {}
    for slug, (lines, hue) in AVATARS.items():
        img = render(lines, hue, LIGHTNESS.get(slug, 0.44))
        img.save(OUT / f"{slug}.webp", "WEBP", quality=88, method=6)
        images[slug] = img
    banner().save(OUT / "discord-banner.jpg", "JPEG", quality=90, optimize=True)
    if args.preview:
        cols, cell = 6, 200
        rows = math.ceil(len(images) / cols)
        sheet = Image.new("RGB", (cols * cell, rows * cell), (245, 245, 245))
        mask = Image.new("L", (160, 160), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 159, 159), fill=255)
        small_mask = Image.new("L", (48, 48), 0)
        ImageDraw.Draw(small_mask).ellipse((0, 0, 47, 47), fill=255)
        for i, img in enumerate(images.values()):
            x, y = (i % cols) * cell, (i // cols) * cell
            sheet.paste(img.resize((160, 160), Image.LANCZOS), (x + 4, y + 4), mask)
            sheet.paste(img.resize((48, 48), Image.LANCZOS), (x + 148, y + 148), small_mask)
        sheet.save(args.preview)
    print(f"{len(images)} avatares en {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
