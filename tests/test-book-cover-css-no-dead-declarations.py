#!/usr/bin/env python3
"""Regression guard for a real dead-CSS bug found in the 2026-09 audit round.

assets/v1-book.css's single "@media (max-width:899px)" block declared
.book-cover-zone/.book-cover/.book-cover-fallback TWICE: once early in the
block with max-width/width:16rem, then again later in the SAME block with
14rem. The 16rem declarations were 100% dead (always overridden by source
order within the same cascade context) -- confirmed by removing them and
checking the resulting computed style is unchanged. This guards against
that specific dead-declaration pattern reappearing for these selectors.

This is intentionally narrow (one file, three selectors) rather than a
general "no duplicate CSS selectors" linter: this codebase legitimately
repeats a selector often (e.g. a shared-properties group rule followed by
an individual-properties rule), which is normal, valid CSS, not a bug --
a general duplicate-selector checker would be mostly false positives.
What actually matters is duplicate declarations of the SAME property for
the SAME selector within the SAME cascade context, which this checks for
directly on the one file/selectors where it was a real, reproduced bug.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_PATH = ROOT / "assets" / "v1-book.css"
WATCHED_SELECTORS = {"html.v1 .book-cover-zone", "html.v1 .book-cover", "html.v1 .book-cover-fallback"}


def split_top_level_commas(s: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    buf = ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    parts.append(buf)
    return parts


def prop_names(declblock: str) -> set[str]:
    props: set[str] = set()
    depth = 0
    buf = ""
    for ch in declblock:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == ";" and depth == 0:
            s = buf.strip()
            if ":" in s:
                props.add(s.split(":", 1)[0].strip().lower())
            buf = ""
        else:
            buf += ch
    s = buf.strip()
    if ":" in s:
        props.add(s.split(":", 1)[0].strip().lower())
    return props


def find_property_overlaps(css: str) -> list[tuple[str, str, set[str]]]:
    """Returns (context, selector, overlapping_props) for any selector that
    redeclares a property it already declared earlier in the same context."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    findings = []
    context_stack: list[str] = []
    seen_stack = [defaultdict(list)]
    i, n = 0, len(css)
    buf = ""
    paren_depth = 0
    while i < n:
        ch = css[i]
        if ch == "(":
            paren_depth += 1
            buf += ch
            i += 1
            continue
        if ch == ")":
            paren_depth -= 1
            buf += ch
            i += 1
            continue
        if ch == "{" and paren_depth == 0:
            prelude = buf.strip()
            buf = ""
            if prelude.startswith("@"):
                context_stack.append(prelude)
                seen_stack.append(defaultdict(list))
                i += 1
                continue
            depth = 1
            j = i + 1
            start = j
            while j < n and depth > 0:
                if css[j] == "{":
                    depth += 1
                elif css[j] == "}":
                    depth -= 1
                j += 1
            declblock = css[start:j - 1]
            props = prop_names(declblock)
            ctx = " > ".join(context_stack) or "(top level)"
            for sel in (s.strip() for s in split_top_level_commas(prelude) if s.strip()):
                for prior_props in seen_stack[-1][sel]:
                    overlap = prior_props & props
                    if overlap:
                        findings.append((ctx, sel, overlap))
                seen_stack[-1][sel].append(props)
            i = j
            continue
        if ch == "}":
            if context_stack:
                context_stack.pop()
            if len(seen_stack) > 1:
                seen_stack.pop()
            buf = ""
            i += 1
            continue
        buf += ch
        i += 1
    return findings


def main() -> int:
    css = CSS_PATH.read_text(encoding="utf-8")
    findings = [f for f in find_property_overlaps(css) if f[1] in WATCHED_SELECTORS]
    if findings:
        for ctx, sel, overlap in findings:
            print(f"FAIL: {sel!r} in {ctx} redeclares already-set propert(y/ies) {sorted(overlap)} "
                  f"-- the earlier declaration is dead code (or, if intentional, this file needs a "
                  f"real design decision documented, not a silent duplicate).")
        return 1
    print("tests/test-book-cover-css-no-dead-declarations: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
