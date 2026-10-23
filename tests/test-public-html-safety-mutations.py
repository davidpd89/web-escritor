#!/usr/bin/env python3
"""Mutation fixtures for the existing public HTML safety checker.

The positive and negative cases verify the parser contract without relying on
current production pages. The Required merge gate runs tests/test-*.py.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-public-html-safety.py"
spec = importlib.util.spec_from_file_location("public_html_safety_checker", CHECKER)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def findings(markup: str) -> list[str]:
    parser = checker.AuditParser("fixture.html")
    parser.feed(markup)
    parser.close()
    return parser.errors


BAD_CASES = (
    ("noopener missing", '<a href="https://example.org/" target="_blank">Go</a>', "noopener"),
    ("image alt missing", '<img src="/cover.webp">', "without alt"),
    ("iframe title missing", '<iframe src="https://example.org/video" title=""></iframe>', "title"),
    ("unsafe JavaScript form", '<form action="JaVaScRiPt:alert(1)"></form>', "javascript:"),
    ("protocol-relative image", '<img src="//cdn.example.org/image.webp" alt="">', "protocol-relative"),
    ("HTTP script", '<script src="http://cdn.example.org/script.js"></script>', "mixed-content"),
    ("unsafe meta refresh", '<meta http-equiv="refresh" content="0; URL=javascript:alert(1)">', "unsafe meta refresh"),
    ("self-closing img without alt", '<img src="/photo.webp" />', "without alt"),
    ("source srcset mixed-content second candidate", '<source srcset="/safe.webp 1x, http://cdn.example.org/unsafe.webp 2x">', "mixed-content srcset"),
    ("responsive img protocol-relative second candidate", '<img src="/safe.webp" srcset="/safe.webp 400w, //cdn.example.org/unsafe.webp 800w" alt="">', "protocol-relative"),
    ("preload imagesrcset mixed content", '<link rel="preload" as="image" imagesrcset="/ok.webp 1x, http://cdn.example.org/bad.webp 2x">', "mixed-content imagesrcset"),
    ("srcset javascript candidate", '<source srcset="javascript:alert(1) 1x, /ok.webp 2x">', "srcset uses javascript:"),
    ("unquoted uppercase source", '<SOURCE SRCSET=HTTP://cdn.example.org/cover.webp>', "mixed-content srcset"),
    ("HTML entity in source URL", '<source srcset="&#104;ttp://cdn.example.org/image.webp 1x">', "mixed-content srcset"),
    ("encoded source URL in standard src", '<img src="http&#58;//cdn.example.org/cover.webp" alt="">', "mixed-content src"),
)

GOOD_CASES = (
    ("safe new-tab link", '<a href="https://example.org/" target="_blank" rel="noopener noreferrer">Go</a>'),
    ("decorative alt", '<img src="/cover.webp" alt="" />'),
    ("titled iframe", '<iframe src="https://example.org/video" title="Vídeo"></iframe>'),
    ("relative meta refresh", '<meta http-equiv="refresh" content="0; URL=/inicio/">'),
    ("comments ignored", '<!-- <img src="http://example.org/evil.png"> -->'),
    ("safe multi-candidate srcset", '<source srcset="/small.webp 400w, /large.webp 800w">'),
    ("HTTPS preload imagesrcset", '<link rel=preload as=image imagesrcset="https://cdn.example.org/img.webp 1x, /larger.webp 2x">'),
    ("data URL containing comma", '<img alt="" srcset="data:image/png;base64,AAAAAA 1x, /cover.webp 2x">'),
    ("URL with comma inside candidate", '<source srcset="/crop,left.webp 1x, /crop,right.webp 2x">'),
)

errors: list[str] = []
for label, markup, expected in BAD_CASES:
    actual = findings(markup)
    if not any(expected in message for message in actual):
        errors.append(f"{label}: expected {expected!r}, got {actual!r}")

for label, markup in GOOD_CASES:
    actual = findings(markup)
    if actual:
        errors.append(f"{label}: unexpected violations {actual!r}")

if errors:
    print("FAIL public HTML safety mutation fixtures")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)

print(f"PASS public HTML safety mutation fixtures: {len(BAD_CASES)} negative + {len(GOOD_CASES)} positive")
