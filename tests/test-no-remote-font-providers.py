#!/usr/bin/env python3
"""Regression contract: public runtime typography must stay self-hosted.

The V1 font sheet documents a real regression where remote Google Fonts delayed
font discovery and contributed to layout shifts. This test prevents public HTML
or CSS from reintroducing common remote font-provider hosts while allowing
ordinary external links elsewhere on the site.
"""
from __future__ import annotations

import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PREFIXES = ("lab/", "tests/", "qa/", "data/", "docs/", "scripts/")

FORBIDDEN_FONT_HOSTS = {
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "use.typekit.net",
    "p.typekit.net",
    "fonts.bunny.net",
}

CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
URL_RE = re.compile(r"(?:https?:)?//[^\s'\"\)<>]+", re.IGNORECASE)


def forbidden_host(url: str) -> str | None:
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    for forbidden in FORBIDDEN_FONT_HOSTS:
        if host == forbidden or host.endswith("." + forbidden):
            return host
    return None


class RuntimeFontHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.remote_font_refs: list[tuple[int, str]] = []
        self._style_depth = 0
        self._style_line = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        data = {name.lower(): (value or "") for name, value in attrs}

        if tag == "style":
            self._style_depth += 1
            self._style_line = self.getpos()[0]
            return

        if tag != "link":
            return

        rel = {token.lower() for token in data.get("rel", "").split()}
        as_value = data.get("as", "").lower()
        is_runtime_style_or_font = "stylesheet" in rel or (
            "preload" in rel and as_value in {"style", "font"}
        )
        if not is_runtime_style_or_font:
            return

        href = data.get("href", "").strip()
        host = forbidden_host(href)
        if host:
            self.remote_font_refs.append((self.getpos()[0], href))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "style" and self._style_depth:
            self._style_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._style_depth:
            return
        cleaned = CSS_COMMENT_RE.sub("", data)
        for match in URL_RE.finditer(cleaned):
            url = match.group(0)
            host = forbidden_host(url)
            if host:
                self.remote_font_refs.append((self._style_line, url))


def tracked_files(pattern: str) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", pattern],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [
        ROOT / rel
        for rel in result.stdout.decode("utf-8").split("\0")
        if rel and not rel.startswith(EXCLUDED_PREFIXES)
    ]


def self_check() -> None:
    assert forbidden_host("https://fonts.googleapis.com/css2?family=Manrope") == "fonts.googleapis.com"
    assert forbidden_host("//fonts.gstatic.com/s/manrope/example.woff2") == "fonts.gstatic.com"
    assert forbidden_host("https://example.com/fonts.css") is None

    parser = RuntimeFontHTMLParser()
    parser.feed(
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope">'
        '<a href="https://fonts.googleapis.com/">Documentación</a>'
    )
    parser.close()
    assert len(parser.remote_font_refs) == 1, "runtime stylesheet must be caught without flagging a normal link"

    cleaned = CSS_COMMENT_RE.sub(
        "",
        "/* https://fonts.googleapis.com/ignored */ "
        "@import url('https://fonts.bunny.net/css?family=Manrope');",
    )
    detected = [forbidden_host(match.group(0)) for match in URL_RE.finditer(cleaned)]
    assert detected == ["fonts.bunny.net"], "CSS comments must be ignored and runtime import detected"


def main() -> None:
    self_check()
    failures: list[str] = []
    html_files = tracked_files("*.html")
    css_files = tracked_files("*.css")

    for path in html_files:
        parser = RuntimeFontHTMLParser()
        parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
        parser.close()
        rel = path.relative_to(ROOT).as_posix()
        for line, url in parser.remote_font_refs:
            failures.append(f"{rel}:{line}: remote font runtime reference: {url}")

    for path in css_files:
        rel = path.relative_to(ROOT).as_posix()
        cleaned = CSS_COMMENT_RE.sub("", path.read_text(encoding="utf-8", errors="ignore"))
        for match in URL_RE.finditer(cleaned):
            url = match.group(0)
            host = forbidden_host(url)
            if host:
                line = cleaned.count("\n", 0, match.start()) + 1
                failures.append(f"{rel}:{line}: remote font provider reference: {url}")

    if failures:
        print("FAIL remote font provider contract:")
        for failure in failures[:50]:
            print(f" - {failure}")
        if len(failures) > 50:
            print(f" - ... {len(failures) - 50} more")
        raise SystemExit(1)

    print(
        "PASS remote font provider contract: "
        f"{len(html_files)} HTML + {len(css_files)} CSS file(s) checked"
    )


if __name__ == "__main__":
    main()
