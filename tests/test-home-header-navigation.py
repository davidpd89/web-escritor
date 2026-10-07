#!/usr/bin/env python3
"""Regression: Home keeps every global navigation entry visible."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "index.html").read_text(encoding="utf-8")
home_css = (ROOT / "assets" / "v1-home.css").read_text(encoding="utf-8")

for selector in ('class="header-search"', 'class="header-home"', 'class="header-sitemap"', 'class="explore-trigger"'):
    assert selector in html, f"Home header is missing {selector}"

assert 'data-assistant-search-open' in html
assert 'href="/"' in html
assert 'href="/mapa-del-sitio/"' in html
assert 'data-explore-open' in html
visibility_contract = ('html.v1[data-lrb-home="true"]:not(.lrb-compact) ' '.site-header__left .explore-trigger')
assert visibility_contract in home_css
rule = home_css.split(visibility_contract, 1)[1].split("}", 1)[0]
assert "display:inline-flex" in rule.replace(" ", ""), "Explore must remain visible on desktop Home before scroll"
print("home-header-navigation: OK (assistant, home, sitemap and explore present)")
