#!/usr/bin/env python3
"""Offline, REVIEW-ONLY duplicate proposals between candidate POIs.

Reads up to 3000 normalized candidates from two local Atlas JSON snapshots.
Nothing is merged or published. Never infer book/author/film relationships.
Deliberately lightweight pilot; global jobs need indexed DuckDB partitions.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

MAX_RECORDS = 3000
MAX_INPUT_BYTES = 4 * 1024 * 1024
ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,79}$")
QID = re.compile(r"^Q[1-9][0-9]*$")
STRONG_ID_FIELDS = ("wikidata_qid", "overture_gers_id", "geonames_id", "pleiades_id")


def clean_name(value: object) -> str:
    if not isinstance(value, str):
        return ""
    base = unicodedata.normalize("NFKD", value.casefold())
    base = "".join(char for char in base if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", base))


def coordinates(row: dict) -> tuple[float, float] | None:
    if row.get("geo_precision") not in ("point", "building"):
        return None  # NEVER compare place-centroid approximations as buildings.
    lat, lon = row.get("latitude"), row.get("longitude")
    if not all(isinstance(x, (int, float)) and not isinstance(x, bool)
               and math.isfinite(x) for x in (lat, lon)):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return float(lat), float(lon)


def metres(p: tuple[float, float], q: tuple[float, float]) -> int:
    dlat = math.radians(q[0] - p[0])
    dlon = math.radians(q[1] - p[1])
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(p[0])) * math.cos(
        math.radians(q[0])) * math.sin(dlon / 2) ** 2
    return round(12_742_000 * math.asin(min(1.0, math.sqrt(a))))


def strong_keys(row: dict) -> set[str]:
    result: set[str] = set()
    for key in STRONG_ID_FIELDS:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            if key == "wikidata_qid" and not QID.fullmatch(value):
                continue
            result.add(key + ":" + value.strip())
    osm_type, osm_id = row.get("osm_type"), row.get("osm_id")
    if osm_type in {"node", "way", "relation"} and isinstance(osm_id, (str, int)):
        if str(osm_id).isdigit():
            result.add("osm:" + osm_type + ":" + str(osm_id))
    return result


def valid_rows(rows: list[dict]) -> list[dict]:
    if len(rows) > MAX_RECORDS:
        raise ValueError(f"Máximo {MAX_RECORDS} POIs para piloto; usar DuckDB por bloques")
    seen = set()
    clean: list[dict] = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise ValueError("Registro candidato sin id")
        rid = row["id"]
        if not ID_PATTERN.fullmatch(rid) or rid in seen:
            raise ValueError(f"ID duplicado/no válido: {rid!r}")
        seen.add(rid)
        if row.get("status") != "candidate":
            raise ValueError("Solo candidatos internos son admisibles")
        if not isinstance(row.get("destination_id"), str):
            raise ValueError("Asignar destino editorial antes de comparar")
        if not isinstance(row.get("name"), str) or not row["name"].strip():
            raise ValueError("Nombre de POI vacío")
        clean.append(row)
    return clean


def propose(left: list[dict], right: list[dict]) -> list[dict]:
    left, right = valid_rows(left), valid_rows(right)
    common_ids = {p["id"] for p in left} & {p["id"] for p in right}
    if common_ids:
        raise ValueError("Mismo ID editorial en dos proveedores: revisar antes de vincular")
    index_id: dict[str, list[dict]] = defaultdict(list)
    index_name: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in right:
        for key in strong_keys(r):
            index_id[key].append(r)
        name = clean_name(r["name"])
        if name:
            index_name[(r["destination_id"], name)].append(r)
    pairs = {}
    for a in left:
        akeys = strong_keys(a)
        known = {}
        for key in akeys:
            for b in index_id.get(key, []):
                known[b["id"]] = b
        for b in known.values():
            if a["destination_id"] == b["destination_id"]:
                status = "shared_external_id_review"
            else:
                status = "same_id_different_destination_review"
            pair_id = (a["id"], b["id"])
            pairs[pair_id] = {
                "left_id": a["id"], "right_id": b["id"], "left_name": a["name"],
                "right_name": b["name"], "decision": "REVIEW_REQUIRED",
                "reason": status, "shared_keys": sorted(akeys & strong_keys(b)),
                "distance_m": None, "automatic_merge": False,
            }
        coord = coordinates(a)
        if coord is None:
            continue
        for b in index_name.get((a["destination_id"], clean_name(a["name"])), []):
            key = (a["id"], b["id"])
            if key in pairs:
                continue
            destcoord = coordinates(b)
            if destcoord is None:
                continue
            distance = metres(coord, destcoord)
            if distance > 150:
                continue
            # Conflicting cross-source Wikidata QIDs are a stronger negative than
            # proximity + name, but the situation deserves editorial review.
            qa, qb = a.get("wikidata_qid"), b.get("wikidata_qid")
            conflicting = bool(qa and qb and qa != qb)
            pairs[key] = {
                "left_id": a["id"], "right_id": b["id"],
                "left_name": a["name"], "right_name": b["name"],
                "decision": "REVIEW_REQUIRED",
                "reason": "conflicting_qids_review" if conflicting else "same_name_nearby_review",
                "shared_keys": [],
                "distance_m": distance, "automatic_merge": False,
            }
    return [pairs[key] for key in sorted(pairs)]


def load(path: Path) -> list[dict]:
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("Archivo >4 MiB, dividir por destinos y ejecutar en lotes")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Se espera fragmento JSON schema_version=1")
    rows = data.get("places")
    if not isinstance(rows, list):
        raise ValueError("Se espera places[]")
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--left", required=True, type=Path)
    p.add_argument("--right", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    if a.left.resolve() == a.right.resolve():
        p.error("Se necesitan dos snapshots distintos")
    if a.out.exists():
        p.error("Salida existente: no sobrescribir las decisiones editoriales")
    results = propose(load(a.left), load(a.right))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({"schema_version": 1, "status": "REVIEW_ONLY",
                                 "proposals": results}, ensure_ascii=False, indent=2)
                     + "\n", encoding="utf-8")
    print(f"{len(results)} posibles identidades para revisar; 0 uniones automáticas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
