#!/usr/bin/env python3
"""Guards the .article-utilities share/print CLS fix (post-#129 audit).

Root cause: the share/print buttons used the `hidden` attribute (real
display:none, zero width) until assets/v1-editorial.js revealed them,
collapsing the row sideways on first paint and jumping wide on reveal. Fixed
by switching to data-js-pending (visibility:hidden -- real width, no CLS)
with a CSP-safe <noscript><link> fallback (external stylesheet, not an
inline <style>, which this site's CSP -- style-src 'self', no unsafe-inline
-- would otherwise block). This test finds every .article-utilities instance
in the repo and requires all of them on the fixed pattern, so a future page
copy-pasting the old markup can't reintroduce the CLS source silently.
"""
from __future__ import annotations

import re
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

tracked_html = subprocess.run(
    ["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True
).stdout.splitlines()

instances = [rel for rel in tracked_html if "article-utilities" in (ROOT / rel).read_text(encoding="utf-8")]
assert instances, "no .article-utilities instances found -- update this test if the component was renamed/removed"

OLD_PATTERN = re.compile(r"hidden\s+data-share-url|hidden\s+data-print")
NOSCRIPT_LINK = '<noscript><link rel="stylesheet" href="/assets/v1-no-js-pending.css"></noscript>'
INLINE_STYLE_IN_NOSCRIPT = re.compile(r"<noscript>\s*<style>")

for rel in instances:
    html = (ROOT / rel).read_text(encoding="utf-8")
    assert not OLD_PATTERN.search(html), (
        f"{rel}: .article-utilities button still uses the CLS-causing `hidden` attribute; "
        "use data-js-pending (assets/v1-editorial.css) instead"
    )
    assert not INLINE_STYLE_IN_NOSCRIPT.search(html), (
        f"{rel}: <noscript><style> is an inline style, blocked by this site's CSP "
        "(style-src 'self', no unsafe-inline) -- use the external "
        f"{NOSCRIPT_LINK!r} pattern instead"
    )
    if "data-js-pending" in html:
        assert NOSCRIPT_LINK in html, (
            f"{rel}: has data-js-pending buttons but is missing the no-JS fallback "
            f"({NOSCRIPT_LINK!r}) that fully hides them when JavaScript never runs"
        )

no_js_pending_css = ROOT / "assets" / "v1-no-js-pending.css"
assert no_js_pending_css.exists(), "assets/v1-no-js-pending.css (external, CSP-safe) is missing"
assert "display:none" in no_js_pending_css.read_text(encoding="utf-8")

editorial_css = (ROOT / "assets" / "v1-editorial.css").read_text(encoding="utf-8")
assert "[data-js-pending]{visibility:hidden}" in editorial_css.replace(" ", ""), (
    "assets/v1-editorial.css must keep data-js-pending buttons in-flow (visibility:hidden), "
    "not display:none, or the width-reservation fix regresses"
)

print(f"PASS article-utilities CLS contract ({len(instances)} instances checked)")
