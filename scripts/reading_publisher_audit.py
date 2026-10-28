#!/usr/bin/env python3
"""Informe de sellos bloqueados por la ingesta (solo lectura, sin aceptar ISBN).

Ejemplo: python scripts/reading_publisher_audit.py
"""
from __future__ import annotations

import json
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from reading_intake_core import normalize_text
from reading_intake_publishers import resolve_publishers

ROOT = Path(__file__).resolve().parents[1]
BLOCK_REASON = "Sello no presente en el registro editorial de la web"


def publisher_audit(state, editorial_registry, config):
    """Aggregate blocked ISBNs and rank hints against existing canonical slugs.

    Hints are *not* verified alias mappings and must never change the intake.
    """
    sources = resolve_publishers(editorial_registry, config.get("publisher_aliases", []))
    groups = defaultdict(lambda: {"isbns": set(), "titulos": set()})
    for entry in state.get("items", {}).values():
        if entry.get("estado_ingesta") != "pendiente_datos" or entry.get("motivo") != BLOCK_REASON:
            continue
        data = entry.get("datos") or {}
        name, isbn = data.get("editorial"), entry.get("isbn13")
        if not isinstance(name, str) or not name.strip() or not isinstance(isbn, str):
            continue
        key = " ".join(name.split())
        groups[key]["isbns"].add(isbn)
        if data.get("titulo"):
            groups[key]["titulos"].add(data["titulo"])

    results = []
    for name, group in sorted(groups.items(), key=lambda p: (-len(p[1]["isbns"]), p[0].casefold())):
        wanted = normalize_text(name)
        candidates = []
        for source in sources:
            labels = [source["name"], *source["aliases"]]
            affinity = max(
                (SequenceMatcher(None, wanted, normalize_text(label)).ratio() for label in labels),
                default=0.0,
            )
            if affinity >= 0.68:
                candidates.append({"slug": source["slug"], "nombre": source["name"], "similitud": round(affinity, 3)})
        candidates.sort(key=lambda x: (-x["similitud"], x["slug"]))
        results.append({
            "sello_detectado": name,
            "isbn_bloqueados": len(group["isbns"]),
            "isbn_ejemplo": sorted(group["isbns"])[:3],
            "candidatos_para_revision_manual": candidates[:3],
            "decision": "pendiente_revision_humana",
        })
    return {
        "sellos_pendientes": len(results),
        "isbn_bloqueados": sum(r["isbn_bloqueados"] for r in results),
        "grupos": results,
        "nota": "Las sugerencias por similitud no validan una identidad editorial; ningún ISBN se publica ni se cambia la configuración.",
    }


def main():
    state = json.loads((ROOT / "data/reading-intake-state.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "data/editoriales.json").read_text(encoding="utf-8"))
    config = json.loads((ROOT / "data/reading-intake-config.json").read_text(encoding="utf-8"))
    print(json.dumps(publisher_audit(state, registry, config), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
