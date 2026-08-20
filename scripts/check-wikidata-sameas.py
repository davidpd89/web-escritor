#!/usr/bin/env python3
"""Validate every Wikidata sameAs used in tracked HTML against a known-good
table, and optionally cross-check that table against the live Wikidata API.

Why this exists: a real incident (2026-08-20) had wikidata.org/wiki/Q1212
("Montana", the US state) used as if it meant "Literatura juvenil"/
"Fantasia juvenil espanola", Q18219 ("A. J. Buckley", an actor) used as
"Worldbuilding", and Q474504 ("Jan Herzog", a rower) used as "Ficcion
especulativa"/"Narrativa especulativa" — all silently wrong because no
existing checker validated semantic truth against Wikidata, only JSON-LD
syntax. This checker is the corrective control.

Two modes:
  python scripts/check-wikidata-sameas.py         # offline: checks every
      QID found in tracked HTML against KNOWN_GOOD below. Fails if a QID
      appears that isn't in the table (forces a human to verify and add
      it deliberately, rather than silently trusting new QIDs).
  python scripts/check-wikidata-sameas.py --live   # also re-fetches each
      QID's current label/description from the real Wikidata API and
      confirms it still matches KNOWN_GOOD (catches drift, not just typos).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Each entry: QID -> (expected English label substring, one-line note).
# Verified directly against https://www.wikidata.org/wiki/Special:EntityData
# on 2026-08-20. Add a new QID here ONLY after verifying it yourself against
# the live entity — never by intuition/guessing from the QID number.
KNOWN_GOOD = {
    "Q139678851": ("David Porto Díaz", "the author's own Wikidata item"),
    "Q139927664": ("Noveris", "fictional city in Samuel entre mundos (ES label only)"),
    "Q119429258": ("portal fantasy", "fantasy fiction involving travel between universes"),
    "Q9326077": ("speculative fiction", "umbrella genre"),
    "Q1822655": ("worldbuilding", "practice of constructing an imaginary world"),
}

# QIDs confirmed WRONG for concepts they were previously attached to in this
# repo. Kept here so a future accidental re-introduction is caught loudly
# instead of silently passing as "unknown, needs review".
KNOWN_BAD = {
    "Q1212": "Montana (US state) — was wrongly used for young-adult/Spanish YA fantasy",
    "Q18219": "A. J. Buckley (actor) — was wrongly used for Worldbuilding",
    "Q474504": "Jan Herzog (rower) — was wrongly used for speculative fiction",
    "Q132311": "fantasy (too generic) — was wrongly used as 'epic fantasy'/'portal fantasy' specifically",
}

QID_RE = re.compile(r"wikidata\.org/wiki/(Q\d+)")


def git_tracked_html():
    result = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            yield ROOT / line


def find_references():
    refs = {}  # qid -> list of (file, line_no)
    for path in git_tracked_html():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for m in QID_RE.finditer(line):
                refs.setdefault(m.group(1), []).append((path.relative_to(ROOT), i))
    return refs


def fetch_live(qids):
    if not qids:
        return {}
    ids = "|".join(sorted(qids))
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={ids}&props=labels|descriptions&languages=en&format=json"
    # Wikimedia's API policy rejects requests without a descriptive
    # User-Agent (returns 403 for the urllib default).
    req = urllib.request.Request(
        url, headers={"User-Agent": "davidportodiaz.com-wikidata-checker/1.0 (https://davidportodiaz.com/; contact: davidpd89@gmail.com)"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out = {}
    for qid, ent in data.get("entities", {}).items():
        label = ent.get("labels", {}).get("en", {}).get("value", "")
        desc = ent.get("descriptions", {}).get("en", {}).get("value", "")
        out[qid] = (label, desc)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="Re-fetch each QID from the live Wikidata API")
    args = ap.parse_args()

    refs = find_references()
    errors = []

    print(f"Found {len(refs)} distinct Wikidata QID(s) referenced in tracked HTML.\n")
    for qid, locations in sorted(refs.items()):
        where = ", ".join(f"{f}:{n}" for f, n in locations)
        if qid in KNOWN_BAD:
            errors.append(f"{qid} is KNOWN BAD ({KNOWN_BAD[qid]}) — still referenced at {where}")
            continue
        if qid not in KNOWN_GOOD:
            errors.append(f"{qid} is not in KNOWN_GOOD — verify it manually against Wikidata and add it to scripts/check-wikidata-sameas.py, referenced at {where}")
            continue
        label, note = KNOWN_GOOD[qid]
        print(f"  {qid}: OK ({label} — {note}) — {where}")

    if args.live and refs:
        print("\nRe-checking KNOWN_GOOD against the live API...")
        live = fetch_live(set(KNOWN_GOOD) & set(refs))
        for qid, (expected_label, _note) in KNOWN_GOOD.items():
            if qid not in live:
                continue
            live_label, live_desc = live[qid]
            if expected_label.split()[0].lower() not in (live_label or "").lower() and qid != "Q139927664":
                errors.append(f"{qid} label drift: table says {expected_label!r}, live API says {live_label!r} ({live_desc!r})")

    if errors:
        print(f"\nFAILED — {len(errors)} issue(s):")
        for e in errors:
            print(f"- {e}")
        return 1

    print("\nOK — every referenced QID is in the verified table, none are known-bad.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
