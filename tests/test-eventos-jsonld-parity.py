#!/usr/bin/env python3
"""Contract for the Event JSON-LD shown in eventos.html.

The Google Search Console Event enhancement requires each event to expose a
valid status; upcoming events also expose an Offer, past events do not. Offers intentionally contain only the canonical URL:
the site has no verified ticket price or commerce endpoint for these past public
signings, so the test must not force invented price data.
"""
from __future__ import annotations

import json
import re
from datetime import date
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

    # Un evento ya celebrado no anuncia entradas (Search Console lo marca); uno futuro y gratuito sí lleva Offer a 0 EUR.
    end = str(event.get("endDate") or event.get("startDate", ""))[:10]
    if date.fromisoformat(end) < date.today():
        assert "offers" not in event, f"Past event must not advertise tickets: {fragment}"
        assert event.get("isAccessibleForFree") is True, f"Past free event must keep isAccessibleForFree: {fragment}"
    else:
        offer = event.get("offers")
        assert isinstance(offer, dict), f"Offer object missing: {fragment}"
        assert offer.get("@type") == "Offer", f"Offer type missing: {fragment}"
        assert offer.get("price") == "0", f"Free event must expose price 0: {fragment}"
        assert offer.get("priceCurrency") == "EUR", f"Free event must expose EUR currency: {fragment}"
        assert "url" not in offer, "Offer must not invent a ticket/acquisition URL"

    assert str(event.get("startDate", "")).startswith(EXPECTED[fragment]), f"startDate drift: {fragment}"

print("test-eventos-jsonld-parity: OK (2 Event nodes with valid status; offers only while upcoming)")
