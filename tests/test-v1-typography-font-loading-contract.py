#!/usr/bin/env python3
"""Regression contract for the V1 typography loading strategy.

These values are intentional:
- body/UI Manrope stays optional to avoid CLS from late paragraph reflow;
- isolated display-only Manrope swaps once loaded;
- Yellowtail swaps so decorative labels do not remain on their fallback.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTS = (ROOT / "assets" / "v1-fonts.css").read_text(encoding="utf-8")
TOKENS = (ROOT / "assets" / "v1-tokens.css").read_text(encoding="utf-8")


def font_faces(family: str) -> list[str]:
    pattern = rf"@font-face\{{font-family:'{re.escape(family)}';.*?\}}"
    return re.findall(pattern, FONTS, flags=re.DOTALL)


def require_display_mode(family: str, expected: str) -> None:
    faces = font_faces(family)
    assert faces, f"{family}: no @font-face declarations found"
    wrong = [face for face in faces if f"font-display:{expected}" not in face]
    assert not wrong, f"{family}: every face must use font-display:{expected}"


def main() -> None:
    require_display_mode("Manrope", "optional")
    require_display_mode("Manrope Display", "swap")
    require_display_mode("Yellowtail", "swap")

    expected_tokens = {
        "--font-display": '"Instrument Serif","Instrument Serif Fallback"',
        "--font-ui": '"Manrope","Manrope Fallback"',
        "--font-reading": '"Newsreader","Newsreader Fallback"',
        "--font-script": '"Allura","Allura Fallback"',
    }
    for token, stack_start in expected_tokens.items():
        needle = f"{token}:{stack_start}"
        assert needle in TOKENS, f"{token}: canonical V1 font stack drifted"

    print("PASS V1 typography font-loading contract")


if __name__ == "__main__":
    main()
