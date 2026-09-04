#!/usr/bin/env python3
"""editorial-facts.json's lastReviewed is bumped every time an editorial
fact changes (see scripts/build-public-editorial-facts.py). llms.txt and
llms-full.txt each carry their own hand-written "Ultima actualizacion"
stamp that has to be bumped in the same commit -- nothing enforced that
before this test, which is exactly how both files ended up several days
stale (2026-08-22 and 2026-08-27) after the 2026-09-04 Kindle facts had
already landed in their body text.

This doesn't check that the *content* is current (test-manecillas-
purchase-url-consistency.py and test-machine-authority.py already cross-
check specific facts) -- it only checks that whoever last edited
editorial-facts.json also touched these two stamps, so a stale stamp can't
silently coexist with fresh facts (or the reverse: fresh-looking stamps
hiding stale facts).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTS = json.loads((ROOT / "editorial-facts.json").read_text(encoding="utf-8"))
LAST_REVIEWED = FACTS["lastReviewed"]
assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", LAST_REVIEWED), f"editorial-facts.json lastReviewed is not a date: {LAST_REVIEWED!r}"

errors: list[str] = []

llms_txt = (ROOT / "llms.txt").read_text(encoding="utf-8")
m = re.search(r"Última actualización:\s*(\d{4}-\d{2}-\d{2})", llms_txt)
if not m:
    errors.append("llms.txt: no 'Última actualización: YYYY-MM-DD' stamp found")
elif m.group(1) != LAST_REVIEWED:
    errors.append(
        f"llms.txt: stamp is {m.group(1)!r} but editorial-facts.json.lastReviewed is {LAST_REVIEWED!r} "
        "-- bump the stamp whenever editorial facts change (or vice versa)"
    )

llms_full_txt = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
m = re.search(r"Última actualización:\s*(\d{4}-\d{2}-\d{2})", llms_full_txt)
if not m:
    errors.append("llms-full.txt: no 'Última actualización: YYYY-MM-DD' stamp found")
elif m.group(1) != LAST_REVIEWED:
    errors.append(
        f"llms-full.txt: stamp is {m.group(1)!r} but editorial-facts.json.lastReviewed is {LAST_REVIEWED!r} "
        "-- bump the stamp whenever editorial facts change (or vice versa)"
    )

if errors:
    print("FAIL - machine-readable-freshness-stamp:")
    for err in errors:
        print(f"- {err}")
    raise SystemExit(1)

print(f"test-machine-readable-freshness-stamp: OK (lastReviewed: {LAST_REVIEWED})")
