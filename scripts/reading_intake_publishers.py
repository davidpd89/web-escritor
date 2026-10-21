"""Construye sellos de búsqueda a partir del registro editorial existente.

data/editoriales.json es autoridad sobre slugs/nombres, NO un feed de novedades.
No interpreta "status=closed" (recepción de manuscritos) como sello inactivo.
Sin red ni costes; la relación ISBN→sello sigue pendiente de validación.
"""
from __future__ import annotations

import re
import unicodedata

_NON_TRADITIONAL = ("autoedicion", "autopublic", "servicios editoriales",
                    "modelo editorial por verificar", "coedicion")


def _key(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value).casefold())
    simple = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", simple).strip()


def relevant_publisher(record: dict) -> bool:
    if not record.get("publish") or not record.get("name") or not record.get("slug"):
        return False
    model = _key(record.get("publisher_type", ""))
    if not (model == "tradicional" or model == "independiente"):
        return False
    if any(block in model for block in _NON_TRADITIONAL):
        return False
    return True  # All subject areas are eligible; the source validates each edition.


def resolve_publishers(editoriales: dict, overrides: list[dict] | None = None,
                       *, max_publishers: int | None = None) -> list[dict]:
    """Return canonical publisher slugs with optional manually supplied aliases.

    Overridden entries always use the canonical site's slug from editoriales.
    Unknown override names are NOT allowed to create new publisher pages.
    """
    overrides = overrides or []
    indexed_by_slug = {record.get("slug"): record for record in overrides
                       if record.get("slug")}
    indexed_by_name = {_key(record.get("name", "")): record for record in overrides
                       if record.get("name")}
    result = []
    for record in editoriales.get("publishers", []):
        if not relevant_publisher(record):
            continue
        override = indexed_by_slug.get(record["slug"]) or indexed_by_name.get(_key(record["name"])) or {}
        if override.get("enabled") is False:
            continue
        # The books API sometimes omits "Editorial"/"Ediciones" prefixes:
        # "Hidra" and "Editorial Hidra" denote the same canonical site slug.
        short_name = re.sub(r"^(?:Editorial|Ediciones)\s+", "",
                            record["name"], flags=re.IGNORECASE)
        aliases = list(dict.fromkeys([
            record["name"],
            short_name,
            *(override.get("aliases") or []),
            *([override["name"]] if override.get("name") else [])
        ]))
        result.append({
            "slug": record["slug"],
            "name": record["name"],
            "aliases": aliases,
            "group": record.get("group", ""),
            "genres": record.get("genres", []),
            "enabled": True,
        })
    # Sort by slug; a separately configured rotation cursor can paginate fairly.
    result.sort(key=lambda p: p["slug"])
    if max_publishers is not None:
        return result[:max_publishers]
    return result
