#!/usr/bin/env python3
"""Regression contract for Manrope / Manrope Display source parity.

Manrope Display exists only to give isolated Home headings font-display:swap.
It must reuse the same font files, weight/style and unicode ranges as Manrope
so the browser can reuse the same downloads. Formatting is not part of the
contract.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / "assets" / "v1-fonts.css").read_text(encoding="utf-8")

FACE_RE = re.compile(r"@font-face\s*\{([^{}]*)\}", re.IGNORECASE | re.DOTALL)
URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
FORMAT_RE = re.compile(r"format\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)


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


def normalize_words(value: str) -> str:
    return " ".join(value.split()).lower()


def normalize_unicode_range(value: str) -> str:
    ranges = [re.sub(r"\s+", "", part).lower() for part in value.split(",") if part.strip()]
    return ",".join(sorted(ranges))


def sources(value: str) -> tuple[tuple[str, str], ...]:
    assert "local(" not in value.casefold(), f"Manrope source must stay URL-backed: {value!r}"
    urls = [match.group(2).strip() for match in URL_RE.finditer(value)]
    formats = [match.group(2).strip().lower() for match in FORMAT_RE.finditer(value)]
    assert urls, f"src has no URL-backed font source: {value!r}"
    assert len(urls) == len(formats), f"src URL/format count mismatch: {value!r}"
    return tuple(zip(urls, formats))


def family_signatures(family: str) -> set[tuple[str, str, tuple[tuple[str, str], ...], str]]:
    signatures: set[tuple[str, str, tuple[tuple[str, str], ...], str]] = set()
    count = 0

    for body in FACE_RE.findall(CSS):
        decls = declarations(body)
        if unquote(decls.get("font-family", "")).casefold() != family.casefold():
            continue

        count += 1
        assert decls.get("src"), f"{family}: face is missing src"
        assert decls.get("unicode-range"), f"{family}: face is missing unicode-range"

        signature = (
            normalize_words(decls.get("font-style", "normal")),
            normalize_words(decls.get("font-weight", "normal")),
            sources(decls["src"]),
            normalize_unicode_range(decls["unicode-range"]),
        )
        assert signature not in signatures, f"{family}: duplicate source/range face"
        signatures.add(signature)

    assert count > 0, f"{family}: no @font-face declarations found"
    return signatures


def main() -> None:
    assert family_signatures("MANROPE") == family_signatures("Manrope")
    assert normalize_unicode_range("U+0100-02BA, U+02BD") == normalize_unicode_range(
        "u+02bd,u+0100-02ba"
    )

    manrope = family_signatures("Manrope")
    display = family_signatures("Manrope Display")

    assert display == manrope, (
        "Manrope Display must reuse Manrope style/weight/src/unicode-range exactly; "
        f"Manrope has {len(manrope)} signature(s), Display has {len(display)}"
    )

    print(f"PASS V1 Manrope Display parity: {len(manrope)} shared face signature(s)")


if __name__ == "__main__":
    main()
