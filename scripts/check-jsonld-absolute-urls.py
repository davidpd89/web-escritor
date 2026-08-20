#!/usr/bin/env python3
"""Check that JSON-LD identity/reference fields use absolute canonical
URLs, not site-relative paths.

Why: a real bug (2026-08-20) had 12 tracked pages using
"url": "/herramientas/manuscrito/" and "author": {"@id": "/#author"}
instead of absolute https://davidportodiaz.com/... URLs. Relative values
in these specific fields are ambiguous outside the page's own document
context (a JSON-LD consumer fetching the raw script content, or an
aggregator, has no base URL to resolve against) and break @id-based
entity linking across pages (two nodes are only "the same entity" in
JSON-LD if their @id strings are identical — "/#author" on one page and
"https://davidportodiaz.com/#author" on another are NOT the same node).

Checks these fields specifically, wherever they appear in a JSON-LD
<script type="application/ld+json"> block: url, @id, isPartOf, about
(and about.@id / isPartOf.@id when those are objects). Only flags values
that look like a site-relative path (start with "/" but not "//"); an
absolute https://... URL, a mailto:/tel: URI, or a bare fragment
elsewhere is not what this checks.

Usage:
  python scripts/check-jsonld-absolute-urls.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_ORIGIN = "https://davidportodiaz.com"

FIELDS_TO_CHECK = {"url", "@id", "isPartOf", "about", "mainEntity", "isBasedOn"}

SCRIPT_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)


def git_tracked_html():
    result = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            yield ROOT / line


def is_relative_path(value: str) -> bool:
    return isinstance(value, str) and value.startswith("/") and not value.startswith("//")


def walk(node, path: str, findings: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in FIELDS_TO_CHECK:
                if isinstance(value, str) and is_relative_path(value):
                    findings.append(f"{path}.{key} = {value!r} (relative, should be {SITE_ORIGIN}{value})")
                elif isinstance(value, dict) and "@id" in value and is_relative_path(value["@id"]):
                    findings.append(f"{path}.{key}.@id = {value['@id']!r} (relative, should be {SITE_ORIGIN}{value['@id']})")
            walk(value, f"{path}.{key}", findings)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, f"{path}[{i}]", findings)


def main() -> int:
    errors = []
    scanned = 0
    for path in git_tracked_html():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        blocks = SCRIPT_RE.findall(text)
        if not blocks:
            continue
        scanned += 1
        rel = path.relative_to(ROOT)
        for block in blocks:
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue  # validate_jsonld.py already checks syntax; not this checker's job
            findings: list[str] = []
            walk(data, "$", findings)
            for f in findings:
                errors.append(f"{rel}: {f}")

    if errors:
        print(f"FAIL — {len(errors)} relative JSON-LD reference(s) across {scanned} page(s) with JSON-LD:")
        for e in errors:
            print(f"- {e}")
        return 1

    print(f"OK — {scanned} page(s) with JSON-LD checked, all url/@id/isPartOf/about/mainEntity/isBasedOn references are absolute.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
