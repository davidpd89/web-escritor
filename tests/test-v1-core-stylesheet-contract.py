#!/usr/bin/env python3
"""Sitewide regression contract for the V1 core stylesheet stack.

Every tracked public HTML page that opts into the V1 system via class="v1"
must load the three canonical base stylesheets exactly once and in this order:
v1-fonts.css -> v1-tokens.css -> v1-base.css.

This protects new/generated pages from silently entering V1 with a partial or
misordered base stack.
"""
from __future__ import annotations

import posixpath
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PREFIXES = ("lab/", "tests/", "qa/", "data/", "scripts/templates/")
REQUIRED = (
    "assets/v1-fonts.css",
    "assets/v1-tokens.css",
    "assets/v1-base.css",
)


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.is_v1 = False
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {name.lower(): value or "" for name, value in attrs}
        if tag.lower() == "html":
            self.is_v1 = "v1" in data.get("class", "").split()
            return
        if tag.lower() != "link":
            return
        rel = {token.lower() for token in data.get("rel", "").split()}
        if "stylesheet" not in rel:
            return
        href = data.get("href", "").strip()
        if href:
            self.stylesheets.append(href)


def resolve_stylesheet(href: str, page_rel: str) -> str:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc:
        return ""
    if parsed.path.startswith("/"):
        return parsed.path.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(page_rel), parsed.path))


def tracked_public_html() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "*.html"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = result.stdout.decode("utf-8").split("\0")
    return [
        ROOT / rel
        for rel in paths
        if rel and not rel.startswith(EXCLUDED_PREFIXES)
    ]


def main() -> None:
    assert resolve_stylesheet("../assets/v1-base.css", "libros/index.html") == "assets/v1-base.css"
    assert resolve_stylesheet("/assets/v1-base.css?v=1", "libros/index.html") == "assets/v1-base.css"
    assert resolve_stylesheet("https://example.com/v1-base.css", "libros/index.html") == ""

    failures: list[str] = []
    v1_pages = 0

    for path in tracked_public_html():
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
        parser.close()

        if not parser.is_v1:
            continue

        v1_pages += 1
        rel = path.relative_to(ROOT).as_posix()
        stylesheets = [resolve_stylesheet(href, rel) for href in parser.stylesheets]

        positions: list[int] = []
        for required in REQUIRED:
            count = stylesheets.count(required)
            if count != 1:
                failures.append(
                    f"{rel}: {required} must appear exactly once as a stylesheet; found {count}"
                )
                continue
            positions.append(stylesheets.index(required))

        if len(positions) == len(REQUIRED) and positions != sorted(positions):
            failures.append(
                f"{rel}: V1 core stylesheet order must be "
                "v1-fonts.css -> v1-tokens.css -> v1-base.css"
            )

    if v1_pages == 0:
        failures.append("no public class=v1 pages found")

    if failures:
        print("FAIL V1 core stylesheet contract:")
        for failure in failures[:50]:
            print(f" - {failure}")
        if len(failures) > 50:
            print(f" - ... {len(failures) - 50} more")
        raise SystemExit(1)

    print(f"PASS V1 core stylesheet contract: {v1_pages} public V1 page(s) checked")


if __name__ == "__main__":
    main()
