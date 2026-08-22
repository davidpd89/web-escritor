#!/usr/bin/env python3
"""Regression checks for the public tools-hub registry boundary."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "tools-hub.json"


def route_to_file(href: str) -> Path:
    if not (href.startswith("/") and href.endswith("/")):
        raise AssertionError(f"invalid registry route: {href}")
    return ROOT / href.strip("/") / "index.html"


data = json.loads(REGISTRY.read_text(encoding="utf-8"))
tools = data.get("tools", [])
directories = data.get("directories", [])
assert tools, "tools-hub registry must contain public tools"

hrefs = [item["href"] for item in tools] + [item["href"] for item in directories]
assert len(hrefs) == len(set(hrefs)), "duplicate public href in tools-hub registry"

# These routes intentionally exist, but are internal/noindex. They must not
# reappear as public hub products or public reference directories.
for internal_href in ("/herramientas/auditor-web/", "/publicar-web/"):
    assert internal_href not in hrefs, f"internal route leaked into public hub: {internal_href}"
    html_path = route_to_file(internal_href)
    assert html_path.exists(), f"internal route unexpectedly deleted: {internal_href}"
    html = html_path.read_text(encoding="utf-8").lower()
    assert 'name="robots"' in html and "noindex" in html, f"internal route lost noindex: {internal_href}"

# Every public registry target and tool implementation asset must exist.
for item in tools:
    page = route_to_file(item["href"])
    assert page.exists(), f"public tool target missing: {item['href']}"
    source = ROOT / item["source_doc"]
    assert source.exists(), f"tool implementation source missing: {item['slug']} -> {item['source_doc']}"

for item in directories:
    page = route_to_file(item["href"])
    assert page.exists(), f"public directory target missing: {item['href']}"
    html = page.read_text(encoding="utf-8").lower()
    assert not ('name="robots"' in html and "noindex" in html), f"noindex route exposed as public directory: {item['href']}"

# The generated hub is part of the same contract.
hub = (ROOT / "herramientas" / "index.html").read_text(encoding="utf-8")
assert "/herramientas/auditor-web/" not in hub
assert "/publicar-web/" not in hub
assert f">{len(tools)} herramientas<" in hub

print(f"PASS tools-hub boundary: {len(tools)} public tools, {len(directories)} public directories; internal routes preserved and hidden")
