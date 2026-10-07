#!/usr/bin/env python3
"""Regression contract for font-family usage in V1 CSS.

Outside assets/v1-fonts.css, V1 styles should use the canonical --font-* tokens.
A small set of deliberate direct stacks is allowed only in the files where
those exceptions already exist. Both font-family declarations and the font:
shorthand are covered so the contract cannot be bypassed via shorthand.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

TOKEN = r"var\(--font-(?:display|ui|reading|script)\)"
TOKEN_RE = re.compile(rf"^{TOKEN}$")
TOKEN_AT_END_RE = re.compile(rf"\s({TOKEN})$")
DECL_RE = re.compile(r"font-family\s*:\s*([^;}]+)", re.IGNORECASE)
SHORTHAND_RE = re.compile(r"(?:^|[;{]\s*)font\s*:\s*([^;}]+)", re.IGNORECASE | re.MULTILINE)
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

ALLOWED_SHORTHAND_TAILS: dict[str, set[str]] = {
    "v1-fragments.css": {
        "'Yellowtail',var(--font-ui),cursive",
    },
    "v1-tools.css": {
        "ui-monospace,SFMono-Regular,Menlo,monospace",
    },
}


def normalized(value: str) -> str:
    return " ".join(value.split())


def shorthand_family_is_allowed(path: Path, value: str) -> bool:
    if value == "inherit":
        return True

    for tail in ALLOWED_SHORTHAND_TAILS.get(path.name, set()):
        if value.endswith(tail):
            return True

    match = TOKEN_AT_END_RE.search(value)
    if not match:
        return False

    # A canonical token must be the sole family tail. A comma immediately
    # before it means a direct fallback family was inserted ahead of the token
    # (e.g. "Arial, var(--font-ui)"), which must be reviewed explicitly.
    prefix = value[: match.start(1)].rstrip()
    return not prefix.endswith(",")


def main() -> None:
    failures: list[str] = []
    family_checked = 0
    shorthand_checked = 0

    for path in sorted(ASSETS.glob("v1*.css")):
        if path.name == "v1-fonts.css":
            continue

        css = COMMENT_RE.sub("", path.read_text(encoding="utf-8", errors="ignore"))

        for match in DECL_RE.finditer(css):
            family_checked += 1
            value = normalized(match.group(1))

            if TOKEN_RE.fullmatch(value):
                continue

            if value in ALLOWED_DIRECT.get(path.name, set()):
                continue

            failures.append(
                f"{path.relative_to(ROOT).as_posix()}: unexpected direct font-family {value!r}"
            )

        for match in SHORTHAND_RE.finditer(css):
            shorthand_checked += 1
            value = normalized(match.group(1))
            if shorthand_family_is_allowed(path, value):
                continue

            failures.append(
                f"{path.relative_to(ROOT).as_posix()}: font shorthand bypasses canonical family tokens: {value!r}"
            )

    if family_checked == 0:
        failures.append("no V1 font-family declarations found")
    if shorthand_checked == 0:
        failures.append("no V1 font shorthand declarations found")

    if failures:
        print("FAIL V1 font-family token contract:")
        for failure in failures[:50]:
            print(f" - {failure}")
        if len(failures) > 50:
            print(f" - ... {len(failures) - 50} more")
        raise SystemExit(1)

    print(
        "PASS V1 font-family token contract: "
        f"{family_checked} font-family + {shorthand_checked} font shorthand declaration(s) checked"
    )


if __name__ == "__main__":
    main()
