#!/usr/bin/env python3
"""Build the Las manecillas del recuerdo 3D book mockup from the real,
versioned cover — no AI generation, fully reproducible from a clean
checkout.

INPUT VERSIONED (git-tracked):
  assets/portada-las-manecillas-del-recuerdo-1024.webp  (the real cover)
  assets/manecillas/source/mockup-build.html.txt        (the CSS 3D recipe)

BUILDER (this script):
  Renders the recipe with the real cover composited onto the front face
  via headless Chrome (Selenium), using Emulation.setDefaultBackground
  ColorOverride for a transparent capture. Auto-crops to content bounds,
  then produces the main web asset plus 320/512/768/1024 responsive
  variants.

OUTPUT (git-tracked, this script overwrites them deterministically):
  assets/manecillas-book-mockup.webp
  assets/manecillas-book-mockup-{320,512,768,1024}.webp

The cover pixels are never touched, redrawn, or reinterpreted by any
model — this only positions the real, unmodified cover image in 3D
space via CSS transforms and adds a plain-color spine (no invented
spine text) and a page-edge strip, per the project's "portada oficial =
fuente intocable" rule.

Requires: selenium (+ a Chrome/Chromedriver available on PATH) and
Pillow. Both were already used ad hoc for this asset during development;
this script is the first committed, reproducible version of that
process.

Usage:
  python scripts/build-manecillas-mockup.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).resolve().parents[1]
COVER = ROOT / "assets" / "portada-las-manecillas-del-recuerdo-1024.webp"
RECIPE = ROOT / "assets" / "manecillas" / "source" / "mockup-build.html.txt"
BUILD_HTML = ROOT / "assets" / "manecillas" / "source" / "_mockup-build.rendered.html"
RAW_SHOT = ROOT / "assets" / "manecillas" / "source" / "_mockup-raw.png"
MASTER_OUT = ROOT / "assets" / "manecillas" / "source" / "manecillas-book-mockup-master.png"
FINAL_OUT = ROOT / "assets" / "manecillas-book-mockup.webp"
RESPONSIVE_WIDTHS = (320, 512, 768, 1024)
MASTER_HEIGHT = 2100  # main asset target height, ~ same scale Samuel's mockup uses
SCREENSHOT_SCALE = 3.0  # supersample for crisp small cover text, then downscale


def render_screenshot() -> None:
    template = RECIPE.read_text(encoding="utf-8")
    cover_uri = COVER.resolve().as_uri()
    rendered = template.replace("COVER_URL_PLACEHOLDER", cover_uri)
    BUILD_HTML.write_text(rendered, encoding="utf-8")

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument(f"--force-device-scale-factor={SCREENSHOT_SCALE}")
    opts.add_argument("--window-size=1200,1300")
    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(BUILD_HTML.resolve().as_uri())
        driver.execute_cdp_cmd(
            "Emulation.setDefaultBackgroundColorOverride",
            {"color": {"r": 0, "g": 0, "b": 0, "a": 0}},
        )
        el = driver.find_element("css selector", ".stage")
        RAW_SHOT.write_bytes(el.screenshot_as_png)
    finally:
        driver.quit()
        BUILD_HTML.unlink(missing_ok=True)


def crop_and_master() -> Image.Image:
    im = Image.open(RAW_SHOT)
    bbox = im.getbbox()
    cropped = im.crop(bbox)
    pad = int(max(cropped.size) * 0.02)
    padded = Image.new("RGBA", (cropped.width + pad * 2, cropped.height + pad * 2), (0, 0, 0, 0))
    padded.paste(cropped, (pad, pad), cropped)
    padded.save(MASTER_OUT)
    RAW_SHOT.unlink(missing_ok=True)
    return padded


def export_web_sizes(master: Image.Image) -> None:
    scale = MASTER_HEIGHT / master.height
    main_w = round(master.width * scale)
    main = master.resize((main_w, MASTER_HEIGHT), Image.LANCZOS)
    # quality search to land close to Samuel's mockup weight (~190 KiB)
    # without a hardcoded quality that could look bad on a future cover.
    for q in (78, 74, 70, 66):
        main.save(FINAL_OUT, "WEBP", quality=q, method=6)
        if FINAL_OUT.stat().st_size <= 260 * 1024:
            break
    print(f"{FINAL_OUT.name}: {main.size} {FINAL_OUT.stat().st_size / 1024:.1f} KiB")

    for w in RESPONSIVE_WIDTHS:
        h = round(master.height * (w / master.width))
        variant = master.resize((w, h), Image.LANCZOS)
        out = ROOT / "assets" / f"manecillas-book-mockup-{w}.webp"
        variant.save(out, "WEBP", quality=82, method=6)
        print(f"{out.name}: {variant.size} {out.stat().st_size / 1024:.1f} KiB")


def main() -> None:
    if not COVER.exists():
        raise SystemExit(f"Missing versioned input cover: {COVER}")
    if not RECIPE.exists():
        raise SystemExit(f"Missing mockup recipe: {RECIPE}")
    render_screenshot()
    master = crop_and_master()
    export_web_sizes(master)


if __name__ == "__main__":
    main()
