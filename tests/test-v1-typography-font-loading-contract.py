#!/usr/bin/env python3
"""Regression contract for the V1 typography loading strategy.

These values are intentional:
- body/UI Manrope stays optional to avoid CLS from late paragraph reflow;
- isolated display-only Manrope swaps once loaded;
- Yellowtail swaps so decorative labels do not remain on their fallback.

Whitespace/minification and quote style are not part of this contract.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTS = (ROOT / "assets" / "v1-fonts.css").read_text(encoding="utf-8")
TOKENS = (ROOT / "assets" / "v1-tokens.css").read_text(encoding="utf-8")


def normalize_css(css: str) -> str:
    return re.sub(r"\s+", "", css).replace("'", '"').lower()


def font_faces(family: str) -> list[str]:
    family_needle = normalize_css(f'font-family:"{family}"')
    blocks = re.findall(r"@font-face\s*\{.*?\}", FONTS, flags=re.DOTALL | re.IGNORECASE)
    return [normalize_css(block) for block in blocks if family_needle in normalize_css(block)]


def require_display_mode(family: str, expected: str) -> None:
    faces = font_faces(family)
    assert faces, f"{family}: no @font-face declarations found"
    wrong = [face for face in faces if f"font-display:{expected}" not in face]
    assert not wrong, f"{family}: every face must use font-display:{expected}"


def main() -> None:
    require_display_mode("Manrope", "optional")
    require_display_mode("Manrope Display", "swap")
    require_display_mode("Yellowtail", "swap")

    normalized_tokens = normalize_css(TOKENS)
    expected_tokens = {
        "--font-display": '"Instrument Serif","Instrument Serif Fallback"',
        "--font-ui": '"Manrope","Manrope Fallback"',
        "--font-reading": '"Newsreader","Newsreader Fallback"',
        "--font-script": '"Allura","Allura Fallback"',
    }
    for token, stack_start in expected_tokens.items():
        needle = normalize_css(f"{token}:{stack_start}")
        assert needle in normalized_tokens, f"{token}: canonical V1 font stack drifted"

    print("PASS V1 typography font-loading contract")


if __name__ == "__main__":
    main()
