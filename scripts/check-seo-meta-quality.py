#!/usr/bin/env python3
"""Check sitewide SEO meta quality, duplicate prevention, canonical parity, and OG consistency.

Enforces:
1. Unique <title> and meta description across all published indexable pages.
2. Exact matching between canonical URL and actual published route.
3. Strict parity between canonical href and property="og:url".
4. Absence of duplicate canonical, description, or robots meta tags within <head>.
5. Length limits (titles: 20-75 chars, descriptions: 40-175 chars) on all indexable pages.

Usage:
    python scripts/check-seo-meta-quality.py
"""
from __future__ import annotations

import io
import re
import sys
from collections import defaultdict
from pathlib import Path
from html.parser import HTMLParser

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {
    ".git", ".github", "node_modules", "tests", "scripts", "artifacts",
    ".preview-dist-sitewide-qa", ".preview-dist", ".claude", "tmp", "data",
}

class HeadMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_head = False
        self.in_title = False
        self.title_parts: list[str] = []
        self.title: str = ""
        self.title_count = 0
        self.descriptions: list[str] = []
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.og_url: str | None = None
        self.og_title: str | None = None
        self.og_description: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower == "head":
            self.in_head = True
            return
        if not self.in_head:
            return

        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        if tag_lower == "title":
            self.in_title = True
            self.title_count += 1
        elif tag_lower == "link" and attr_dict.get("rel", "").lower() == "canonical":
            self.canonicals.append(attr_dict.get("href", "").strip())
        elif tag_lower == "meta":
            name = attr_dict.get("name", "").lower()
            prop = attr_dict.get("property", "").lower()
            content = attr_dict.get("content", "").strip()

            if name == "description":
                self.descriptions.append(content)
            elif name == "robots":
                self.robots.append(content)
            elif prop == "og:url":
                self.og_url = content
            elif prop == "og:title":
                self.og_title = content
            elif prop == "og:description":
                self.og_description = content

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower == "head":
            self.in_head = False
        elif tag_lower == "title":
            self.in_title = False
            self.title = "".join(self.title_parts).strip()

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)


def parse_page_head(path: Path) -> HeadMetaParser:
    parser = HeadMetaParser()
    content = path.read_text(encoding="utf-8", errors="ignore")
    head_end = content.find("</head>")
    if head_end != -1:
        parser.feed(content[: head_end + 7])
    else:
        parser.feed(content)
    return parser


def check_seo_meta_quality(base_dir: Path | None = None) -> list[str]:
    root_path = base_dir or ROOT
    failures: list[str] = []
    titles: dict[str, list[str]] = defaultdict(list)
    descriptions: dict[str, list[str]] = defaultdict(list)
    canonicals: dict[str, list[str]] = defaultdict(list)

    html_files = list(root_path.rglob("*.html"))
    for path in sorted(html_files):
        try:
            rel_parts = path.relative_to(root_path).parts
        except ValueError:
            rel_parts = path.parts
        if any(part in SKIP_PARTS for part in rel_parts):
            continue

        try:
            rel_path = path.relative_to(root_path).as_posix()
        except ValueError:
            rel_path = path.as_posix()

        parser = parse_page_head(path)
        is_noindex = any("noindex" in r.lower() for r in parser.robots)

        # 1. Multiplicity errors in <head>
        if parser.title_count > 1:
            failures.append(f"{rel_path}: multiple <title> tags ({parser.title_count}) in <head>")
        if len(parser.canonicals) > 1:
            failures.append(f"{rel_path}: multiple <link rel='canonical'> tags ({len(parser.canonicals)}) in <head>")
        if len(parser.descriptions) > 1:
            failures.append(f"{rel_path}: multiple <meta name='description'> tags ({len(parser.descriptions)}) in <head>")
        if len(parser.robots) > 1:
            failures.append(f"{rel_path}: multiple <meta name='robots'> tags ({len(parser.robots)}) in <head>")

        if not is_noindex:
            # 2. Required title and bounds
            if not parser.title:
                failures.append(f"{rel_path}: missing or empty <title>")
            else:
                titles[parser.title].append(rel_path)
                if len(parser.title) < 20:
                    failures.append(f"{rel_path}: title too short ({len(parser.title)} chars): '{parser.title}'")
                elif len(parser.title) > 75:
                    failures.append(f"{rel_path}: title too long ({len(parser.title)} chars): '{parser.title}'")

            # 3. Required description and bounds
            if not parser.descriptions or not parser.descriptions[0]:
                failures.append(f"{rel_path}: missing or empty <meta name='description'>")
            else:
                desc = parser.descriptions[0]
                descriptions[desc].append(rel_path)
                if len(desc) < 40:
                    failures.append(f"{rel_path}: description too short ({len(desc)} chars): '{desc}'")
                elif len(desc) > 175:
                    failures.append(f"{rel_path}: description too long ({len(desc)} chars): '{desc}'")

            # 4. Canonical validity and route parity
            if not parser.canonicals or not parser.canonicals[0]:
                failures.append(f"{rel_path}: missing <link rel='canonical'>")
            else:
                canon = parser.canonicals[0]
                canonicals[canon].append(rel_path)
                expected_route = "/" if rel_path == "index.html" else ("/" + rel_path[:-10] if rel_path.endswith("/index.html") else "/" + rel_path)
                expected_canon = f"https://davidportodiaz.com{expected_route}"
                if canon != expected_canon:
                    failures.append(f"{rel_path}: canonical mismatch: expected '{expected_canon}', got '{canon}'")

            # 5. OpenGraph url parity with canonical
            if parser.og_url and parser.canonicals:
                if parser.og_url != parser.canonicals[0]:
                    failures.append(f"{rel_path}: og:url ('{parser.og_url}') does not match canonical ('{parser.canonicals[0]}')")

    # 6. Uniqueness across indexable pages
    for title, files in titles.items():
        if len(files) > 1:
            failures.append(f"Duplicate <title> across indexable pages: '{title}' in {files}")

    for desc, files in descriptions.items():
        if len(files) > 1:
            failures.append(f"Duplicate <meta name='description'> across indexable pages: '{desc[:60]}...' in {files}")

    for canon, files in canonicals.items():
        if len(files) > 1:
            failures.append(f"Duplicate canonical URL across distinct files: '{canon}' in {files}")

    return failures


if __name__ == "__main__":
    issues = check_seo_meta_quality()
    if issues:
        print(f"FAIL — {len(issues)} SEO meta quality issue(s):")
        for err in issues:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("OK — Sitewide SEO meta quality, uniqueness, canonical and OG parity verified.")
