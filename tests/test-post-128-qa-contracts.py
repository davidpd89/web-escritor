#!/usr/bin/env python3
"""Regression contracts discovered in the post-#128 audit."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# #128 correctly updated the Home test for the <=899px breakpoint and the
# JS-only beta territory, but weakened the touch-target regression bar from
# the project's implemented 42px to WCAG's 24px normative minimum. WCAG is the
# floor; 42px is the current design contract. A silent 42 -> 24 regression
# must fail QA even though it would still clear WCAG 2.5.8.
home_qa = (ROOT / "qa" / "home-map-interaction.mjs").read_text(encoding="utf-8")
assert re.search(r"box\.height\s*>=\s*42\s*&&\s*box\.width\s*>=\s*42", home_qa), (
    "home-map-interaction.mjs must protect the current >=42px Explore target; "
    "24px is the WCAG floor, not the project's regression baseline"
)

shell_css = (ROOT / "assets" / "v1-shell-lrb-v2.css").read_text(encoding="utf-8")
for selector_fragment in (".header-home", ".header-sitemap", ".header-contact", ".explore-trigger"):
    assert selector_fragment in shell_css
assert "width:42px;height:42px" in shell_css, (
    "mobile shell no longer declares the 42px control contract; if design changes intentionally, "
    "update CSS and this test together with reflow evidence"
)

# #127 established package.json/lockfile as the single Playwright authority.
# No workflow may reintroduce an ad-hoc Playwright version install.
workflow_dir = ROOT / ".github" / "workflows"
offenders = []
for path in workflow_dir.glob("*.yml"):
    text = path.read_text(encoding="utf-8")
    if re.search(r"npm\s+install[^\n]*playwright@", text):
        offenders.append(path.relative_to(ROOT).as_posix())
for path in workflow_dir.glob("*.yaml"):
    text = path.read_text(encoding="utf-8")
    if re.search(r"npm\s+install[^\n]*playwright@", text):
        offenders.append(path.relative_to(ROOT).as_posix())
assert not offenders, f"ad-hoc Playwright version reintroduced in workflows: {offenders}"

print("PASS post-#128 QA contracts")
