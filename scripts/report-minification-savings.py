#!/usr/bin/env python3
"""Report-only: measure the realistic byte savings of minifying
script.js/styles.css, both raw and after gzip.

Context: index.html loads script.js (~44 KB) and styles.css (~122 KB)
unminified, on every page of the site, and there is no build step (no
bundler, no package.json wiring a minifier) -- GitHub Pages serves these
files exactly as committed. This script measures what minifying them would
actually be worth, honestly:

- Raw savings: how many fewer bytes ship if whitespace/comments are
  stripped. This is the number most people quote, and it overstates the
  real-world benefit, because...
- Gzip savings: GitHub Pages already serves these compressed. Gzip is very
  good at compressing repeated whitespace, so the MARGINAL savings from
  minifying on top of gzip is usually much smaller than the raw number
  suggests. This is the number that actually matches what a visitor's
  browser downloads.

CSS is minified here with a conservative, safe regex pass (strip /* */
comments, collapse whitespace, drop the last `;` before `}`) -- CSS's
grammar makes this reliable. JS is NOT minified by this script: a correct
JS minifier has to be a real parser (template literals, regex literals,
ASI, comments-that-look-like-code-inside-strings all break a naive regex
approach), and this repo intentionally has no JS build dependency yet (see
docs/PENDIENTE-K-MINIFICATION-REPORT.md for why). Reporting a fake "minified"
JS size here would be worse than not reporting one. JS gzip savings alone
are still measured and are the more meaningful number anyway.

Python standard library only.

Usage:
    python scripts/report-minification-savings.py
    python scripts/report-minification-savings.py --root .
"""
from __future__ import annotations

import argparse
import gzip
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
CSS_WHITESPACE_RE = re.compile(r"[ \t\r\n]+")
CSS_TRAILING_SEMI_RE = re.compile(r";\s*}")
CSS_SPACE_AROUND_RE = re.compile(r"\s*([{}:;,])\s*")


def gzip_size(text: str) -> int:
    return len(gzip.compress(text.encode("utf-8"), compresslevel=9))


def minify_css(text: str) -> str:
    text = CSS_COMMENT_RE.sub("", text)
    text = CSS_WHITESPACE_RE.sub(" ", text)
    text = CSS_SPACE_AROUND_RE.sub(r"\1", text)
    text = CSS_TRAILING_SEMI_RE.sub("}", text)
    return text.strip()


def fmt(n: int) -> str:
    return f"{n / 1024:.1f} KB"


def pct(before: int, after: int) -> str:
    if before == 0:
        return "n/a"
    return f"{(1 - after / before) * 100:.1f}%"


def report_css(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    minified = minify_css(original)
    orig_bytes = len(original.encode("utf-8"))
    min_bytes = len(minified.encode("utf-8"))
    orig_gzip = gzip_size(original)
    min_gzip = gzip_size(minified)
    rel = path.relative_to(ROOT).as_posix()
    print(f"\n{rel}")
    print(f"  raw:   {fmt(orig_bytes):>10} -> {fmt(min_bytes):>10}  ({pct(orig_bytes, min_bytes)} smaller)")
    print(f"  gzip:  {fmt(orig_gzip):>10} -> {fmt(min_gzip):>10}  ({pct(orig_gzip, min_gzip)} smaller)  <- what a visitor actually downloads today vs. after minifying")


def report_js_gzip_only(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    orig_bytes = len(original.encode("utf-8"))
    orig_gzip = gzip_size(original)
    rel = path.relative_to(ROOT).as_posix()
    print(f"\n{rel}")
    print(f"  raw:   {fmt(orig_bytes):>10} (unminified; not safely regex-minifiable, see docstring)")
    print(f"  gzip:  {fmt(orig_gzip):>10}  <- what a visitor actually downloads today")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args()
    root = Path(args.root).resolve()

    print("Minification savings report (raw vs. gzip) -- report-only, nothing written to disk.")
    report_css(root / "styles.css")
    report_js_gzip_only(root / "script.js")
    print(
        "\nNote: gzip savings from minifying are the realistic number -- GitHub Pages "
        "already serves these files compressed, and gzip already collapses most of the "
        "whitespace/comment overhead minification would otherwise remove."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
