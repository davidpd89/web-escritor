"""Taxonomía de descubrimiento compartida por /editoriales/ y el radar de convocatorias.

Las fuentes declaran etiquetas literales (104 en editoriales, ~50 en el radar). Para que se pueda
buscar «fantasía» sin conocer toda la nomenclatura, ``data/genre-families.json`` agrupa esas
etiquetas en familias amplias. La etiqueta de la fuente nunca se reescribe: la familia solo
añade una coincidencia amplia que la página explica en cada ficha.
"""

from __future__ import annotations

import html
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES_PATH = ROOT / "data" / "genre-families.json"
FAMILY_PREFIX = "familia:"


def normalize(value: str) -> str:
    """Igual que ``normalize`` en el JS: minúsculas y sin tildes, conservando ñ y ü."""
    text = unicodedata.normalize("NFD", str(value).lower())
    text = "".join(ch for i, ch in enumerate(text) if not (unicodedata.combining(ch) and not (ch == "̃" and i and text[i - 1] == "n") and not (ch == "̈" and i and text[i - 1] == "u")))
    return unicodedata.normalize("NFC", text).strip()


def load_families(path: Path = FAMILIES_PATH) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    families = data["families"]
    seen: set[str] = set()
    for family in families:
        if not family.get("id") or family["id"] in seen or not family.get("label") or not family.get("tags"):
            raise ValueError(f"familia inválida o duplicada: {family!r}")
        seen.add(family["id"])
        if len({normalize(t) for t in family["tags"]}) != len(family["tags"]):
            raise ValueError(f"{family['id']}: etiquetas repetidas")
    return families


def tag_map(families: list[dict]) -> dict[str, list[str]]:
    """Etiqueta normalizada -> ids de familia, en el orden de la taxonomía."""
    mapping: dict[str, list[str]] = {}
    for family in families:
        for tag in family["tags"]:
            mapping.setdefault(normalize(tag), []).append(family["id"])
    return mapping


def families_for(tags: list[str], families: list[dict]) -> list[str]:
    mapping = tag_map(families)
    found = {fid for tag in tags for fid in mapping.get(normalize(tag), [])}
    return [f["id"] for f in families if f["id"] in found]


def genre_select_options(records_tags: list[list[str]], families: list[dict], exact_label=lambda t: t, counts: bool = True) -> str:
    """<optgroup> de familias (solo las que tienen fichas) seguido de las etiquetas exactas."""
    esc = lambda v: html.escape(str(v), quote=True)
    per_family = {f["id"]: 0 for f in families}
    for tags in records_tags:
        for fid in families_for(tags, families):
            per_family[fid] += 1
    family_opts = "".join(
        '<option value="{}{}">{}{}</option>'.format(FAMILY_PREFIX, esc(f["id"]), esc(f["label"]), f" ({per_family[f['id']]})" if counts else "")
        for f in families if per_family[f["id"]]
    )
    exact = sorted({t for tags in records_tags for t in tags}, key=lambda t: normalize(t))
    exact_opts = "".join(f'<option value="{esc(t)}">{esc(exact_label(t))}</option>' for t in exact)
    return f'<optgroup label="Familias (coincidencia amplia)">{family_opts}</optgroup><optgroup label="Etiqueta exacta de la fuente">{exact_opts}</optgroup>'


def families_json(families: list[dict]) -> str:
    """Mapa para el cliente; se incrusta en <script type="application/json" data-genre-families>."""
    payload = {
        "labels": {f["id"]: f["label"] for f in families},
        "tags": tag_map(families),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
