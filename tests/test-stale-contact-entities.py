#!/usr/bin/env python3
"""Mutation fixtures for the obsolete public contact-address scanner.

Prepared for later CI; this draft PR intentionally uses [skip ci].
"""
from __future__ import annotations

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checker = runpy.run_path(str(ROOT / "scripts" / "check-no-stale-contact-email.py"))
detect = checker["has_obsolete_contact"]

BAD = {
    "literal address": "samuelentremundos@gmail.com",
    "uppercase": "SAMUELENTREMUNDOS@GMAIL.COM",
    "numeric decimal first letter": "&#115;amuelentremundos@gmail.com",
    "numeric hex first letter": "&#x73;amuelentremundos@gmail.com",
    "interior encoded letter": "samu&#101;lentremundos@gmail.com",
    "fully encoded data-n": 'data-n="&#115;&#97;&#109;&#117;&#101;&#108;&#101;&#110;&#116;&#114;&#101;&#109;&#117;&#110;&#100;&#111;&#115;"',
    "mixed attr and at-sign": 'href="mailto:samuelentremundos&#64;gmail.com"',
}
GOOD = {
    "current contact": "davidportodiaz@gmail.com",
    "book title without address stem": "Samuel entre mundos",
    "different local part": "samuelentremundo@gmail.com",
    "unresolved double-escaped numeric ref": "&amp;#115;amuelentremundos",
    "unrelated numeric text": "&#115;ample@example.com",
}

failures: list[str] = []
for label, html in BAD.items():
    if not detect(html):
        failures.append(f"{label}: obsolete contact not detected")
for label, html in GOOD.items():
    if detect(html):
        failures.append(f"{label}: false positive")

if failures:
    print("FAIL stale-contact HTML-entity mutations")
    for failure in failures:
        print(" -", failure)
    raise SystemExit(1)
print(f"PASS stale-contact HTML-entity mutations: {len(BAD)} negative + {len(GOOD)} positive")
