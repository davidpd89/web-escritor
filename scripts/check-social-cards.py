#!/usr/bin/env python3
"""Audit Open Graph and X/Twitter card metadata for static HTML.

Site-specific goals:
- report every indexable HTML page that cannot produce a predictable rich share card;
- verify local card assets exist and declared dimensions match the file;
- keep first adoption as a report; use --strict after legacy debt is fixed.

Python standard library only.
"""
from __future__ import annotations

import argparse
import struct
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

SITE_ORIGIN = "https://davidportodiaz.com"
DEFAULT_ARTICLE_CARD = "/assets/david-porto-imagen-compartir.webp"


class MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.canonical: str | None = None
        self.has_head: bool = False
        self._in_head = False
        self._done = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._done:
            return
        tag = tag.lower()
        data = {k.lower(): (v or "") for k, v in attrs}
        if tag == "head":
            self._in_head = True
            self.has_head = True
            return
        if tag == "body":
            self._done = True
            return
        if not self._in_head:
            return
        if tag == "meta":
            key = (data.get("property") or data.get("name") or "").strip().lower()
            if key and key not in self.meta:
                self.meta[key] = data.get("content", "").strip()
        elif tag == "link" and data.get("rel", "").strip().lower() == "canonical":
            self.canonical = data.get("href", "").strip() or None


@dataclass
class Finding:
    severity: str
    path: str
    code: str
    message: str


@dataclass
class PageAudit:
    path: str
    og_type: str = ""
    og_image: str = ""
    findings: list[Finding] = field(default_factory=list)


REQUIRED_OG = (
    "og:title",
    "og:description",
    "og:type",
    "og:url",
    "og:image",
    "og:image:width",
    "og:image:height",
    "og:image:alt",
)
REQUIRED_TWITTER = (
    "twitter:card",
    "twitter:title",
    "twitter:description",
    "twitter:image",
    "twitter:image:alt",
)


def parse_html(path: Path) -> MetaParser | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    parser = MetaParser()
    parser.feed(text[:250_000])
    return parser


def is_noindex(parser: MetaParser) -> bool:
    return "noindex" in parser.meta.get("robots", "").lower()


def local_asset_path(url: str, root: Path, origin: str) -> Path | None:
    parsed = urlparse(url)
    expected = urlparse(origin)
    if parsed.scheme != "https" or parsed.netloc != expected.netloc:
        return None
    if parsed.query or parsed.fragment:
        return None
    rel = unquote(parsed.path).lstrip("/")
    return root / rel


def image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 10:
        return None

    # PNG
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])

    # GIF
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])

    # JPEG
    if data.startswith(b"\xff\xd8"):
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            i += 2
            if marker in (0xD8, 0xD9):
                continue
            if i + 2 > len(data):
                break
            length = int.from_bytes(data[i:i+2], "big")
            if length < 2 or i + length > len(data):
                break
            if marker in {0xC0,0xC1,0xC2,0xC3,0xC5,0xC6,0xC7,0xC9,0xCA,0xCB,0xCD,0xCE,0xCF}:
                height = int.from_bytes(data[i+3:i+5], "big")
                width = int.from_bytes(data[i+5:i+7], "big")
                return width, height
            i += length

    # WebP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) >= 30:
        chunk = data[12:16]
        if chunk == b"VP8X" and len(data) >= 30:
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
            return width, height
        if chunk == b"VP8 " and len(data) >= 30:
            # Lossy frame header contains 9d 01 2a followed by 14-bit width/height.
            pos = data.find(b"\x9d\x01\x2a", 20, min(len(data), 80))
            if pos != -1 and pos + 7 <= len(data):
                width = int.from_bytes(data[pos+3:pos+5], "little") & 0x3FFF
                height = int.from_bytes(data[pos+5:pos+7], "little") & 0x3FFF
                return width, height
        if chunk == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
            b1, b2, b3, b4 = data[21:25]
            width = 1 + (((b2 & 0x3F) << 8) | b1)
            height = 1 + (((b4 & 0x0F) << 10) | (b3 << 2) | ((b2 & 0xC0) >> 6))
            return width, height

    return None


def add(audit: PageAudit, severity: str, code: str, msg: str) -> None:
    audit.findings.append(Finding(severity, audit.path, code, msg))


