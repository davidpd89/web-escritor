#!/usr/bin/env python3
"""Las manecillas: every Yellowtail stack must use the metric-adjusted fallback.

Yellowtail is font-display:swap and arrives after first paint. With the shared
Manrope-based UI fallback the script strings (hero eyebrow, action row) are much
wider while loading, so the hero reflowed when the font arrived: CLS 0.134 at
768px and 0.151 at 1280px in production (2026-10-23). The Samuel fallback face
(size-adjust, defined in v1-shell.css) keeps the same footprint; measured CLS
with it is ~0.0005 with fonts delayed 350ms.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / "assets" / "v1-manecillas-design-v8.css").read_text(encoding="utf-8")
shell = (ROOT / "assets" / "v1-shell.css").read_text(encoding="utf-8")

assert "font-family:'Samuel Yellowtail Fallback'" in shell, "fallback face must exist in v1-shell.css"
stacks = re.findall(r"font-family:\s*'Yellowtail'[^;}]*", css)
assert stacks, "expected Yellowtail stacks in the Manecillas stylesheet"
for stack in stacks:
    assert "'Samuel Yellowtail Fallback'" in stack, stack
print(f"PASS manecillas yellowtail fallback ({len(stacks)} stacks)")
