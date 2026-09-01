#!/usr/bin/env python3
"""K.3 regression: dynamic Home Amazon links must carry rel=sponsored/nofollow.

assets/v1-home-editorial-v3.js injects two "Comprar en Amazon" cards (Samuel,
Manecillas placeholder) through a shared addTextLink() helper that sets rel
for any absolute https:// href. It previously only set noopener/noreferrer,
missing sponsored/nofollow on the affiliate (tag=...) link -- a real gap
flagged by #237/K.3 and confirmed still present against current main.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets/v1-home-editorial-v3.js"

js = SRC.read_text(encoding="utf-8")

assert "SAMUEL_AMAZON_URL" in js, "Home Amazon affiliate URL constant disappeared"
assert "tag=davidporto-21" in js, "Home Amazon affiliate tag disappeared"

match = re.search(r"function addTextLink\([^)]*\)\s*\{(.*?)\n  \}", js, flags=re.S)
assert match, "addTextLink() not found in assets/v1-home-editorial-v3.js"
body = match.group(1)

assert "sponsored" in body and "nofollow" in body, (
    "addTextLink() no longer sets rel=sponsored/nofollow for affiliate (tag=...) links"
)
assert "tag=" in body, "addTextLink() rel branch is no longer keyed off the affiliate tag= param"

print("home-amazon-rel-sponsored: OK")
