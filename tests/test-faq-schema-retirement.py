#!/usr/bin/env python3
"""A.7 regression: retire known FAQPage markup without deleting human FAQs."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    "Samuel": {
        "path": ROOT / "libros/samuel-entre-mundos/index.html",
        "human_marker": 'id="faq"',
        "heading": "Preguntas frecuentes.",
        "min_details": 8,
        "required_types": {"Book", "WebPage"},
    },
    "Noveris": {
        "path": ROOT / "universo/noveris/index.html",
        "human_marker": 'id="preguntas-frecuentes"',
        "heading": "Preguntas frecuentes.",
        "min_details": 5,
        "required_types": {"WebPage", "DefinedTermSet"},
    },
    "Cuaderno / que-es-el-portal-fantasy": {
        "path": ROOT / "cuaderno/que-es-el-portal-fantasy/index.html",
        "human_marker": 'id="faq"',
        "heading": "Preguntas frecuentes",
        "min_details": 3,
        "required_types": {"Article", "BreadcrumbList"},
    },
    "Cuaderno / portal-fantasy-vs-fantasia-epica": {
        "path": ROOT / "cuaderno/portal-fantasy-vs-fantasia-epica/index.html",
        "human_marker": 'id="faq"',
        "heading": "Preguntas frecuentes",
        "min_details": 3,
        "required_types": {"Article", "BreadcrumbList"},
    },
    "Cuaderno / fantasia-juvenil-espanola-portales-magia-coste": {
        "path": ROOT / "cuaderno/fantasia-juvenil-espanola-portales-magia-coste/index.html",
        "human_marker": 'id="faq"',
        "heading": "Preguntas frecuentes",
        "min_details": 3,
        "required_types": {"Article", "BreadcrumbList"},
    },
    "Cuaderno / libros-fantasia-juvenil-espanola-2025-2026": {
        "path": ROOT / "cuaderno/libros-fantasia-juvenil-espanola-2025-2026/index.html",
        "human_marker": 'id="faq"',
        "heading": "Preguntas frecuentes",
        "min_details": 3,
        "required_types": {"Article", "BreadcrumbList"},
    },
    "Cuaderno / worldbuilding-noveris-ciudad-magica": {
        "path": ROOT / "cuaderno/worldbuilding-noveris-ciudad-magica/index.html",
        "human_marker": 'id="preguntas-frecuentes"',
        "heading": "Preguntas frecuentes",
        "min_details": 4,
        "required_types": {"Article", "BreadcrumbList"},
    },
}


def structured_nodes(html: str) -> list[dict]:
    nodes: list[dict] = []
    for raw in re.findall(r'<script\s+type="application/ld\+json">\s*([\s\S]*?)\s*</script>', html, flags=re.I):
        doc = json.loads(raw)
        graph = doc.get("@graph") if isinstance(doc, dict) else None
        if isinstance(graph, list):
            nodes.extend(node for node in graph if isinstance(node, dict))
        elif isinstance(doc, dict):
            nodes.append(doc)
    return nodes


for label, contract in PAGES.items():
    html = contract["path"].read_text(encoding="utf-8")
    assert contract["human_marker"] in html, f"{label}: human FAQ section disappeared"
    assert contract["heading"] in html, f"{label}: visible FAQ heading disappeared"
    assert html.count("<details") >= contract["min_details"], f"{label}: visible FAQ answers were removed with schema"

    nodes = structured_nodes(html)
    for node in nodes:
        node_type = node.get("@type")
        types = node_type if isinstance(node_type, list) else [node_type]
        assert "FAQPage" not in types, f"{label}: retired FAQPage markup was reintroduced"

    seen_types = {
        t
        for node in nodes
        for t in (node.get("@type") if isinstance(node.get("@type"), list) else [node.get("@type")])
        if isinstance(t, str)
    }
    missing = contract["required_types"] - seen_types
    assert not missing, f"{label}: unrelated structured-data types removed accidentally: {sorted(missing)}"

print("faq-schema-retirement: OK")
