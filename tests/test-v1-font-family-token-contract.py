#!/usr/bin/env python3
"""Regression contract for direct font-family declarations in V1 CSS.

Outside assets/v1-fonts.css, V1 styles should use the canonical --font-* tokens.
A small set of deliberate direct stacks is allowed only in the files where
those exceptions already exist.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

TOKEN_RE = re.compile(r"^var\(--font-(?:display|ui|reading|script)\)$")
DECL_RE = re.compile(r"font-family\s*:\s*([^;}]+)", re.IGNORECASE)
COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)

ALLOWED_DIRECT: dict[str, set[str]] = {
    "v1-ai-authority.css": {
        '"SFMono-Regular",Consolas,"Liberation Mono",monospace',
    },
    "v1-fragments.css": {
        "'Yellowtail',var(--font-ui),cursive",
    },
    "v1-home.css": {
        "'Yellowtail',var(--font-ui),cursive",
        "'Manrope Display','Manrope Fallback','Avenir Next',Avenir,'Segoe UI',sans-serif",
    },
    "v1-manecillas-design-v8.css": {
        "'Yellowtail',var(--font-ui),cursive",
    },
    "v1-samuel.css": {
        "'Yellowtail',var(--font-ui),cursive",
    },
    "v1-shell.css": {
        "'Samuel Yellowtail Fallback'",
        "'Yellowtail','Samuel Yellowtail Fallback',cursive",
    },
    "v1-site-cohesion-v6.css": {
        "'Yellowtail',var(--font-ui),cursive",
    },
}


def main() -> None:
    failures: list[str] = []
    checked = 0

    for path in sorted(ASSETS.glob("v1*.css")):
        if path.name == "v1-fonts.css":
            continue

        css = COMMENT_RE.sub("", path.read_text(encoding="utf-8", errors="ignore"))
        for match in DECL_RE.finditer(css):
            checked += 1
            value = " ".join(match.group(1).split())

            if TOKEN_RE.fullmatch(value):
                continue

            allowed = ALLOWED_DIRECT.get(path.name, set())
            if value in allowed:
                continue

            failures.append(
                f"{path.relative_to(ROOT).as_posix()}: unexpected direct font-family {value!r}"
            )

    if checked == 0:
        failures.append("no V1 font-family declarations found")

    if failures:
        print("FAIL V1 font-family token contract:")
        for failure in failures[:50]:
            print(f" - {failure}")
        if len(failures) > 50:
            print(f" - ... {len(failures) - 50} more")
        raise SystemExit(1)

    print(f"PASS V1 font-family token contract: {checked} declaration(s) checked")


if __name__ == "__main__":
    main()
