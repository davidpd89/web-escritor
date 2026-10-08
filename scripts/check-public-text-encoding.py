#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "data/content-registry.json").read_text(encoding="utf-8"))
DEFAULTS = REGISTRY.get("defaults", {})

MOJIBAKE = (
    "\ufffd",   # Unicode replacement character
    "Ã",        # UTF-8 decoded as Windows-1252/Latin-1
    "Â",
    "â€",
    "â€™",
    "â€œ",
    "â€\x9d",
    "ðŸ",
    "ï»¿",
)

class EarlyUtf8Meta(HTMLParser):
    """Locate a real UTF-8 meta declaration, not one inside a comment/script."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "meta" and any(
            key.lower() == "charset" and (value or "").strip().lower() == "utf-8"
            for key, value in attrs
        ):
            self.found = True

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def has_early_utf8_meta(raw: bytes) -> bool:
    """The complete encoding declaration must fit in the first 1024 BYTES."""
    parser = EarlyUtf8Meta()
    # Meta syntax is ASCII. Truncate before decoding: multibyte text must not
    # move the browser's 1024-byte discovery boundary.
    parser.feed(raw[:1024].decode("ascii", errors="ignore"))
    parser.close()
    return parser.found


def public_files() -> list[Path]:
    files: set[Path] = set()
    for raw in REGISTRY.get("entries", []):
        item = {**DEFAULTS, **raw}
        if item.get("status") != "public":
            continue
        source = item.get("sourceFile")
        if source:
            p = ROOT / source
            if p.is_file():
                files.add(p)
    for name in (
        "404.html", "robots.txt", "humans.txt", "llms.txt", "llms-full.txt",
        "manifest.json", "service-worker.js", "sitemap.xml", "editoriales-sitemap.xml",
        "convocatorias-escritores/opportunities.json",
        "convocatorias-escritores/deadlines.ics",
        "editoriales/editoriales-data.json",
    ):
        p = ROOT / name
        if p.is_file():
            files.add(p)
    return sorted(files)

errors: list[str] = []
checked = 0
for path in public_files():
    rel = path.relative_to(ROOT).as_posix()
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"{rel}: invalid UTF-8 at byte {exc.start}")
        continue
    checked += 1

    for token in MOJIBAKE:
        if token in text:
            line = text[: text.index(token)].count("\n") + 1
            errors.append(f"{rel}:{line}: suspicious mojibake token {token!r}")

    if path.suffix.lower() in {".html", ".htm"}:
        if not has_early_utf8_meta(raw):
            errors.append(f"{rel}: public HTML lacks a real UTF-8 meta charset in its first 1024 bytes")

    if path.suffix.lower() == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}:{exc.lineno}: invalid JSON: {exc.msg}")

if errors:
    print("PUBLIC TEXT ENCODING: FAIL")
    for error in errors:
        print(" -", error)
    sys.exit(1)

print(f"PUBLIC TEXT ENCODING: PASS ({checked} public artifacts)")