def audit_page(path: Path, root: Path, origin: str) -> PageAudit | None:
    parser = parse_html(path)
    if parser is None or is_noindex(parser):
        return None
    # Build artifacts / includes (e.g. data/*.generated.html) are HTML
    # fragments meant to be embedded into a real page's <body>, not
    # standalone documents - they have no <head> of their own to carry
    # social-card metadata, so auditing them as pages is a false positive.
    if not parser.has_head:
        return None

    rel = path.relative_to(root).as_posix()
    audit = PageAudit(rel)
    m = parser.meta
    audit.og_type = m.get("og:type", "").lower()
    audit.og_image = m.get("og:image", "")

    for key in REQUIRED_OG:
        if not m.get(key):
            add(audit, "ERROR", "missing-meta", f"missing {key}")
    for key in REQUIRED_TWITTER:
        if not m.get(key):
            sev = "WARNING" if key == "twitter:image:alt" else "ERROR"
            add(audit, sev, "missing-meta", f"missing {key}")

    canonical = parser.canonical or ""
    if canonical and m.get("og:url") and canonical != m["og:url"]:
        add(audit, "ERROR", "url-drift", f"canonical != og:url ({canonical} vs {m['og:url']})")

    for key in ("og:image", "twitter:image"):
        url = m.get(key, "")
        if not url:
            continue
        parsed = urlparse(url)
        if parsed.scheme != "https":
            add(audit, "ERROR", "image-url", f"{key} must be https: {url}")
            continue
        local = local_asset_path(url, root, origin)
        if parsed.netloc == urlparse(origin).netloc:
            if local is None:
                add(audit, "ERROR", "image-url", f"{key} has query/fragment or invalid local URL: {url}")
                continue
            if not local.is_file():
                add(audit, "ERROR", "missing-asset", f"{key} asset does not exist: {local.relative_to(root)}")
                continue
            if local.stat().st_size > 1_000_000:
                add(audit, "WARNING", "large-card", f"{key} asset exceeds 1 MB: {local.stat().st_size} bytes")

    og_local = local_asset_path(m.get("og:image", ""), root, origin) if m.get("og:image") else None
    if og_local and og_local.is_file():
        actual = image_dimensions(og_local)
        if actual:
            try:
                declared = (int(m.get("og:image:width", "0")), int(m.get("og:image:height", "0")))
            except ValueError:
                declared = (0, 0)
            if declared != actual:
                add(audit, "ERROR", "dimension-drift", f"declared og:image {declared[0]}x{declared[1]} but file is {actual[0]}x{actual[1]}")
        else:
            add(audit, "WARNING", "dimension-unreadable", f"could not read dimensions for {og_local.relative_to(root)}")

    if audit.og_type == "article" and urlparse(audit.og_image).path == DEFAULT_ARTICLE_CARD:
        add(audit, "NOTICE", "generic-card", "article still uses the generic site share image")

    return audit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--origin", default=SITE_ORIGIN)
    ap.add_argument("--strict", action="store_true", help="fail if ERROR findings exist")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    audits: list[PageAudit] = []
    skip_parts = {
        ".git", "node_modules", "vendor", ".github", "tests", "scripts",
        "WEB DAVID PORTO nuevas ideas", "archive", ".codex_work",
        ".preview-dist", "dist",
    }
    for path in sorted(root.rglob("*.html")):
        # Never treat vendored/generated fixtures or draft/example pages from
        # the planning folder as live site pages.
        if any(part in skip_parts for part in path.parts):
            continue
        audit = audit_page(path, root, args.origin)
        if audit:
            audits.append(audit)

    findings = [f for a in audits for f in a.findings]
    counts = defaultdict(int)
    for f in findings:
        counts[f.severity] += 1
        print(f"{f.severity:7} {f.path}: {f.code}: {f.message}")

    # Reuse inventory for editorial planning; not a hard error.
    image_to_articles: dict[str, list[str]] = defaultdict(list)
    for a in audits:
        if a.og_type == "article" and a.og_image:
            image_to_articles[a.og_image].append(a.path)
    for image, pages in sorted(image_to_articles.items()):
        if len(pages) >= 3:
            print(f"NOTICE  shared article card used by {len(pages)} pages: {image}")

    print(
        f"Social cards: {len(audits)} indexable HTML pages; "
        f"{counts['ERROR']} error(s), {counts['WARNING']} warning(s), {counts['NOTICE']} notice(s)."
    )
    return 1 if args.strict and counts["ERROR"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
