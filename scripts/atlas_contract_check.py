#!/usr/bin/env python3
"""Offline referential-integrity gate for the future worldwide literary atlas.

This is a supplementary check, not a full JSON Schema implementation. No network,
web publication, Actions, model calls, or writes. Input is internal draft JSON.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

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
def valid_https_url(url: object) -> bool:
    """Reusable strict-ish source URL gate aligned with reading catalogue."""
    if not isinstance(url, str) or re.search(r"[\s<>\x00-\x1f]", url):
        return False
    try:
        parsed = urlsplit(url)
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and not parsed.username and not parsed.password
                and parsed.port in (None, 443))
    except ValueError:
        return False


def valid_date(value: object) -> bool:
    """Real ISO calendar date (YYYY-MM-DD); the schema regex alone accepts 2026-13-45."""
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


APPROVED = "approved"
COLLECTIONS = ("destinations", "places", "works", "authors", "adaptations",
               "sources", "relationships", "images", "routes")


def problems(data: dict) -> list[str]:
    errors: list[str] = []
    if (not isinstance(data, dict) or data.get("schema_version") != 1
            or isinstance(data.get("schema_version"), bool)):
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

    for category in ("destinations", "places", "routes"):
        seen: dict[str, str] = {}
        for entry in tables[category].values():
            slug = entry.get("slug")
            if isinstance(slug, str):
                if slug in seen:
                    errors.append(f"{category}: slug duplicado {slug!r} en {seen[slug]} y {entry['id']}")
                else:
                    seen[slug] = entry["id"]

    def require(category: str, key: object, scope: str) -> None:
        if not isinstance(key, str) or key not in tables[category]:
            errors.append(f"{scope}: referencia {category}={key!r} no existe")

    def require_approved(category: str, key: object, scope: str) -> None:
        entry = tables[category].get(key) if isinstance(key, str) else None
        if entry is not None and entry.get("status") != APPROVED:
            errors.append(f"{scope}: {category}={key!r} no aprobado")

    def id_list(value: object, scope: str, field: str) -> list[str]:
        if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
            errors.append(f"{scope}: {field} debe ser lista de IDs")
            return []
        return value

    def check_source_evidence(source_id: str, scope: str, verified_at: object = None) -> None:
        src = tables["sources"].get(source_id)
        if src is None:
            return  # require() ya informa de referencia inexistente
        if not all(has_text(src.get(k)) for k in ("url", "title", "retrieved_at", "evidence_summary")):
            errors.append(f"{scope}: fuente {source_id!r} requiere URL, título, fecha y evidencia")
        elif not valid_date(src["retrieved_at"]):
            errors.append(f"{scope}: fuente {source_id!r} tiene retrieved_at que no es una fecha real")
        elif not valid_https_url(src["url"]):
            errors.append(f"{scope}: fuente {source_id!r} requiere URL HTTPS")
        if valid_date(verified_at) and valid_date(src.get("retrieved_at")):
            if date.fromisoformat(verified_at) < date.fromisoformat(src["retrieved_at"]):
                errors.append(
                    f"{scope}: verified_at anterior a retrieved_at de la fuente {source_id!r}"
                )

    # Los controles bidi no son válidos en nombres ni títulos públicos.
    bidi_controls = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))
    public_labels = {
        "destinations": "name",
        "places": "name",
        "works": "title",
        "authors": "name",
        "routes": "title",
    }
    for category, field in public_labels.items():
        for entry in tables[category].values():
            value = entry.get(field)
            if not isinstance(value, str):
                continue
            for char in value:
                if ord(char) in bidi_controls:
                    errors.append(
                        f"{category}/{entry['id']}: {field} contiene "
                        f"control bidireccional U+{ord(char):04X}"
                    )
                    break

    for dest in tables["destinations"].values():
        parent = dest.get("parent_id")
        if parent is not None:
            require("destinations", parent, f"destinations/{dest['id']}")
            if parent == dest["id"]:
                errors.append(f"destinations/{dest['id']}: parent_id no puede ser el propio destino")

    seen_osm: dict[tuple[str, int], str] = {}
    # Cada cadena de destinos debe terminar en una raíz, nunca en un ciclo.
    destinations = tables["destinations"]
    resolved: set[str] = set()
    for destination_id in destinations:
        if destination_id in resolved:
            continue
        seen: set[str] = set()
        current = destination_id
        while current in destinations and current not in resolved:
            if current in seen:
                errors.append(
                    f"destinations/{current}: ciclo detectado en parent_id"
                )
                break
            seen.add(current)
            parent = destinations[current].get("parent_id")
            if not isinstance(parent, str):
                break
            current = parent
        resolved.update(seen)

    for place in tables["places"].values():
        scope = f"places/{place['id']}"
        osm_type, osm_id = place.get("osm_type"), place.get("osm_id")
        if isinstance(osm_type, str) and isinstance(osm_id, int) and not isinstance(osm_id, bool):
            osm_key = (osm_type, osm_id)
            if osm_key in seen_osm:
                errors.append(
                    f"{scope}: objeto OSM duplicado {osm_type}/{osm_id} "
                    f"en {seen_osm[osm_key]} y {place['id']}"
                )
            else:
                seen_osm[osm_key] = place["id"]
        require("destinations", place.get("destination_id"), scope)
        if "overture_confidence" in place:
            confidence = place["overture_confidence"]
            if (not isinstance(confidence, (int, float))
                    or isinstance(confidence, bool)
                    or not math.isfinite(confidence)
                    or not 0 <= confidence <= 1):
                errors.append(scope + ": overture_confidence debe ser un número finito entre 0 y 1")
        lat, lon = place.get("latitude"), place.get("longitude")
        if (lat is None) != (lon is None):
            errors.append(scope + ": latitude y longitude deben aparecer juntas")
        if lat is not None and (not isinstance(lat, (int, float)) or isinstance(lat, bool)
                                or not -90 <= lat <= 90):
            errors.append(scope + ": latitude fuera de rango")
        if lon is not None and (not isinstance(lon, (int, float)) or isinstance(lon, bool)
                                or not -180 <= lon <= 180):
            errors.append(scope + ": longitude fuera de rango")
        if place.get("geo_precision") == "unlocated" and (lat is not None or lon is not None):
            errors.append(scope + ": unlocated no admite coordenadas")
        if place.get("geo_precision") in ("point", "building") and (lat is None or lon is None):
            errors.append(scope + ": point/building requiere coordenadas")
        if place.get("status") == APPROVED:
            if not has_text(place.get("summary_original")) or not place.get("source_ids"):
                errors.append(scope + ": aprobado requiere texto original y fuente")
            require_approved("destinations", place.get("destination_id"), scope)
        for image_id in id_list(place.get("image_ids", []), scope, "image_ids"):
            require("images", image_id, scope)
            image = tables["images"].get(image_id)
            if image is not None and image.get("place_id") != place["id"]:
                errors.append(f"{scope}: image_ids={image_id!r} pertenece a otro lugar")
        for source_id in id_list(place.get("source_ids", []), scope, "source_ids"):
            require("sources", source_id, scope)
            if place.get("status") == APPROVED:
                check_source_evidence(source_id, scope, place.get("verified_at"))
        if bool(place.get("osm_id")) != bool(place.get("osm_type")):
            errors.append(scope + ": osm_id y osm_type deben aparecer juntos")

    for work in tables["works"].values():
        for author_id in id_list(work.get("author_ids", []), f"works/{work['id']}", "author_ids"):
            require("authors", author_id, f"works/{work['id']}")
            if work.get("status") == APPROVED:
                require_approved("authors", author_id, f"works/{work['id']}")
    for adaptation in tables["adaptations"].values():
        require("works", adaptation.get("original_work_id"), f"adaptations/{adaptation['id']}")
        if adaptation.get("status") == APPROVED:
            require_approved("works", adaptation.get("original_work_id"), f"adaptations/{adaptation['id']}")
    seen_relationships: dict[tuple, str] = {}
    for relation in tables["relationships"].values():
        scope = f"relationships/{relation['id']}"
        if relation.get("status") == APPROVED:
            raw_sources = relation.get("source_ids")
            if isinstance(raw_sources, list) and all(isinstance(source, str) for source in raw_sources):
                semantic_key = (
                    relation.get("place_id"),
                    relation.get("subject_type"),
                    relation.get("subject_id"),
                    relation.get("relationship_type"),
                    frozenset(raw_sources),
                    relation.get("evidence_note"),
                )
                if all(isinstance(value, str) for value in semantic_key[:4]) and isinstance(semantic_key[5], str):
                    previous_id = seen_relationships.get(semantic_key)
                    if previous_id is not None:
                        errors.append(
                            f"{scope}: relación semántica duplicada de relationships/{previous_id}"
                        )
                    else:
                        seen_relationships[semantic_key] = relation["id"]
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
        source_ids = id_list(relation.get("source_ids"), scope, "source_ids")
        if not source_ids:
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
            for source_id in source_ids:
                check_source_evidence(source_id, scope, relation.get("verified_at"))
            if not valid_date(relation.get("verified_at")) or not has_text(relation.get("evidence_note")):
                errors.append(scope + ": aprobado exige fecha y evidencia")
            if typ == "popular_claim_unverified":
                errors.append(scope + ": mito no verificado nunca puede aprobarse")
    for image in tables["images"].values():
        scope = f"images/{image['id']}"
        require("places", image.get("place_id"), scope)
        if image.get("status") == APPROVED:
            require_approved("places", image.get("place_id"), scope)
            place_id = image.get("place_id")
            owner = tables["places"].get(place_id) if isinstance(place_id, str) else None
            if owner is not None:
                image_ids = owner.get("image_ids")
                if not isinstance(image_ids, list) or image["id"] not in image_ids:
                    errors.append(
                        f"{scope}: imagen aprobada sin vínculo inverso en "
                        f"places/{place_id}.image_ids"
                    )
            if not all(has_text(image.get(k)) for k in ("license", "license_url", "attribution", "source_url")):
                errors.append(scope + ": imagen aprobada sin derechos/atribución")
            elif not (valid_https_url(image["source_url"]) and valid_https_url(image["license_url"])):
                errors.append(scope + ": imagen aprobada requiere URLs HTTPS válidas")
    for route in tables["routes"].values():
        scope = f"routes/{route['id']}"
        require("destinations", route.get("destination_id"), scope)
        stops = id_list(route.get("place_ids"), scope, "place_ids")
        if len(stops) != len(set(stops)):
            errors.append(scope + ": paradas duplicadas")
        for stop in stops:
            require("places", stop, scope)
            stop_place = tables["places"].get(stop)
            if stop_place is not None and stop_place.get("destination_id") != route.get("destination_id"):
                errors.append(f"{scope}: parada {stop!r} pertenece a otro destino")
            if route.get("status") == APPROVED:
                require_approved("places", stop, scope)
                if stop_place is not None and stop_place.get("geo_precision") == "unlocated":
                    errors.append(f"{scope}: parada {stop!r} sin localización geográfica utilizable (unlocated)")
        if route.get("status") == APPROVED:
            require_approved("destinations", route.get("destination_id"), scope)
    public_labels = {
        "destinations": "name",
        "places": "name",
        "works": "title",
        "authors": "name",
        "adaptations": "title",
        "routes": "title",
    }
    for section, field in public_labels.items():
        for item in tables[section].values():
            if item.get("status") != APPROVED:
                continue
            if not has_text(item.get(field)):
                errors.append(f"{section}/{item['id']}: {field} requiere texto visible")
            if not item.get("verified_at"):
                errors.append(f"{section}/{item['id']}: aprobación sin verified_at")
            elif not valid_date(item["verified_at"]):
                errors.append(f"{section}/{item['id']}: verified_at no es una fecha real")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue", type=Path, help="JSON de trabajo, NO público")
    args = parser.parse_args()
    try:
        data = json.loads(args.catalogue.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"ERROR: no se puede leer el JSON: {exc}")
        return 2
    failures = problems(data)
    for failure in failures:
        print("ERROR: " + failure)
    print(f"Atlas integrity: {len(failures)} fallo(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
