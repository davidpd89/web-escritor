#!/usr/bin/env python3
"""Regression contract for the V1 typography loading strategy.

These values are intentional:
- body/UI Manrope stays optional to avoid CLS from late paragraph reflow;
- isolated display-only Manrope swaps once loaded;
- Yellowtail swaps so decorative labels do not remain on their fallback.

The contract compares CSS declarations semantically enough to survive harmless
whitespace/minification and quote-style changes. Formatting is not part of the
typography contract.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTS = (ROOT / "assets" / "v1-fonts.css").read_text(encoding="utf-8")
TOKENS = (ROOT / "assets" / "v1-tokens.css").read_text(encoding="utf-8")

FONT_FACE_RE = re.compile(r"@font-face\s*\{([^{}]*)\}", re.IGNORECASE | re.DOTALL)
CUSTOM_PROPERTY_RE = re.compile(
    r"(?P<name>--[\w-]+)\s*:\s*(?P<value>[^;{}]+);",
    re.IGNORECASE,
)


def declarations(block: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in block.split(";"):
        if ":" not in raw:
            continue
        name, value = raw.split(":", 1)
        result[name.strip().lower()] = value.strip()
    return result


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def normalize_css_value(value: str) -> str:
    return re.sub(r"\s+", "", value).replace("'", '"')


def font_faces(css: str, family: str) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    for body in FONT_FACE_RE.findall(css):
        decls = declarations(body)
        if unquote(decls.get("font-family", "")) == family:
            matches.append(decls)
    return matches


def custom_properties(css: str) -> dict[str, str]:
    return {
        match.group("name"): match.group("value").strip()
        for match in CUSTOM_PROPERTY_RE.finditer(css)
    }


def require_display_mode(family: str, expected: str) -> None:
    faces = font_faces(FONTS, family)
    assert faces, f"{family}: no @font-face declarations found"
    wrong = [
        face
        for face in faces
        if face.get("font-display", "").strip().lower() != expected
    ]
    assert not wrong, f"{family}: every face must use font-display:{expected}"


def verify_parser_format_tolerance() -> None:
    formatted = """
    @font-face {
      font-family: "Manrope";
      font-style: normal;
      font-display : optional;
    }

    :root {
      --font-ui : "Manrope", "Manrope Fallback", sans-serif;
    }
    """
    faces = font_faces(formatted, "Manrope")
    assert len(faces) == 1 and faces[0].get("font-display") == "optional"
    props = custom_properties(formatted)
    assert normalize_css_value(props["--font-ui"]).startswith(
        normalize_css_value('"Manrope","Manrope Fallback"')
    )


def main() -> None:
    verify_parser_format_tolerance()

    require_display_mode("Manrope", "optional")
    require_display_mode("Manrope Display", "swap")
    require_display_mode("Yellowtail", "swap")

    expected_tokens = {
        "--font-display": '"Instrument Serif","Instrument Serif Fallback"',
        "--font-ui": '"Manrope","Manrope Fallback"',
        "--font-reading": '"Newsreader","Newsreader Fallback"',
        "--font-script": '"Allura","Allura Fallback"',
    }
    props = custom_properties(TOKENS)
    for token, stack_start in expected_tokens.items():
        actual = props.get(token)
        assert actual is not None, f"{token}: canonical V1 token is missing"
        assert normalize_css_value(actual).startswith(normalize_css_value(stack_start)), (
            f"{token}: canonical V1 font stack drifted"
        )

    print("PASS V1 typography font-loading contract")


if __name__ == "__main__":
    main()
