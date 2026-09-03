#!/usr/bin/env python3
"""Validate the heading outline and skip-link contract inside <main>.

Three invariants, all of them things that broke silently at least once and
that no other gate covers:

1. Each page's <main> starts at <h1>, has exactly one, and never skips a
   level on the way down (h1 -> h3 with no h2 in between). Screen reader
   users navigate by heading level, so a gap hides the structure from them.
2. A page whose skip link points at #id must contain that id, and the
   target must be focusable (tabindex). Without it the browser scrolls but
   focus stays on <body>, so the region is never announced.
3. Every <img> carries alt, and every form field has an accessible name
   (wrapping <label>, <label for>, aria-label, aria-labelledby or title).

Headings in the header, the Explorar dialog and the footer are deliberately
out of scope: they sit outside <main> and legitimately precede the h1.

Python standard library only.

Usage:
    python scripts/check-heading-structure.py
    python scripts/check-heading-structure.py --root .
"""
from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path

SKIP_PARTS = {
    ".git", ".github", "node_modules", "tests", "vendor",
    "WEB DAVID PORTO nuevas ideas", "archive", ".codex_work",
    ".preview-dist", "dist", "lab", ".claude",
}

VOID = {
    "input", "img", "br", "hr", "meta", "link", "source", "area",
    "col", "embed", "track", "wbr", "param", "base",
}

NON_NAMED_INPUT_TYPES = {"hidden", "submit", "button", "reset", "image"}


class PageParser(HTMLParser):
    """Collect what the three checks need in a single pass."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.main_depth: int | None = None
        self.main_attrs: dict[str, str] = {}
        self.headings: list[tuple[int, int]] = []   # (level, line) inside <main>
        self.ids: set[str] = set()
        self.focusable_ids: set[str] = set()
        self.skip_targets: list[tuple[str, int]] = []
        self.label_for: set[str] = set()
        self.imgs_no_alt: list[int] = []
        self.unnamed_fields: list[tuple[str, int]] = []

    def handle_starttag(self, tag, attrs) -> None:
        tag = tag.lower()
        data = {k.lower(): (v or "") for k, v in attrs}
        line = self.getpos()[0]

        if data.get("id"):
            self.ids.add(data["id"])
            if "tabindex" in data:
                self.focusable_ids.add(data["id"])

        if tag == "main" and self.main_depth is None:
            self.main_depth = len(self.stack)
            self.main_attrs = data

        if tag == "a":
            href = data.get("href", "")
            classes = data.get("class", "")
            if href.startswith("#") and "skip-link" in classes:
                self.skip_targets.append((href[1:], line))

        if tag == "label" and data.get("for"):
            self.label_for.add(data["for"])

        if tag == "img" and "alt" not in data:
            self.imgs_no_alt.append(line)

        if tag in ("input", "select", "textarea"):
            kind = (data.get("type") or "text").lower()
            if kind not in NON_NAMED_INPUT_TYPES:
                # A <label for> may appear after the field, so the id is
                # resolved against label_for once the whole page is parsed.
                named_here = bool(
                    data.get("aria-label")
                    or data.get("aria-labelledby")
                    or data.get("title")
                    or "label" in self.stack
                )
                if not named_here:
                    self.unnamed_fields.append((data.get("id", ""), line))

        if re.fullmatch(r"h[1-6]", tag) and self.in_main():
            self.headings.append((int(tag[1]), line))

        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag) -> None:
        tag = tag.lower()
        if tag not in self.stack:
            return
        while self.stack:
            popped = self.stack.pop()
            if popped == tag:
                break
        if self.main_depth is not None and len(self.stack) < self.main_depth:
            self.main_depth = -1  # closed; never reopen

    def in_main(self) -> bool:
        return self.main_depth is not None and self.main_depth >= 0 and "main" in self.stack


def is_noindex(text: str) -> bool:
    m = re.search(
        r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']',
        text, flags=re.I,
    )
    return bool(m and "noindex" in m.group(1).lower())


def audit(path: Path, root: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = path.relative_to(root).as_posix()
    parser = PageParser()
    try:
        parser.feed(text)
    except Exception as exc:  # malformed markup is itself worth reporting
        return [f"{rel}: no se pudo analizar el HTML ({exc})"]

    errors: list[str] = []
    indexable = not is_noindex(text)

    # 1. Heading outline inside <main>.
    levels = [lvl for lvl, _ in parser.headings]
    if indexable and parser.main_attrs:
        if levels.count(1) != 1:
            errors.append(f"{rel}: <main> debe tener exactamente un <h1> (tiene {levels.count(1)})")
        if levels and levels[0] != 1:
            line = parser.headings[0][1]
            errors.append(f"{rel}:{line}: el primer encabezado de <main> es h{levels[0]}, debe ser h1")
    previous = None
    for level, line in parser.headings:
        if previous is not None and level > previous + 1:
            errors.append(f"{rel}:{line}: salto de encabezado h{previous} -> h{level}")
        previous = level

    # 2. Skip link must resolve to a focusable target.
    for target, line in parser.skip_targets:
        if target not in parser.ids:
            errors.append(f"{rel}:{line}: el skip link apunta a #{target}, que no existe")
        elif target not in parser.focusable_ids:
            errors.append(
                f"{rel}:{line}: #{target} necesita tabindex para recibir el foco "
                f"desde el skip link"
            )

    # 3. Alt text and accessible names.
    for line in parser.imgs_no_alt:
        errors.append(f"{rel}:{line}: <img> sin atributo alt")
    for field_id, line in parser.unnamed_fields:
        if field_id and field_id in parser.label_for:
            continue
        errors.append(f"{rel}:{line}: campo de formulario sin nombre accesible")

    return errors


def find_html_files(root: Path):
    for path in sorted(root.rglob("*.html")):
        if any(part in SKIP_PARTS for part in path.relative_to(root).parts):
            continue
        yield path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    all_errors: list[str] = []
    scanned = 0
    for path in find_html_files(root):
        scanned += 1
        all_errors.extend(audit(path, root))

    for e in all_errors:
        print(f"ERROR {e}")

    print(
        f"\nHeading/skip-link structure: {scanned} ficheros HTML revisados; "
        f"{len(all_errors)} problema(s)."
    )
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
