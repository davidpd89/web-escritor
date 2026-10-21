#!/usr/bin/env python3
"""Normalize prefiltered Overture POI candidates into Atlas v1 PLACE fragments.

Never approves or publishes. Explicit destination ID and bounding box required;
never guesses a city from a point, a string, or a country centroid.
Output is a FRAGMENT for the review system, not a complete public catalogue.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ID = re.compile(r"^[a-z][a-z0-9-]{2,79}$")
TYPES = {"bookshop": "bookshop", "library": "library",
         "museum": "museum", "historic_site": "historic_site"}


def within(lon: float, lat: float, bbox: tuple[float, float, float, float]) -> bool:
    west, south, east, north = bbox
    # This first adapter intentionally excludes anti-meridian crossing bbox;
    # such regions should be split into two inputs for exact membership.
    if west > east or south > north:
        raise ValueError("bbox invertida: divide las zonas del antimeridiano")
    return west <= lon <= east and south <= lat <= north


def normalize(rows: list[dict], *, destination_id: str,
              bbox: tuple[float, float, float, float], source_id: str) -> list[dict]:
    if not ID.fullmatch(destination_id) or not ID.fullmatch(source_id):
        raise ValueError("IDs editoriales incompatibles con contrato #669")
    records, unique = [], set()
    for row in rows:
        if row.get("status") != "candidate" or row.get("provider") != "overture_places":
            continue
        if row.get("kind_candidate") not in TYPES:
            continue
        lon, lat = row.get("longitude"), row.get("latitude")
        if (not isinstance(lon, (int, float)) or isinstance(lon, bool)
                or not isinstance(lat, (int, float)) or isinstance(lat, bool)):
            continue
        if not -180 <= lon <= 180 or not -90 <= lat <= 90 or not within(lon, lat, bbox):
            continue
        oid, gers = row.get("id"), row.get("provider_id")
        if not isinstance(oid, str) or not ID.fullmatch(oid) or oid in unique:
            continue
        if not isinstance(gers, str) or not row.get("provider_release"):
            continue
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        unique.add(oid)
        # No page slug generated from an untrusted or translated name.
        records.append({
            "id": oid, "slug": oid, "name": name.strip(),
            "destination_id": destination_id,
            "place_type": TYPES[row["kind_candidate"]],
            "geo_precision": "point",
            "latitude": lat, "longitude": lon,
            "overture_gers_id": gers,
            "overture_release": row["provider_release"],
            "overture_confidence": row.get("provider_confidence"),
            "status": "candidate",
            "source_ids": [source_id],
            # Deliberately NO summary_original and verified_at: publication gate fails.
        })
    return records


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidate_jsonl", type=Path)
    p.add_argument("--destination-id", required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--bbox", required=True, nargs=4, type=float,
                   metavar=("WEST", "SOUTH", "EAST", "NORTH"))
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    if a.out.exists() or a.out.resolve() == a.candidate_jsonl.resolve():
        p.error("No sobrescribir archivos de entrada ni salidas existentes")
    if a.candidate_jsonl.stat().st_size > 16 * 1024 * 1024:
        p.error("Demasiado grande: procesar por bbox más pequeña")
    lines = a.candidate_jsonl.read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in lines if line.strip()]
    places = normalize(rows, destination_id=a.destination_id,
                       source_id=a.source_id, bbox=tuple(a.bbox))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({"schema_version": 1, "places": places},
                                ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(places)} POIs candidatos para revisión; ninguno está aprobado ni publicado")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
