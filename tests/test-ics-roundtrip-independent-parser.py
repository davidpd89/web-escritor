#!/usr/bin/env python3
"""Round-trip test (item 9 of the 2026-09 audit round) for every ICS and
JSON-LD generator in the repository: a JS/Python-generated calendar or
structured-data payload might satisfy its own generator's structural
assertions (right prefix, right property names) while still being subtly
malformed in a way only a real, independent implementation would reject.

tests/test-evento-ics-rfc5545.mjs already documents that this was checked
once "out of band" with Python's icalendar library, but never turned that
into a regression test -- so a future change could reintroduce a real
parsing break and nothing in CI would catch it. This test does that for
both this site's ICS producers:

  - assets/evento-escritor-core.js (the client-side event tool)
  - scripts/build-radar-opportunities.py (the Convocatorias radar's
    already-published deadlines.ics, re-parsed here as well as the live
    convocatorias-escritores/deadlines.ics file)

and confirms the event tool's JSON-LD re-parses with Python's own
json.loads (independent of the V8/JS JSON implementation that produced it).

Uso:
  python tests/test-ics-roundtrip-independent-parser.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from icalendar import Calendar

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []


def check(condition: bool, label: str) -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


# --- 1. evento-escritor-core.js: ICS + JSON-LD -----------------------------
result = subprocess.run(
    ["node", str(ROOT / "tests" / "fixtures" / "evento-ics-gen.mjs")],
    cwd=ROOT, capture_output=True, encoding="utf-8",
)
check(result.returncode == 0, f"evento-escritor-core.js generator exits 0 (stderr: {result.stderr.strip()[:200]})")
payload = json.loads(result.stdout.strip().splitlines()[-1])

cal = Calendar.from_ical(payload["ics"])
events = [c for c in cal.walk() if c.name == "VEVENT"]
check(len(events) == 1, "icalendar parses exactly 1 VEVENT from the event tool's ICS")
if events:
    ev = events[0]
    check(str(ev.get("summary")).startswith("Presentación"), "SUMMARY round-trips with accents intact")
    dtstart = ev.get("dtstart").dt
    check(dtstart.hour == 17 and dtstart.minute == 0, f"DTSTART is 17:00 UTC per icalendar (got {dtstart})")
    check("línea deliberadamente larga" in str(ev.get("description")), "folded DESCRIPTION unfolds correctly")

ld = json.loads(payload["jsonLd"])  # Python's own JSON parser, not V8's.
check(ld.get("@type") == "Event", "event tool's JSON-LD re-parses with json.loads and keeps @type Event")
check(bool(ld.get("location", {}).get("address", {}).get("addressLocality")), "JSON-LD nested address survives re-parse")

# --- 2. build-radar-opportunities.py: ICS ----------------------------------
spec = importlib.util.spec_from_file_location("build_radar", ROOT / "scripts" / "build-radar-opportunities.py")
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)

data = json.loads((ROOT / "data" / "radar-opportunities.json").read_text(encoding="utf-8"))
items = br.load_items(ROOT / "data" / "radar-opportunities.json")
generated_ics = br.build_ics(items, date.fromisoformat("2026-08-22"))

radar_cal = Calendar.from_ical(generated_ics)
radar_events = [c for c in radar_cal.walk() if c.name == "VEVENT"]
active_count = len(br.active_items(items, date.fromisoformat("2026-08-22")))
check(len(radar_events) == active_count, f"icalendar parses {active_count} VEVENT(s) from the radar builder's ICS")

# The committed deadlines.ics is the same content the browser actually
# serves -- parse that file directly too, independent of build_ics().
live_ics_path = ROOT / "convocatorias-escritores" / "deadlines.ics"
if live_ics_path.exists():
    live_cal = Calendar.from_ical(live_ics_path.read_bytes())
    check(len([c for c in live_cal.walk() if c.name == "VEVENT"]) >= 0, "the committed deadlines.ics parses with icalendar")

print(f"tests/test-ics-roundtrip-independent-parser: {'OK' if not failures else f'{len(failures)} FALLO(S)'}")
raise SystemExit(1 if failures else 0)
