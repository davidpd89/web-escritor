#!/usr/bin/env python3
"""A.7 regression: preserve Samuel's human FAQ while retiring FAQPage markup."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "libros/samuel-entre-mundos/index.html"

html = PAGE.read_text(encoding="utf-8")
assert 'id="faq"' in html, "Samuel's human FAQ section must remain available"
assert "Preguntas frecuentes." in html, "visible FAQ heading disappeared"
assert html.count("<details>") >= 8, "visible FAQ answers were removed with the schema"

nodes: list[dict] = []
for raw in re.findall(r'<script\s+type="application/ld\+json">\s*([\s\S]*?)\s*</script>', html, flags=re.I):
    doc = json.loads(raw)
    graph = doc.get("@graph") if isinstance(doc, dict) else None
    if isinstance(graph, list):
        nodes.extend(node for node in graph if isinstance(node, dict))
    elif isinstance(doc, dict):
        nodes.append(doc)

for node in nodes:
    node_type = node.get("@type")
    types = node_type if isinstance(node_type, list) else [node_type]
    assert "FAQPage" not in types, "Samuel must not reintroduce retired FAQPage markup"

assert any(node.get("@type") == "Book" for node in nodes), "Book structured data was removed accidentally"
assert any(node.get("@type") == "WebPage" for node in nodes), "WebPage structured data was removed accidentally"

print("samuel-faq-schema-retirement: OK")
