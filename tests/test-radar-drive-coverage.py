#!/usr/bin/env python3
"""Preserve reviewed contest coverage and keep unverified calls out of the calendar."""
import importlib.util
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("radar", ROOT / "scripts/build-radar-opportunities.py")
radar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(radar)
data_path = ROOT / "data/radar-opportunities.json"
items = radar.load_items(data_path)
watch = radar.load_watchlist(data_path)
radar.ensure_disjoint_ids(items, watch)
coverage = json.loads((ROOT / "docs/qa/contest-coverage-2026-10-19.json").read_text(encoding="utf-8"))
assert coverage["source_rows"] == len(coverage["entries"]) == 162
assert all(set(entry) == {"title", "id"} for entry in coverage["entries"]), "coverage must contain public titles and IDs only"
targets = {entry["id"] for entry in coverage["entries"]}
assert len(targets) == 157, "weekly rounds and shared modalities are intentionally grouped"
clock = date.fromisoformat(coverage["reviewed_at"])
public = json.loads(radar.public_json(items, clock, watch))
published = {item["id"] for key in ("items", "expired", "watchlist") for item in public[key]}
assert targets <= published, f"reviewed contests missing from public output: {sorted(targets - published)}"
ics = radar.build_ics(items, clock)
pending = [item for item in watch if item.get("watch_kind") == "verification"]
assert pending, "the source review has unresolved primary bases"
for item in pending:
    radar.validate_watch(item)
    card = radar.watch_card(item)
    assert "Pendiente de verificar" in card
    assert "Consultar convocatoria y bases" in card
    assert 'data-deadline=""' in card
    assert item["id"] not in ics, f"unverified call leaked into calendar: {item['id']}"
assert "arteaula-relato-corto-2027-watch" not in ics, "announced future opening is not an open call"
assert "aama-literatura-aeronautica-2026@" in ics, "verified AAMA deadline must reach the calendar"
assert "elcano-centenario-relato-micro-2027@" in ics, "both Elcano modalities share one calendar event"
print("test-radar-drive-coverage: 162 rows / 157 public targets; pending calls excluded from ICS: OK")
