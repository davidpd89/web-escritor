#!/usr/bin/env python3
"""Static parity/security contract for ferias.html.

No network access: this test validates only repository state and local assets.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "ferias.html"
HTML = PAGE.read_text(encoding="utf-8")
CANONICAL = "https://davidportodiaz.com/ferias.html"
EVENT_IDS = {
    "feria-libro-aranjuez-2026": "2026-05-23",
    "feria-libro-madrid-2026": "2026-06-10",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def local_path(url: str) -> Path | None:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        if parsed.netloc != "davidportodiaz.com":
            return None
        path = parsed.path
    else:
        path = url.split("?", 1)[0].split("#", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    return ROOT / path.lstrip("/")


ids = re.findall(r'\bid="([^"]+)"', HTML)
require(len(ids) == len(set(ids)), "ferias.html contains duplicate IDs")
for event_id in EVENT_IDS:
    require(event_id in ids, f"missing canonical anchor #{event_id}")
for alias in ("aranjuez", "madrid"):
    require(alias in ids, f"missing historical alias #{alias}")

canonical_match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', HTML)
require(canonical_match is not None, "canonical link missing")
require(canonical_match.group(1) == CANONICAL, "canonical changed unexpectedly")

scripts = re.findall(
    r'<script\s+type="application/ld\+json">\s*(.*?)\s*</script>',
    HTML,
    flags=re.S,
)
require(scripts, "JSON-LD missing")
documents = [json.loads(script) for script in scripts]
nodes = []
for document in documents:
    nodes.extend(document.get("@graph", [document]))
events = [node for node in nodes if node.get("@type") == "Event"]
require(len(events) == 2, f"expected exactly 2 Event nodes, got {len(events)}")

for event in events:
    event_id = event.get("@id", "")
    require(event_id.startswith(CANONICAL + "#"), f"Event @id is not under canonical page: {event_id}")
    fragment = event_id.split("#", 1)[1]
    require(fragment in EVENT_IDS, f"unexpected Event fragment #{fragment}")
    require(fragment in ids, f"Event @id does not resolve to a real anchor: #{fragment}")
    require(event.get("url") == event_id, f"Event url must equal its anchored @id: {fragment}")
    require(event.get("eventStatus") == "https://schema.org/EventCompleted", f"past event is not EventCompleted: {fragment}")
    require(event.get("eventStatus") != "https://schema.org/EventScheduled", f"past event is EventScheduled: {fragment}")
    visible_date = EVENT_IDS[fragment]
    require(str(event.get("startDate", "")).startswith(visible_date), f"startDate mismatch for {fragment}")
    require(f'datetime="{visible_date}"' in HTML, f"visible date missing for {fragment}")
    require(event.get("offers", {}).get("url") == event_id, f"Offer url not anchored canonically for {fragment}")
    image = event.get("image")
    require(isinstance(image, str) and image, f"Event image missing for {fragment}")
    image_path = local_path(image)
    require(image_path is not None and image_path.is_file(), f"Event image does not exist locally: {image}")

aranjuez = next(event for event in events if "aranjuez" in event["@id"])
require(aranjuez["startDate"] == "2026-05-23", "Aranjuez must remain date-only until an individual signing time is verified")
require(aranjuez["endDate"] == "2026-05-23", "Aranjuez endDate must remain date-only")
require("10:00–11:30" not in HTML and "10:00-11:30" not in HTML, "unverified Aranjuez time leaked back into ferias.html")
require(
    aranjuez.get("organizer", {}).get("url")
    == "https://www.aranjuez.es/eres-autor-libreria-o-editorial-inscribete-en-la-feria-del-libro-de-aranjuez-2026/",
    "Aranjuez organizer must point to the official municipal source",
)

madrid = next(event for event in events if "madrid" in event["@id"])
require(madrid["startDate"] == "2026-06-10T19:00:00+02:00", "Madrid start time drifted")
require(madrid["endDate"] == "2026-06-10T20:00:00+02:00", "Madrid end time drifted")
require("caseta 337" in HTML.lower(), "Madrid caseta 337 missing from visible archive")

for src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', HTML):
    path = local_path(src)
    require(path is not None and path.is_file(), f"local image missing: {src}")

require('href="/eventos.html"' in HTML, "archive lacks a clear exit to /eventos.html")
require("Ver agenda completa" in HTML, "agenda exit copy missing")
require(
    'href="/cuaderno/feria-libro-madrid-2026-samuel-entre-mundos/"' in HTML,
    "authorized Madrid chronicle link missing",
)
require("fragmento-gratis.webp" not in HTML, "promotional fragment artwork must not appear inside the documentary fair archive")
require("mailto:samuelentremundos" not in HTML, "generic event-solicitation CTA duplicated into the documentary archive")

print("ferias parity: OK")
