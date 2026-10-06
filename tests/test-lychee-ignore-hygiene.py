#!/usr/bin/env python3
"""Keep .lycheeignore honest.

Every line in that file is a link the external-link check will never look at
again, so the file is where a dead link goes to hide. Four things are enforced:

1. no duplicate patterns;
2. every pattern is a valid regex (an invalid one silences nothing and nobody
   notices);
3. a pattern that names one concrete URL is anchored with ^...$ -- lychee
   matches these as unanchored regexes, so an exception written for
   `https://doi.org/10.1016/j.rmal.2024.100168` would also silence
   `.../100168-anything`. Domain-wide patterns (ending in `/.*`) are exempt by
   design: they exist precisely to cover a whole host;
4. an anchored exception still matches a URL this repo actually publishes --
   once the page that cited it is gone, the exception is just an unchecked hole.

Scope note: this walks `git ls-files`, excluding scripts/ and tests/, because
that is exactly what the workflow feeds lychee (`./**/*.html` on a clean
checkout, with those two paths excluded). Using the filesystem instead would
make the result depend on whatever untracked HTML a given working copy has.
"""
from __future__ import annotations

import html
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORE = ROOT / ".lycheeignore"
URL_RE = re.compile(r"https?://[^\s\"'<>)]+")
# Mirrors --exclude-path in .github/workflows/broken-links.yml.
EXCLUDED_PREFIXES = ("scripts/", "tests/")


def checked_html() -> list[Path]:
    listed = subprocess.run(
        ["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [
        ROOT / rel
        for rel in listed
        if rel and not rel.startswith(EXCLUDED_PREFIXES) and (ROOT / rel).is_file()
    ]


def public_urls() -> set[str]:
    urls: set[str] = set()
    for path in checked_html():
        # The URLs live in href attributes, so `&` arrives as `&amp;`. Without
        # unescaping, every exception for a query string with more than one
        # parameter looks unused -- which would have had us delete eight live
        # exceptions the first time this ran.
        text = html.unescape(path.read_text(encoding="utf-8", errors="strict"))
        urls.update(URL_RE.findall(text))
    return urls


def main() -> int:
    lines = IGNORE.read_text(encoding="utf-8").splitlines()
    exact: list[tuple[int, str]] = []
    seen: dict[str, int] = {}
    errors: list[str] = []

    for line_no, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line in seen:
            errors.append(f".lycheeignore:{line_no}: duplicate pattern; first at line {seen[line]}")
        else:
            seen[line] = line_no

        try:
            re.compile(line)
        except re.error as exc:
            errors.append(f".lycheeignore:{line_no}: invalid regex: {exc}")
            continue

        if line.endswith("/.*"):
            # Domain-wide on purpose; nothing to anchor and nothing to expire.
            continue

        if not (line.startswith("^") and line.endswith("$")):
            errors.append(
                f".lycheeignore:{line_no}: single-URL exception must be anchored with ^...$ "
                f"or it silences every URL starting with it: {line}"
            )
            continue

        exact.append((line_no, line))

    urls = public_urls()
    for line_no, pattern in exact:
        rx = re.compile(pattern)
        if not any(rx.fullmatch(url) for url in urls):
            errors.append(
                f".lycheeignore:{line_no}: exact exception no longer matches any URL "
                f"published in HTML: {pattern}"
            )

    if errors:
        print(f"FAIL lychee ignore hygiene: {len(errors)} issue(s)")
        for error in errors:
            print(error)
        return 1

    print(
        f"PASS lychee ignore hygiene: {len(seen)} patterns, "
        f"{len(exact)} exact exceptions all still referenced"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
