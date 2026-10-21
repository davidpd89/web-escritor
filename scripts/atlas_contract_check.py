#!/usr/bin/env python3
"""Offline referential-integrity gate for the future worldwide literary atlas.

This is a supplementary check, not a full JSON Schema implementation. No network,
web publication, Actions, model calls, or writes. Input is internal draft JSON.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ID = re.compile(r"^[a-z][a-z0-9-]{2,79}$")
QID = re.compile(r"^Q[1-9][0-9]*$")
RELATIONS = {
    "narrative_explicit": "work",
    "inspiration_documented": "work",
    "filming_location": "adaptation",
    "author_public_history": "author",
    "literary_homage": "work",
    "popular_claim_unverified": "work",
}
APPROVED = "approved"
COLLECTIONS = ("destinations", "places", "works", "authors", "adaptations",
               "sources", "relationships", "images", "routes")


def problems(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return ["schema_version debe ser 1"]
    tables: dict[str, dict[str, dict]] = {}
    for category in COLLECTIONS:
        values = data.get(category)
        if not isinstance(values, list):
            errors.append(f"{category}: falta una lista")
            tables[category] = {}
            continue
        table = {}
        for index, entry in enumerate(values):
            if not isinstance(entry, dict):
                errors.append(f"{category}[{index}]: objeto esperado")
                continue
            eid = entry.get("id")
            if not isinstance(eid, str) or not ID.fullmatch(eid):
                errors.append(f"{category}[{index}]: id inválido")
                continue
            if eid in table:
                errors.append(f"{category}: id duplicado {eid}")
            table[eid] = entry
        tables[category] = table

    def require(category: str, key: object, scope: str) -> None:
        if not isinstance(key, str) or key not in tables[category]:
            errors.append(f"{scope}: referencia {category}={key!r} no existe")

    def require_approved(category: str, key: object, scope: str) -> None:
        entry = tables[category].get(key) if isinstance(key, str) else None
        if entry is not None and entry.get("status") != APPROVED:
            errors.append(f"{scope}: {category}={key!r} no aprobado")

    for place in tables["places"].values():
        scope = f"places/{place['id']}"
        require("destinations", place.get("destination_id"), scope)
        lat, lon = place.get("latitude"), place.get("longitude")
        if (lat is None) != (lon is None):
            errors.append(scope + ": latitude y longitude deben aparecer juntas")
        if lat is not None and (not isinstance(lat, (int, float)) or isinstance(lat, bool)
                                or not -90 <= lat <= 90):
            errors.append(scope + ": latitude fuera de rango")
        if lon is not None and (not isinstance(lon, (int, float)) or isinstance(lon, bool)
                                or not -180 <= lon <= 180):
            errors.append(scope + ": longitude fuera de rango")
        if place.get("geo_precision") == "unlocated" and lat is not None:
            errors.append(scope + ": unlocated no admite coordenadas")
        if place.get("status") == APPROVED:
            if not place.get("summary_original") or not place.get("source_ids"):
                errors.append(scope + ": aprobado requiere texto original y fuente")
            require_approved("destinations", place.get("destination_id"), scope)
        for image_id in place.get("image_ids", []):
            require("images", image_id, scope)
        for source_id in place.get("source_ids", []):
            require("sources", source_id, scope)
        if place.get("osm_id") and not place.get("osm_type"):
            errors.append(scope + ": osm_id requiere osm_type")

    for work in tables["works"].values():
        for author_id in work.get("author_ids", []):
            require("authors", author_id, f"works/{work['id']}")
    for adaptation in tables["adaptations"].values():
        require("works", adaptation.get("original_work_id"), f"adaptations/{adaptation['id']}")
    for relation in tables["relationships"].values():
        scope = f"relationships/{relation['id']}"
        require("places", relation.get("place_id"), scope)
        typ = relation.get("relationship_type")
        required_subject = RELATIONS.get(typ)
        if required_subject is None:
            errors.append(scope + f": tipo_relacion desconocido {typ!r}")
        if relation.get("subject_type") != required_subject:
            errors.append(scope + ": tipo_relacion/subject_type incompatibles")
        else:
            table = {"work": "works", "adaptation": "adaptations", "author": "authors"}.get(required_subject)
            if table:
                require(table, relation.get("subject_id"), scope)
        source_ids = relation.get("source_ids") or []
        if not isinstance(source_ids, list) or not source_ids:
            errors.append(scope + ": toda relación necesita fuente propia")
        else:
            for source_id in source_ids:
                require("sources", source_id, scope)
        if relation.get("status") == APPROVED:
            require_approved("places", relation.get("place_id"), scope)
            if relation.get("subject_type") == required_subject:
                table = {"work": "works", "adaptation": "adaptations", "author": "authors"}.get(required_subject)
                if table:
                    require_approved(table, relation.get("subject_id"), scope)
            for source_id in (source_ids if isinstance(source_ids, list) else []):
                src = tables["sources"].get(source_id) if isinstance(source_id, str) else None
                if src is not None and not all(src.get(field) for field in ("url", "retrieved_at", "evidence_summary")):
                    errors.append(scope + ": fuente aprobada requiere URL, fecha y resumen de evidencia")
            if not relation.get("verified_at") or not relation.get("evidence_note"):
                errors.append(scope + ": aprobado exige fecha y evidencia")
            if typ == "popular_claim_unverified":
                errors.append(scope + ": mito no verificado nunca puede aprobarse")
    for image in tables["images"].values():
        scope = f"images/{image['id']}"
        require("places", image.get("place_id"), scope)
        if image.get("status") == APPROVED:
            if not all(image.get(k) for k in ("license", "license_url", "attribution", "source_url")):
                errors.append(scope + ": imagen aprobada sin derechos/atribución")
    for route in tables["routes"].values():
        scope = f"routes/{route['id']}"
        require("destinations", route.get("destination_id"), scope)
        stops = route.get("place_ids") or []
        if len(stops) != len(set(stops)):
            errors.append(scope + ": paradas duplicadas")
        for stop in stops:
            require("places", stop, scope)
            if route.get("status") == APPROVED:
                require_approved("places", stop, scope)
        if route.get("status") == APPROVED:
            require_approved("destinations", route.get("destination_id"), scope)
    for section in ("destinations", "places", "works", "authors", "adaptations", "routes"):
        for item in tables[section].values():
            if item.get("status") == APPROVED and not item.get("verified_at"):
                errors.append(f"{section}/{item['id']}: aprobación sin verified_at")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue", type=Path, help="JSON de trabajo, NO público")
    args = parser.parse_args()
    data = json.loads(args.catalogue.read_text(encoding="utf-8"))
    failures = problems(data)
    for failure in failures:
        print("ERROR: " + failure)
    print(f"Atlas integrity: {len(failures)} fallo(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
