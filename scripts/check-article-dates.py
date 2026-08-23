#!/usr/bin/env python3
"""Validate visible article dates against JSON-LD dates in Cuaderno articles."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLE_GLOB = "cuaderno/**/index.html"

JSONLD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
ARTICLE_HEADER_RE = re.compile(r"<header\s+class=\"article-header\"", re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PUBLISHED_VISIBLE_RE = re.compile(
    r"Publicado el\s*<time[^>]*datetime=[\"'](?P<date>\d{4}-\d{2}-\d{2})[\"']",
    re.I,
)
UPDATED_VISIBLE_RE = re.compile(
    r"Actualizado el\s*<time[^>]*datetime=[\"'](?P<date>\d{4}-\d{2}-\d{2})[\"']",
    re.I,
)


def iter_nodes(node):
    if isinstance(node, dict):
        yield node
        if isinstance(node.get("@graph"), list):
            for child in node["@graph"]:
                yield from iter_nodes(child)
        for value in node.values():
            yield from iter_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_nodes(item)


def extract_article_dates(html: str) -> tuple[str | None, str | None]:
    published = None
    modified = None
    for match in JSONLD_RE.finditer(html):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for node in iter_nodes(data):
            if not isinstance(node, dict):
                continue
            type_value = node.get("@type")
            types = type_value if isinstance(type_value, list) else [type_value]
            if not any(t in {"Article", "BlogPosting"} for t in types if isinstance(t, str)):
                continue
            p = node.get("datePublished")
            m = node.get("dateModified")
            if isinstance(p, str) and DATE_RE.match(p[:10]):
                published = p[:10]
            if isinstance(m, str) and DATE_RE.match(m[:10]):
                modified = m[:10]
            if published and modified:
                return published, modified
    return published, modified


def check_file(path: Path) -> tuple[list[str], bool]:
    errors: list[str] = []
    rel = path.relative_to(ROOT).as_posix()
    html = path.read_text(encoding="utf-8", errors="replace")

    if not ARTICLE_HEADER_RE.search(html):
        return errors, False

    published, modified = extract_article_dates(html)
    if not published or not modified:
        errors.append(f"{rel}: missing datePublished/dateModified in JSON-LD Article")
        return errors, True

    visible_published = PUBLISHED_VISIBLE_RE.search(html)
    if not visible_published:
        errors.append(f"{rel}: missing visible published date block")
    elif visible_published.group("date") != published:
        errors.append(f"{rel}: missing visible published date matching JSON-LD ({published})")

    visible_updated = UPDATED_VISIBLE_RE.search(html)
    has_updated = visible_updated is not None
    if modified == published:
        if has_updated:
            errors.append(f"{rel}: has visible updated date even though dateModified == datePublished ({modified})")
    else:
        if not visible_updated:
            errors.append(f"{rel}: missing visible updated date block ({modified})")
        elif visible_updated.group("date") != modified:
            errors.append(f"{rel}: missing visible updated date matching JSON-LD ({modified})")

    return errors, True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check visible article dates in Cuaderno articles")
    parser.add_argument("--check", action="store_true", help="Run in check mode (default behavior)")
    _ = parser.parse_args()

    files = sorted(ROOT.glob(ARTICLE_GLOB))
    errors: list[str] = []
    checked = 0
    for file_path in files:
        file_errors, is_article = check_file(file_path)
        if is_article:
            checked += 1
        errors.extend(file_errors)

    if errors:
        print("FAIL: article date visibility mismatch", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 1

    print(f"PASS: article date visibility ({checked} articles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
