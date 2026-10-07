#!/usr/bin/env python3
"""Regression contract for the V1 typography loading strategy.

These values are intentional:
- canonical body/editorial/script families stay optional to avoid late reflow;
- isolated display-only Manrope and decorative Yellowtail swap once loaded;
- each semantic typography token is defined once and keeps its canonical pair.

Whitespace/minification and quote style are not part of this contract.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTS = (ROOT / "assets" / "v1-fonts.css").read_text(encoding="utf-8")
TOKENS = (ROOT / "assets" / "v1-tokens.css").read_text(encoding="utf-8")


def normalize_font_stack(value: str) -> str:
    parts = re.split(r"\s*,\s*", value.strip())
    return ",".join(part.strip().replace('"', "'") for part in parts)


def font_faces(family: str) -> list[str]:
    blocks = re.findall(r"@font-face\s*\{.*?\}", FONTS, flags=re.DOTALL | re.IGNORECASE)
    family_re = re.compile(
        rf"font-family\s*:\s*(['\"]){re.escape(family)}\1\s*(?:;|}})",
        re.IGNORECASE,
    )
    return [block for block in blocks if family_re.search(block)]


def require_display_mode(family: str, expected: str) -> None:
    faces = font_faces(family)
    assert faces, f"{family}: no @font-face declarations found"
    display_re = re.compile(rf"font-display\s*:\s*{re.escape(expected)}\s*(?:;|}})", re.IGNORECASE)
    wrong = [face for face in faces if not display_re.search(face)]
    assert not wrong, f"{family}: every face must use font-display:{expected}"


def token_values(token: str) -> list[str]:
    pattern = rf"{re.escape(token)}\s*:\s*([^;}}]+)"
    return [normalize_font_stack(value) for value in re.findall(pattern, TOKENS)]


def require_canonical_token(token: str, stack_start: str) -> None:
    values = token_values(token)
    assert len(values) == 1, f"{token}: expected exactly one declaration, found {len(values)}"
    expected = normalize_font_stack(stack_start)
    assert values[0].startswith(expected), f"{token}: canonical V1 font stack drifted"


def main() -> None:
    expected_display_modes = {
        "Instrument Serif": "optional",
        "Manrope": "optional",
        "Manrope Display": "swap",
        "Newsreader": "optional",
        "Allura": "optional",
        "Yellowtail": "swap",
    }
    for family, expected in expected_display_modes.items():
        require_display_mode(family, expected)

    assert normalize_font_stack('"Instrument  Serif","Instrument Serif Fallback"') != normalize_font_stack(
        '"Instrument Serif","Instrument Serif Fallback"'
    )
    assert normalize_font_stack('"Manrope",var(--FONT-ui)') != normalize_font_stack(
        '"Manrope",var(--font-ui)'
    )

    expected_tokens = {
        "--font-display": '"Instrument Serif","Instrument Serif Fallback"',
        "--font-ui": '"Manrope","Manrope Fallback"',
        "--font-reading": '"Newsreader","Newsreader Fallback"',
        "--font-script": '"Allura","Allura Fallback"',
    }
    for token, stack_start in expected_tokens.items():
        require_canonical_token(token, stack_start)

    print("PASS V1 typography font-loading contract")


if __name__ == "__main__":
    main()
