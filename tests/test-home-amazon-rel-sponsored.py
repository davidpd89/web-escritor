#!/usr/bin/env python3
"""K.3 regression: dynamic Home Amazon links must carry rel=sponsored/nofollow.

assets/v1-home-editorial-v3.js injects "Comprar en Amazon" cards (Samuel's
direct amazon.es?tag= link, Manecillas' amzn.to Kindle affiliate short link)
through a shared addTextLink() helper that sets rel for any absolute
https:// href. It previously only set noopener/noreferrer, missing
sponsored/nofollow on the affiliate link -- a real gap flagged by #237/K.3.

2026-09-05: the affiliate check moved out of addTextLink() into its own
isAmazonAffiliateUrl() helper (also fixed to recognize amzn.to as affiliate
outright, since that host never carries a visible tag= itself -- a second
real gap that silently stripped rel=sponsored/aria-label from Manecillas'
Home CTAs the day its purchaseUrl became a real amzn.to link). This test
follows that refactor: it checks addTextLink() delegates to the helper, and
that the helper itself still requires tag= for amazon.es while trusting
amzn.to unconditionally.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets/v1-home-editorial-v3.js"

js = SRC.read_text(encoding="utf-8")

assert "SAMUEL_AMAZON_URL" in js, "Home Amazon affiliate URL constant disappeared"
assert "tag=davidporto-21" in js, "Home Amazon affiliate tag disappeared"
assert "AMAZON_SHORTLINK_HOSTS" in js and "amzn.to" in js, (
    "Home must still recognize amzn.to (Manecillas' Kindle affiliate short link) as affiliate"
)

link_match = re.search(r"function addTextLink\([^)]*\)\s*\{(.*?)\n  \}", js, flags=re.S)
assert link_match, "addTextLink() not found in assets/v1-home-editorial-v3.js"
link_body = link_match.group(1)

assert "sponsored" in link_body and "nofollow" in link_body, (
    "addTextLink() no longer sets rel=sponsored/nofollow for affiliate links"
)
assert "isAmazonAffiliateUrl" in link_body, (
    "addTextLink() must delegate its affiliate decision to isAmazonAffiliateUrl(), not re-derive its own check"
)

affiliate_match = re.search(r"function isAmazonAffiliateUrl\([^)]*\)\s*\{(.*?)\n    \}", js, flags=re.S)
assert affiliate_match, "isAmazonAffiliateUrl() not found in assets/v1-home-editorial-v3.js"
affiliate_body = affiliate_match.group(1)

assert "tag=" in affiliate_body, "isAmazonAffiliateUrl() no longer keys amazon.es off the affiliate tag= param"
assert "amazon" in affiliate_body.lower(), (
    "isAmazonAffiliateUrl() must be scoped to Amazon hosts, not any domain with ?tag="
)
assert "AMAZON_SHORTLINK_HOSTS" in affiliate_body, (
    "isAmazonAffiliateUrl() must treat the amzn.to short-link allowlist as affiliate outright"
)

print("home-amazon-rel-sponsored: OK")
