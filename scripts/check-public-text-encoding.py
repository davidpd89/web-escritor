#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "data/content-registry.json").read_text(encoding="utf-8"))
DEFAULTS = REGISTRY.get("defaults", {})

MOJIBAKE = (
    "�",   # Unicode replacement character
    "â€",       # UTF-8 decoded as Windows-1252/Latin-1 (comillas, guiones, euro)
    "ðŸ",
    "ï»¿",
)

# «Ã» y «Â» sueltas son letras legítimas (Âsanas, Mândûkyakârikâ, SÃO PAULO): solo son mojibake cuando les
# sigue lo que Windows-1252 pone en lugar de un byte de continuación UTF-8 («Â·», «Â », «Ã©», «Ã±»).
_CONTINUATION = ''.join(chr(c) for c in (*range(0x80, 0xC0), *range(0x2013, 0x203B), 0x152, 0x153, 0x160, 0x161, 0x178, 0x17D, 0x17E, 0x192, 0x2C6, 0x2DC, 0x20AC, 0x2122))
MOJIBAKE_LEAD = re.compile('[' + chr(0xC3) + chr(0xC2) + '][' + re.escape(_CONTINUATION) + ']')


def mojibake_hits(text: str):
    """(señal, posición) de cada resto de codificación rota en el texto."""
    for token in MOJIBAKE:
        at = text.find(token)
        if at >= 0:
            yield token, at
    found = MOJIBAKE_LEAD.search(text)
    if found:
        yield found.group(), found.start()

# Parse the serialized <meta> tag: HTMLParser decodes character references in
# attribute values, but charset declarations may not contain character refs.
RAW_ATTRIBUTE = re.compile(
    r'''\s+([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?'''
)


def literal_meta_charset(starttag: str) -> str | None:
    tail = starttag[5:]
    pos = 0
    while pos < len(tail):
        match = RAW_ATTRIBUTE.match(tail, pos)
        if match is None:
            break
        name, quoted_double, quoted_single, unquoted = match.groups()
        if name.lower() == "charset":
            return next((v for v in (quoted_double, quoted_single, unquoted)
                         if v is not None), "")
        pos = match.end()
    return None


class EarlyUtf8Meta(HTMLParser):
    """Locate a real UTF-8 meta declaration, not one inside a comment/script."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "meta":
            return
        # Never accept an entity-encoded charset from the parsed attrs.
        raw_value = literal_meta_charset(self.get_starttag_text())
        if raw_value is not None and raw_value.lower() == "utf-8":
            self.found = True

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def has_early_utf8_meta(raw: bytes) -> bool:
    """The complete encoding declaration must fit in the first 1024 BYTES."""
    parser = EarlyUtf8Meta()
    # Latin-1 preserves the location of each source byte; ignore-ASCII
    # decoding could turn a non-ASCII tag name into a fictitious <meta>.
    parser.feed(raw[:1024].decode("latin-1"))
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


def main() -> int:
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
        return 1

    print(f"PUBLIC TEXT ENCODING: PASS ({checked} public artifacts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
