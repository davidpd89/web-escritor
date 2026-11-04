#!/usr/bin/env python3
"""Regression contract for V1 metric-matched fallback font faces.

These fallback faces are part of the CLS strategy: their size/vertical metrics
and local() source order are intentional. Formatting is not part of the
contract.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "assets" / "v1-fonts.css").read_text(encoding="utf-8")

FACE_RE = re.compile(r"@font-face\s*\{([^{}]*)\}", re.IGNORECASE | re.DOTALL)
LOCAL_RE = re.compile(r"local\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)


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


def fallback_faces() -> dict[tuple[str, str], dict[str, str]]:
    faces: dict[tuple[str, str], dict[str, str]] = {}
    for body in FACE_RE.findall(CSS):
        decls = declarations(body)
        family = unquote(decls.get("font-family", ""))
        if " Fallback" not in family:
            continue
        style = decls.get("font-style", "normal").strip().lower()
        key = (family, style)
        assert key not in faces, f"duplicate fallback face: {family} ({style})"
        faces[key] = decls
    return faces


def local_sources(src: str) -> tuple[str, ...]:
    return tuple(match.group(2).strip() for match in LOCAL_RE.finditer(src))


def percentage(value: str | None) -> Decimal:
    assert value is not None and value.endswith("%"), f"expected CSS percentage, found {value!r}"
    try:
        return Decimal(value[:-1])
    except InvalidOperation as exc:
        raise AssertionError(f"invalid CSS percentage: {value!r}") from exc


def main() -> None:
    assert percentage("123.530%") == percentage("123.53%")
    assert percentage("0.00%") == percentage("0%")

    # Measured with fontTools (see the comment in assets/v1-fonts.css): one face
    # per real local font, because size-adjust is not portable between them.
    expected = {
        ("Newsreader Fallback", "normal"): {
            "locals": ('Georgia',),
            "size-adjust": "90.67%",
            "ascent-override": "81.06%",
            "descent-override": "29.23%",
            "line-gap-override": "0%",
        },
        ("Newsreader Fallback Liberation", "normal"): {
            "locals": ('Liberation Serif', 'LiberationSerif', 'Times New Roman', 'TimesNewRomanPSMT', 'Tinos'),
            "size-adjust": "99.39%",
            "ascent-override": "73.95%",
            "descent-override": "26.66%",
            "line-gap-override": "0%",
        },
        ("Newsreader Fallback DejaVu", "normal"): {
            "locals": ('DejaVu Serif', 'DejaVuSerif'),
            "size-adjust": "77.75%",
            "ascent-override": "94.53%",
            "descent-override": "34.08%",
            "line-gap-override": "0%",
        },
        ("Instrument Serif Fallback", "normal"): {
            "locals": ('Georgia',),
            "size-adjust": "76.41%",
            "ascent-override": "129.56%",
            "descent-override": "40.57%",
            "line-gap-override": "0%",
        },
        ("Instrument Serif Fallback Liberation", "normal"): {
            "locals": ('Liberation Serif', 'LiberationSerif', 'Times New Roman', 'TimesNewRomanPSMT', 'Tinos'),
            "size-adjust": "83.75%",
            "ascent-override": "118.20%",
            "descent-override": "37.01%",
            "line-gap-override": "0%",
        },
        ("Instrument Serif Fallback DejaVu", "normal"): {
            "locals": ('DejaVu Serif', 'DejaVuSerif'),
            "size-adjust": "65.52%",
            "ascent-override": "151.10%",
            "descent-override": "47.31%",
            "line-gap-override": "0%",
        },
        ("Newsreader Fallback", "italic"): {
            "locals": ('Georgia Italic', 'Georgia-Italic'),
            "size-adjust": "82.66%",
            "ascent-override": "88.92%",
            "descent-override": "32.06%",
            "line-gap-override": "0%",
        },
        ("Newsreader Fallback Liberation", "italic"): {
            "locals": ('Liberation Serif Italic', 'LiberationSerif-Italic', 'Times New Roman Italic', 'TimesNewRomanPS-ItalicMT', 'Tinos Italic'),
            "size-adjust": "91.28%",
            "ascent-override": "80.52%",
            "descent-override": "29.03%",
            "line-gap-override": "0%",
        },
        ("Newsreader Fallback DejaVu", "italic"): {
            "locals": ('DejaVu Serif Italic', 'DejaVuSerif-Italic'),
            "size-adjust": "72.61%",
            "ascent-override": "101.23%",
            "descent-override": "36.50%",
            "line-gap-override": "0%",
        },
        ("Instrument Serif Fallback", "italic"): {
            "locals": ('Georgia Italic', 'Georgia-Italic'),
            "size-adjust": "79.64%",
            "ascent-override": "124.31%",
            "descent-override": "38.93%",
            "line-gap-override": "0%",
        },
        ("Instrument Serif Fallback Liberation", "italic"): {
            "locals": ('Liberation Serif Italic', 'LiberationSerif-Italic', 'Times New Roman Italic', 'TimesNewRomanPS-ItalicMT', 'Tinos Italic'),
            "size-adjust": "87.94%",
            "ascent-override": "112.57%",
            "descent-override": "35.25%",
            "line-gap-override": "0%",
        },
        ("Instrument Serif Fallback DejaVu", "italic"): {
            "locals": ('DejaVu Serif Italic', 'DejaVuSerif-Italic'),
            "size-adjust": "69.95%",
            "ascent-override": "141.52%",
            "descent-override": "44.32%",
            "line-gap-override": "0%",
        },
        ("Manrope Fallback", "normal"): {
            "locals": ('Arial', 'ArialMT', 'Liberation Sans', 'LiberationSans', 'Arimo', 'Helvetica'),
            "size-adjust": "101.84%",
            "ascent-override": "104.68%",
            "descent-override": "29.46%",
            "line-gap-override": "0%",
        },
        ("Manrope Fallback DejaVu", "normal"): {
            "locals": ('DejaVu Sans', 'DejaVuSans'),
            "size-adjust": "90.05%",
            "ascent-override": "118.38%",
            "descent-override": "33.32%",
            "line-gap-override": "0%",
        },
        ("Allura Fallback", "normal"): {
            "locals": ('Arial', 'ArialMT', 'Liberation Sans', 'LiberationSans', 'Arimo', 'Helvetica'),
            "size-adjust": "73.60%",
            "ascent-override": "108.69%",
            "descent-override": "61.14%",
            "line-gap-override": "0%",
        },
        ("Allura Fallback DejaVu", "normal"): {
            "locals": ('DejaVu Sans', 'DejaVuSans'),
            "size-adjust": "65.08%",
            "ascent-override": "122.92%",
            "descent-override": "69.14%",
            "line-gap-override": "0%",
        },
    }

    faces = fallback_faces()
    assert set(expected).issubset(faces), (
        "missing V1 metric fallback face(s): "
        + ", ".join(f"{family} ({style})" for family, style in sorted(set(expected) - set(faces)))
    )

    for key, contract in expected.items():
        face = faces[key]
        family, style = key
        assert local_sources(face.get("src", "")) == contract["locals"], (
            f"{family} ({style}): local() fallback order drifted"
        )
        for prop in (
            "size-adjust",
            "ascent-override",
            "descent-override",
            "line-gap-override",
        ):
            assert percentage(face.get(prop)) == percentage(contract[prop]), (
                f"{family} ({style}): {prop} drifted "
                f"(expected {contract[prop]}, found {face.get(prop)!r})"
            )

    tokens = (ROOT / "assets" / "v1-tokens.css").read_text(encoding="utf-8")
    for token, families in {
        "--font-display": ("Instrument Serif", "Instrument Serif Fallback", "Instrument Serif Fallback Liberation", "Instrument Serif Fallback DejaVu"),
        "--font-reading": ("Newsreader", "Newsreader Fallback", "Newsreader Fallback Liberation", "Newsreader Fallback DejaVu"),
        "--font-ui": ("Manrope", "Manrope Fallback", "Manrope Fallback DejaVu"),
        "--font-script": ("Allura", "Allura Fallback", "Allura Fallback DejaVu"),
    }.items():
        match = re.search(re.escape(token) + r"\s*:([^;]*);", tokens)
        assert match, f"{token} missing from v1-tokens.css"
        stack = tuple(unquote(part) for part in match.group(1).split(","))
        assert stack[: len(families)] == families, f"{token}: fallback faces missing or out of order: {stack}"

    print(f"PASS V1 fallback metrics contract: {len(expected)} face(s) checked")


if __name__ == "__main__":
    main()
