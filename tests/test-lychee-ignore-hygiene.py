#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORE = ROOT / ".lycheeignore"
URL_RE = re.compile(r"https?://[^\s\"'<>)]+")


def public_urls() -> set[str]:
    urls: set[str] = set()
    for path in ROOT.rglob("*.html"):
        parts = set(path.relative_to(ROOT).parts)
        if parts & {".git", "node_modules", "artifacts", ".preview-dist", ".preview-dist-ci"}:
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
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

        if line.startswith("^https://") and line.endswith("$"):
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
