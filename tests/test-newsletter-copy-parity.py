#!/usr/bin/env python3
"""assets/newsletter-general.js and script.js each keep their own copy of
the newsletter pending-confirmation copy (PENDING_COPY / NEWSLETTER_PENDING_
COPY) -- script.js's submitNewsletter() re-implements form wiring/validation
around newsletter-general.js's shared postNewsletter() network call, but the
per-source copy strings themselves are hand-duplicated, not shared.

That's exactly how the two files ended up saying different things after an
editorial change: newsletter-general.js's `manecillas` entry was updated for
the Kindle launch while script.js's stayed on the pre-launch "te avisare
cuando este disponible" promise (caught 2026-09-05). Until the two
implementations are actually consolidated, this test is the guard that
makes that drift impossible to ship silently again.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extract_copy_dict(text: str, block_name: str, source_path: str) -> dict[str, str]:
    block_match = re.search(rf"{block_name}\s*=\s*\{{(.*?)\n\s*\}};", text, re.S)
    assert block_match, f"{source_path}: {block_name} block not found"
    # Trailing "\n" makes the last entry (no trailing comma before the
    # closing brace, which the block regex above consumes as its boundary)
    # match the same per-entry pattern as every other line.
    entries = dict(re.findall(r"(\w+):\s*['\"](.*?)['\"],?\s*\n", block_match.group(1) + "\n"))
    assert entries, f"{source_path}: {block_name} parsed to zero entries -- extractor regex is stale"
    return entries


general_js = (ROOT / "assets" / "newsletter-general.js").read_text(encoding="utf-8")
script_js = (ROOT / "script.js").read_text(encoding="utf-8")

general_copy = extract_copy_dict(general_js, "PENDING_COPY", "assets/newsletter-general.js")
script_copy = extract_copy_dict(script_js, "NEWSLETTER_PENDING_COPY", "script.js")

errors: list[str] = []

missing_in_script = sorted(set(general_copy) - set(script_copy))
missing_in_general = sorted(set(script_copy) - set(general_copy))
if missing_in_script:
    errors.append(f"script.js NEWSLETTER_PENDING_COPY is missing source(s) present in newsletter-general.js: {missing_in_script}")
if missing_in_general:
    errors.append(f"newsletter-general.js PENDING_COPY is missing source(s) present in script.js: {missing_in_general}")

for key in sorted(set(general_copy) & set(script_copy)):
    if general_copy[key] != script_copy[key]:
        errors.append(
            f"newsletter copy for source={key!r} diverged between the two implementations:\n"
            f"  assets/newsletter-general.js: {general_copy[key]!r}\n"
            f"  script.js:                    {script_copy[key]!r}"
        )

if errors:
    print("FAIL - newsletter-copy-parity:")
    for err in errors:
        print(f"- {err}")
    raise SystemExit(1)

print(f"test-newsletter-copy-parity: OK ({len(general_copy)} source(s) checked)")
