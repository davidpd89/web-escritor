#!/usr/bin/env python3
"""Turn an ALREADY DOWNLOADED Overture Places GeoJSON bbox into INTERNAL POI candidates.

Never fetches external APIs, never exports persons' contact details, never publishes.
Bounded in-memory loader: use small bboxes; global ingestion needs GeoParquet/DuckDB.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import uuid
from pathlib import Path

MAX_INPUT_BYTES = 16 * 1024 * 1024  # fail closed; this is NOT a global JSON parser

# Core taxonomy names checked against Overture 2026-09-23.0 CSV; legacy aliases retained.
# Source: OvertureMaps/docs/static/taxonomy/2026-09-23.0/taxonomy.csv
KEYWORDS = {
    "bookshop": ("bookstore", "academic_bookstore", "used_bookstore", "comic_books_store",
                 "book_store", "bookshop", "bookseller", "used_books"),
    "library": ("library", "libraries", "public_library"),
    "museum": ("museum", "literary_museum", "house_museum"),
    "historic_site": ("historic_site", "historical_site", "monument", "memorial", "memorial_site"),
}


def category_kind(props: dict) -> str | None:
    taxonomy = props.get("taxonomy") or {}
    strings = []
    if isinstance(taxonomy, dict):
        strings.extend([taxonomy.get("primary"), *(taxonomy.get("hierarchy") or []),
                        *(taxonomy.get("alternates") or [])])
    strings.append(props.get("basic_category"))
    # Legacy fallback is only to read older outputs; new September 2026 uses taxonomy.
    legacy = props.get("categories") or {}
    if isinstance(legacy, dict):
        strings.append(legacy.get("primary"))
    names = {str(s).casefold() for s in strings if isinstance(s, str)}
    for kind, aliases in KEYWORDS.items():
        if names.intersection(aliases):
            return kind
    return None


def first_name(props: dict) -> str | None:
    names = props.get("names") or {}
    if isinstance(names, dict):
        main = names.get("primary")
        if isinstance(main, str) and main.strip():
            return main.strip()
        common = names.get("common") or {}
        if isinstance(common, dict):
            for lang in ("es", "en", "fr", "de", "pt", "it"):
                if isinstance(common.get(lang), str) and common[lang].strip():
                    return common[lang].strip()
    return None


def candidate(feature: dict, release: str) -> dict | None:
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        return None
    props = feature.get("properties") or {}
    geom = feature.get("geometry") or {}
    if not isinstance(props, dict) or not isinstance(geom, dict):
        return None
    kind = category_kind(props)
    name = first_name(props)
    if not kind or not name or geom.get("type") != "Point":
        return None
    coords = geom.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        return None
    lon, lat = coords[:2]
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool)
               and math.isfinite(v) for v in (lat, lon)):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    raw_id = feature.get("id") or props.get("id")
    if not isinstance(raw_id, str):
        return None
    try:
        provider_id = str(uuid.UUID(raw_id))
    except ValueError:
        return None
    confidence = props.get("confidence")
    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
        confidence = None
    digest = hashlib.sha256(provider_id.encode("ascii")).hexdigest()[:20]
    return {
        "id": "ov-" + digest,
        "status": "candidate",
        "provider": "overture_places",
        "provider_id": provider_id,
        "provider_release": release,
        "kind_candidate": kind,
        "name": name,
        "longitude": lon, "latitude": lat,
        "geo_precision": "point_provider_unverified",
        "provider_confidence": confidence,
        "place_relation_status": "none",
        "verified_at": None,
        "provider_data_url": "https://docs.overturemaps.org/guides/places/",
        "license_status": "source_attribution_review_required",
        "evidence_warning": "POI genérico, NO demuestra escenario literario ni rodaje",
    }


def extract(data: dict, release: str, max_candidates: int = 1000) -> list[dict]:
    if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
        raise ValueError("Se requiere GeoJSON FeatureCollection de un bbox Overture")
    output = []
    seen = set()
    for feature in data["features"]:
        row = candidate(feature, release)
        if row and row["id"] not in seen:
            output.append(row)
            seen.add(row["id"])
        if len(output) >= max_candidates:
            break
    return output


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("geojson", type=Path, help="GeoJSON de bbox local, NUNCA URL de web")
    p.add_argument("--release", required=True, help="Versión verificable 2026-09-23.1, etc.")
    p.add_argument("--max-candidates", type=int, default=1000)
    p.add_argument("--out", type=Path, help="Salida JSONL interna, NO página web")
    a = p.parse_args()
    if not 1 <= a.max_candidates <= 10000:
        p.error("--max-candidates fuera de rango")
    if a.geojson.stat().st_size > MAX_INPUT_BYTES:
        p.error("GeoJSON >16 MiB; dividir por bbox o usar DuckDB/GeoParquet")
    if a.out and a.out.exists():
        p.error("No sobrescribir una instantánea existente")
    content = json.loads(a.geojson.read_text(encoding="utf-8"))
    items = extract(content, a.release, a.max_candidates)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        with a.out.open("x", encoding="utf-8") as stream:
            for row in items:
                stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"candidates": len(items), "release": a.release,
                      "status": "INTERNAL_NOT_VERIFIED"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
