#!/usr/bin/env python3
"""Read one saved Pleiades place JSON and propose an internal historic-place candidate.

Pleiades geographic evidence != fiction settings. Never infer scene/author, use
a precise point for a site from reprPoint alone, or publish on provider status.
Offline only; download/release handling intentionally separate.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

MAX_FILE_BYTES = 2 * 1024 * 1024
NUMERIC_ID = re.compile(r"^[0-9]{1,18}$")


def aliases_from(names: object, title: str, max_aliases: int = 40) -> list[dict]:
    """Preserve historical names/periods and do not copy bibliographic HTML."""
    seen: set[tuple[str, str]] = set()
    output: list[dict] = []
    if not isinstance(names, list):
        return output
    for record in names:
        if not isinstance(record, dict):
            continue
        period = []
        attestations = record.get("attestations") or []
        if isinstance(attestations, list):
            period = sorted({
                item.get("timePeriod") for item in attestations
                if isinstance(item, dict) and isinstance(item.get("timePeriod"), str)
            })
        language = record.get("language") if isinstance(record.get("language"), str) else ""
        for field in ("romanized", "attested"):
            value = record.get(field)
            if not isinstance(value, str):
                continue
            value = " ".join(value.split()).strip()
            if not value or len(value) > 160 or value.casefold() == title.casefold():
                continue
            key = (value.casefold(), language)
            if key in seen:
                continue
            seen.add(key)
            output.append({"name": value, "language": language or None,
                           "periods": period, "from": field})
            if len(output) >= max_aliases:
                return output
    return output


def place_candidate(raw: dict, *, release: str) -> dict | None:
    if not isinstance(raw, dict):
        return None
    ident = raw.get("id")
    ident = str(ident) if isinstance(ident, (int, str)) and not isinstance(ident, bool) else ""
    title = raw.get("title")
    if not NUMERIC_ID.fullmatch(ident) or not isinstance(title, str) or not title.strip():
        return None
    # "published" refers to Pleiades editorial review, not ours.
    if raw.get("review_state") not in ("published", "reviewed"):
        return None
    title = " ".join(title.split())[:160]
    coords = raw.get("reprPoint")
    point = None
    if (isinstance(coords, list) and len(coords) == 2
            and all(isinstance(x, (float, int)) and not isinstance(x, bool)
                    and math.isfinite(x) for x in coords)
            and -180 <= coords[0] <= 180 and -90 <= coords[1] <= 90):
        point = {"longitude": coords[0], "latitude": coords[1]}
    names = aliases_from(raw.get("names"), title)
    types = raw.get("placeTypes") or []
    kinds = sorted({str(k) for k in types if isinstance(k, str) and len(k) < 80}) if isinstance(types, list) else []
    return {
        "id": "pl-" + ident, "provider": "pleiades", "provider_id": ident,
        "provider_url": "https://pleiades.stoa.org/places/" + ident,
        "provider_release": release,
        "title": title, "aliases": names, "provider_place_types": kinds,
        "representative_point": point,
        "geo_precision": "area_or_city" if point else "unlocated",
        "status": "candidate", "literary_relation_status": "none",
        "dataset_license": "CC-BY-3.0",
        "attribution_required": True,
        "note": "Topónimo histórico; no prueba ambientación de ninguna novela ni precisión de fachada",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("pleiades_json", type=Path, help="Un JSON individual guardado previamente")
    p.add_argument("--release", required=True, help="Version de dump o fecha de consulta")
    p.add_argument("--output", type=Path, help="Nuevo JSON solo para revisión")
    args = p.parse_args()
    if args.pleiades_json.stat().st_size > MAX_FILE_BYTES:
        p.error("Archivo >2 MiB; usar conversor de dumps en futura PR independiente")
    if args.output and (args.output.exists() or args.output.resolve() == args.pleiades_json.resolve()):
        p.error("No sobrescribir la entrada ni una salida existente")
    raw = json.loads(args.pleiades_json.read_text(encoding="utf-8"))
    item = place_candidate(raw, release=args.release)
    if item is None:
        print("Pleiades candidato inválido/pendiente, sin salida")
        return 1
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    print(json.dumps({"id": item["id"], "status": item["status"],
                      "alias_count": len(item["aliases"]),
                      "has_representative_point": item["representative_point"] is not None}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
