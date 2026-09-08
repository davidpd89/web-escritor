#!/usr/bin/env python3
"""Audit public artifacts for static exposure of the author's contact email.

The current site historically encoded the address with numeric HTML entities.
That is visually fine but weak against scrapers because standard HTML parsers
resolve those entities automatically. This audit therefore checks BOTH raw text
and HTML-unescaped text.

By default the script is report-only so it can be introduced before the markup
migration. Use --strict once the migration is complete and wire that mode into
CI so future pages cannot regress to a static address/mailto.
"""
from __future__ import annotations

import argparse
import html
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Same address as the reveal runtime, represented without a plaintext email
# literal in this source file. This is obfuscation, not a secret.
AUTHOR_EMAIL_CODES = (
    100, 97, 118, 105, 100, 112, 111, 114, 116, 111, 100, 105, 97, 122,
    64, 103, 109, 97, 105, 108, 46, 99, 111, 109,
)
AUTHOR_EMAIL = "".join(chr(code) for code in AUTHOR_EMAIL_CODES)
MAILTO = f"mailto:{AUTHOR_EMAIL}"

PUBLIC_SUFFIXES = {".html", ".htm", ".xml", ".json", ".txt", ".webmanifest", ".js", ".mjs"}
SKIP_DIRS = {
    ".git",
    ".github",
    "docs",
    "tests",
    "qa",
    "scripts",
    "node_modules",
    "lab",
}

# Files whose entire purpose is a human or machine reading the contact address
# programmatically or on paper -- obfuscating them would defeat the file, not
# protect anyone. This is a short, explicit allowlist, not a directory skip,
# so a new page can never accidentally inherit the exemption.
PUBLIC_DISCLOSURE_EXEMPT = {
    "humans.txt",
    "llms.txt",
    "llms-full.txt",
    "editorial-facts.json",  # build-time source only; not deployed (404 on the live site)
    "assets/samuel-entre-mundos-ficha-tecnica.txt",  # downloadable press fact sheet
    "press-kit/david-porto-diaz.json",
    "press-kit/las-manecillas-del-recuerdo.json",
    "press-kit/samuel-entre-mundos.json",
    # Meant to be printed and read offline by book clubs; a click-to-reveal
    # trigger is meaningless on paper.
    "clubes-de-lectura/samuel-entre-mundos/guia-imprimible/index.html",
}


@dataclass(frozen=True)
class Finding:
    path: str
    kind: str


def inspect_text(text: str) -> set[str]:
    """Return exposure kinds present in one public artifact."""
    decoded = html.unescape(text)
    kinds: set[str] = set()

    if AUTHOR_EMAIL in text:
        kinds.add("plaintext_email")
    if MAILTO in text:
        kinds.add("plaintext_mailto")

    # This catches numeric/named HTML-entity obfuscation such as the site's
    # previous &#100;&#97;... pattern, which normal parsers decode for bots too.
    if AUTHOR_EMAIL in decoded and AUTHOR_EMAIL not in text:
        kinds.add("html_entity_email")
    if MAILTO in decoded and MAILTO not in text:
        kinds.add("html_entity_mailto")

    return kinds


def iter_public_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in PUBLIC_SUFFIXES:
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if rel.as_posix() in PUBLIC_DISCLOSURE_EXEMPT:
            continue
        yield path


def scan_tree(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_public_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for kind in sorted(inspect_text(text)):
            findings.append(Finding(str(path.relative_to(root)), kind))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when a public artifact exposes the protected email",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    findings = scan_tree(args.root.resolve())

    if args.json:
        print(json.dumps([finding.__dict__ for finding in findings], indent=2))
    elif findings:
        print("Public email exposure findings:")
        for finding in findings:
            print(f"- {finding.path}: {finding.kind}")
    else:
        print("Public email exposure audit: 0 findings")

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
