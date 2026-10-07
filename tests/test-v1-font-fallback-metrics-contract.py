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
        if not family.endswith(" Fallback"):
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

    expected = {
        ("Newsreader Fallback", "normal"): {
            "locals": ("Georgia", "Liberation Serif", "DejaVu Serif"),
            "size-adjust": "123.53%",
            "ascent-override": "59.51%",
            "descent-override": "21.45%",
            "line-gap-override": "0%",
        },
        ("Instrument Serif Fallback", "normal"): {
            "locals": ("Georgia", "Liberation Serif", "DejaVu Serif"),
            "size-adjust": "95.91%",
            "ascent-override": "103.23%",
            "descent-override": "32.32%",
            "line-gap-override": "0%",
        },
        ("Newsreader Fallback", "italic"): {
            "locals": ("Georgia", "Liberation Serif", "DejaVu Serif"),
            "size-adjust": "111.95%",
            "ascent-override": "65.66%",
            "descent-override": "23.67%",
            "line-gap-override": "0%",
        },
        ("Instrument Serif Fallback", "italic"): {
            "locals": ("Georgia", "Liberation Serif", "DejaVu Serif"),
            "size-adjust": "98.88%",
            "ascent-override": "100.12%",
            "descent-override": "31.35%",
            "line-gap-override": "0%",
        },
        ("Manrope Fallback", "normal"): {
            "locals": ("Arial", "Liberation Sans", "DejaVu Sans", "Helvetica"),
            "size-adjust": "128.11%",
            "ascent-override": "83.21%",
            "descent-override": "23.42%",
            "line-gap-override": "0%",
        },
        ("Allura Fallback", "normal"): {
            "locals": ("Arial", "Liberation Sans", "DejaVu Sans", "Helvetica"),
            "size-adjust": "130.27%",
            "ascent-override": "61.41%",
            "descent-override": "34.54%",
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

    print(f"PASS V1 fallback metrics contract: {len(expected)} face(s) checked")


if __name__ == "__main__":
    main()
