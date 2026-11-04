#!/usr/bin/env python3
"""Contract for the Event JSON-LD shown in eventos.html.

Historical free signings retain their status, canonical anchors and dates.
There is no verified current ticket offer, so free attendance is represented
without inventing an Offer, availability or acquisition URL.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "eventos.html").read_text(encoding="utf-8")
CANONICAL = "https://davidportodiaz.com/eventos.html"
EXPECTED = {
    "feria-libro-madrid-2026": "2026-06-10T19:00:00+02:00",
    "feria-libro-aranjuez-2026": "2026-05-23",
}

blocks = re.findall(
    r'<script\s+type="application/ld\+json">\s*(.*?)\s*</script>',
    HTML,
    flags=re.S,
)
assert blocks, "eventos.html must contain JSON-LD"
nodes = []
for block in blocks:
    document = json.loads(block)
    nodes.extend(document.get("@graph", [document]))
events = [node for node in nodes if node.get("@type") == "Event"]
assert len(events) == len(EXPECTED), f"expected {len(EXPECTED)} Event nodes, got {len(events)}"

for event in events:
    event_id = event.get("@id", "")
    assert event_id.startswith(CANONICAL + "#"), f"Event id outside canonical URL: {event_id}"
    fragment = event_id.split("#", 1)[1]
    assert fragment in EXPECTED, f"Unexpected Event fragment: {fragment}"
    assert event.get("url") == event_id, f"Event url must preserve anchored canonical URL: {fragment}"
    assert event.get("eventStatus") == "https://schema.org/EventScheduled", f"Invalid/missing eventStatus: {fragment}"

    assert event.get("isAccessibleForFree") is True, f"Free attendance lost: {fragment}"
    assert "offers" not in event, f"Historical event must not invent a current ticket offer: {fragment}"

    assert str(event.get("startDate", "")).startswith(EXPECTED[fragment]), f"startDate drift: {fragment}"

print("test-eventos-jsonld-parity: OK (2 historical free events, canonical anchors and no invented offers)")
