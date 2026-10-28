#!/usr/bin/env python3
"""Regression contract: public runtime typography must stay self-hosted.

The site CSP already declares style-src/font-src 'self'. This test makes the
same policy deterministic before browser runtime: public HTML may not load a
remote stylesheet/font preload, and public CSS may not import remote CSS or
source a @font-face from a remote URL. Ordinary external links/images are out
of scope.
"""
from __future__ import annotations

import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PREFIXES = ("lab/", "tests/", "qa/", "data/", "docs/", "scripts/")
CANONICAL_ORIGIN = ("https", "davidportodiaz.com", 443)

CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
IMPORT_RE = re.compile(
    r"@import\s+(?:url\(\s*)?(['\"]?)([^'\"\)\s;]+)\1\s*\)?",
    re.IGNORECASE,
)
FONT_FACE_RE = re.compile(r"@font-face\s*\{([^{}]*)\}", re.IGNORECASE | re.DOTALL)
CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)


def is_nonlocal(ref: str) -> bool:
    ref = ref.strip()
    if not ref:
        return False

    if ref.startswith("//"):
        ref = "https:" + ref

    parsed = urlsplit(ref)
    if not parsed.scheme and not parsed.netloc:
        return False

    effective_port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    return (
        parsed.scheme.lower(),
        (parsed.hostname or "").lower(),
        effective_port,
    ) != CANONICAL_ORIGIN


def css_runtime_font_refs(css: str) -> list[tuple[int, str, str]]:
    """Return (line, kind, ref) for non-local font/style runtime references."""
    cleaned = CSS_COMMENT_RE.sub("", css)
    refs: list[tuple[int, str, str]] = []

    for match in IMPORT_RE.finditer(cleaned):
        ref = match.group(2).strip()
        if is_nonlocal(ref):
            line = cleaned.count("\n", 0, match.start()) + 1
            refs.append((line, "@import", ref))

    for face in FONT_FACE_RE.finditer(cleaned):
        body = face.group(1)
        for match in CSS_URL_RE.finditer(body):
            ref = match.group(2).strip()
            if is_nonlocal(ref):
                absolute_start = face.start(1) + match.start()
                line = cleaned.count("\n", 0, absolute_start) + 1
                refs.append((line, "@font-face", ref))

    return refs


class RuntimeFontHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.remote_refs: list[tuple[int, str, str]] = []
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
        as_value = data.get("as", "").strip().lower()
        kind = ""
        if "stylesheet" in rel:
            kind = "stylesheet"
        elif "preload" in rel and as_value in {"style", "font"}:
            kind = f"preload as={as_value}"

        href = data.get("href", "").strip()
        if kind and is_nonlocal(href):
            self.remote_refs.append((self.getpos()[0], kind, href))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "style" and self._style_depth:
            self._style_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._style_depth:
            return
        for offset, kind, ref in css_runtime_font_refs(data):
            self.remote_refs.append((self._style_line + offset - 1, kind, ref))


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
    assert is_nonlocal("https://api.fontshare.com/v2/css") is True
    assert is_nonlocal("//cdn.example.net/font.woff2") is True
    assert is_nonlocal("http://davidportodiaz.com/assets/fonts/manrope.woff2") is True
    assert is_nonlocal("https://davidportodiaz.com/assets/fonts/manrope.woff2") is False
    assert is_nonlocal("https://davidportodiaz.com:443/assets/fonts/manrope.woff2") is False
    assert is_nonlocal("https://davidportodiaz.com:444/assets/fonts/manrope.woff2") is True
    assert is_nonlocal("//davidportodiaz.com/assets/fonts/manrope.woff2") is False
    assert is_nonlocal("/assets/fonts/manrope.woff2") is False
    assert is_nonlocal("../fonts/manrope.woff2") is False

    parser = RuntimeFontHTMLParser()
    parser.feed(
        '<link rel="stylesheet" href="https://unknown.example/fonts.css">'
        '<a href="https://unknown.example/fonts.css">Documentación</a>'
    )
    parser.close()
    assert len(parser.remote_refs) == 1, "remote runtime stylesheet must be caught without flagging a normal link"

    refs = css_runtime_font_refs(
        "/* @import 'https://ignored.example/font.css'; */"
        "@import url('https://new-font-provider.example/family.css');"
        "@font-face{font-family:X;src:url(https://cdn.example.net/x.woff2) format('woff2')}"
        ".hero{background:url(https://images.example.net/hero.jpg)}"
    )
    assert [(kind, ref) for _line, kind, ref in refs] == [
        ("@import", "https://new-font-provider.example/family.css"),
        ("@font-face", "https://cdn.example.net/x.woff2"),
    ], "only remote style imports/font-face sources belong to this contract"


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
        for line, kind, ref in parser.remote_refs:
            failures.append(f"{rel}:{line}: non-local {kind}: {ref}")

    for path in css_files:
        rel = path.relative_to(ROOT).as_posix()
        css = path.read_text(encoding="utf-8", errors="ignore")
        for line, kind, ref in css_runtime_font_refs(css):
            failures.append(f"{rel}:{line}: non-local {kind}: {ref}")

    if failures:
        print("FAIL self-hosted font runtime contract:")
        for failure in failures[:50]:
            print(f" - {failure}")
        if len(failures) > 50:
            print(f" - ... {len(failures) - 50} more")
        raise SystemExit(1)

    print(
        "PASS self-hosted font runtime contract: "
        f"{len(html_files)} HTML + {len(css_files)} CSS file(s) checked"
    )


if __name__ == "__main__":
    main()
