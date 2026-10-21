#!/usr/bin/env python3
"""Preview-only on-demand facet JSON shards by destination (not sitewide megabyte blob).

Run with local approved internal snapshot, write only into atlas-preview folder.
Does NOT publish data, index filters, call APIs or build real site.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from atlas_static_preview import RELATION_SUBJECTS, approved, destination_url, eligible, place_url, safe_slug, valid_https_url


def facet_shards(data: dict) -> tuple[dict, dict[str, dict]]:
    destinations, places = eligible(data)
    valid_places = {p["id"]: p for p in places}
    approved_subjects = {}
    for table, label in (("works", "title"), ("authors", "name"), ("adaptations", "title")):
        approved_subjects[table] = {v["id"]: v.get(label, "")
                                    for v in data.get(table, []) if approved(v)}
    table_by_type = {"work": "works", "author": "authors", "adaptation": "adaptations"}
    source_ids = {
        s["id"] for s in data.get("sources", [])
        if valid_https_url(s.get("url"))
        and s.get("title") and s.get("retrieved_at") and s.get("evidence_summary")
    }
    by_place: dict[str, list[dict]] = defaultdict(list)
    for r in data.get("relationships", []):
        if not approved(r) or r.get("place_id") not in valid_places:
            continue
        if (RELATION_SUBJECTS.get(r.get("relationship_type")) != r.get("subject_type")
                or not r.get("evidence_note")):
            continue
        table = table_by_type.get(r.get("subject_type"))
        if not table or r.get("subject_id") not in approved_subjects[table]:
            continue
        refs = r.get("source_ids") or []
        if not isinstance(refs, list) or not refs or not all(
                isinstance(ref, str) and ref in source_ids for ref in refs
        ):
            continue
        by_place[r["place_id"]].append({
            "relation": r.get("relationship_type"),
            "subject_type": r["subject_type"],
            "subject_id": r["subject_id"],
            "subject_name": approved_subjects[table][r["subject_id"]],
        })
    shards: dict[str, dict] = {}
    countries: dict[str, dict] = {}
    for d in sorted(destinations, key=lambda d: (d["country_iso2"], d["name"])):
        slug = safe_slug(d["slug"])
        country = d["country_iso2"]
        if not isinstance(country, str) or len(country) != 2 or not country.isascii() or not country.isalpha() or country != country.upper():
            raise ValueError("ISO2 no válido en " + slug)
        ps = [p for p in places if p.get("destination_id") == d["id"]]
        values = [{
            "id": p["id"], "name": p["name"], "url": place_url(p),
            "type": p["place_type"],
            "relations": sorted(by_place.get(p["id"], []),
                                key=lambda r: (r["subject_type"], r["subject_name"], r["relation"])),
        } for p in sorted(ps, key=lambda p: p["name"])]
        if slug in shards:
            raise ValueError("Slug de destino duplicado: " + slug)
        shards[slug] = {"version": 1, "destination": {"name": d["name"], "url": destination_url(d)},
                        "places": values}
        c = countries.setdefault(country, {"iso2": country, "destinations": []})
        c["destinations"].append({
            "slug": slug, "name": d["name"], "url": destination_url(d),
            "count": len(values), "place_types": dict(sorted(Counter(p["type"] for p in values).items()))
        })
    manifest = {"version": 1, "countries": [countries[k] for k in sorted(countries)]}
    return manifest, shards


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if "atlas-preview" not in args.out.parts:
        parser.error("Salida restringida a atlas-preview")
    manifest, shards = facet_shards(json.loads(args.snapshot.read_text(encoding="utf-8")))
    root = args.out / "atlas-literario/facets"
    (root / "destinos").mkdir(parents=True, exist_ok=True)
    (root / "index.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True) + "\n",
                                     encoding="utf-8")
    for slug, shard in shards.items():
        (root / "destinos" / (slug + ".json")).write_text(
            json.dumps(shard, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Preview facetas: {len(shards)} destinos, {len(manifest['countries'])} países")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
