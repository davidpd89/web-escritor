#!/usr/bin/env python3
"""Regression contract for V1 shell asset wiring.

The shell builder already owns the generated header/dialog/footer structure and
its explicit exemptions. This test covers a different failure mode: every page
that participates in that shell must also load the common shell stylesheet and
runtime script exactly once.
"""
from __future__ import annotations

import importlib.util
import posixpath
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "scripts" / "build-site-shell.py"

_spec = importlib.util.spec_from_file_location("build_site_shell", BUILDER_PATH)
builder = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = builder
_spec.loader.exec_module(builder)

REQUIRED_STYLESHEET = "assets/v1-shell.css"
REQUIRED_SCRIPT = "assets/v1-shell.js"


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stylesheets: list[str] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()

        if tag == "link":
            rel = {token.lower() for token in data.get("rel", "").split()}
            href = data.get("href", "").strip()
            if "stylesheet" in rel and href:
                self.stylesheets.append(href)
            return

        if tag == "script":
            src = data.get("src", "").strip()
            if src:
                self.scripts.append(src)


def resolve_local(ref: str, page_rel: str) -> str:
    parsed = urlsplit(ref)
    if parsed.scheme or parsed.netloc:
        return ""
    if parsed.path.startswith("/"):
        return parsed.path.lstrip("/")
    return posixpath.normpath(posixpath.join(posixpath.dirname(page_rel), parsed.path))


def main() -> None:
    assert resolve_local("../assets/v1-shell.css?v=4", "libros/index.html") == REQUIRED_STYLESHEET
    assert resolve_local("/assets/v1-shell.js?v=16", "libros/index.html") == REQUIRED_SCRIPT
    assert resolve_local("https://example.com/v1-shell.js", "index.html") == ""

    pages, _escapees = builder.collect_shell_pages(ROOT)
    assert pages, "build-site-shell.py: no V1 shell pages found"

    failures: list[str] = []

    for path in pages:
        rel = path.relative_to(ROOT).as_posix()
        parser = AssetParser()
        parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
        parser.close()

        stylesheets = [resolve_local(ref, rel) for ref in parser.stylesheets]
        scripts = [resolve_local(ref, rel) for ref in parser.scripts]

        css_count = stylesheets.count(REQUIRED_STYLESHEET)
        js_count = scripts.count(REQUIRED_SCRIPT)

        if css_count != 1:
            failures.append(
                f"{rel}: {REQUIRED_STYLESHEET} must appear exactly once; found {css_count}"
            )
        if js_count != 1:
            failures.append(
                f"{rel}: {REQUIRED_SCRIPT} must appear exactly once; found {js_count}"
            )

    if failures:
        print("FAIL V1 shell asset contract:")
        for failure in failures[:50]:
            print(f" - {failure}")
        if len(failures) > 50:
            print(f" - ... {len(failures) - 50} more")
        raise SystemExit(1)

    print(f"PASS V1 shell asset contract: {len(pages)} shell page(s) checked")


if __name__ == "__main__":
    main()
