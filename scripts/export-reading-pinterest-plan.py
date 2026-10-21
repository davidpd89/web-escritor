#!/usr/bin/env python3
"""Exporta el plan de pines al contrato MANUAL existente en RRSS_DavidPorto.

Se puede validar con:
  python C:/GIT/RRSS_DavidPorto/tools/pinterest_execute.py plan.json
Nunca publica ni usa navegador. El RSS nativo sigue siendo la vía principal.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build-reading-pinterest-rss.py"
spec = importlib.util.spec_from_file_location("reading_pinterest_feed", SCRIPT)
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)


def export(root: Path, today: date) -> list[dict]:
    config = feed.json_read(root / feed.CONFIG)
    data = feed.json_read(root / feed.CATALOG)
    state = feed.json_read(root / feed.STATE) if (root / feed.STATE).is_file() else {
        "schema_version": 1, "pins": {}
    }
    entries = feed.suitable_books(root, data, config, today, state=state)
    result = []
    for entry in entries:
        b, board = entry["book"], entry["board"]
        current = state["pins"].get(b["id"])
        if not current or current["board_slug"] != board["slug"]:
            continue
        if current["scheduled_date"] > today.isoformat():
            continue
        result.append({
            "kind": "manual_pin",
            "pin_title": feed.pin_title(b, board),
            "text": feed.pin_description(b, board),
            "media": [config["site"] + entry["image"]],
            "media_alt_text": [f"Portada auténtica del libro {b['titulo']}, de "
                               + ", ".join(b["autores"]) + "."],
            "board_name": board["name"],
            "pin_link": feed.target_url(config["site"], b["slug"], b["id"], board["slug"]),
            "motivo": "Ficha del catálogo; copia manual de respaldo, NO importar si ya existe el pin RSS."
        })
    return sorted(result, key=lambda x: (x["board_name"], x["pin_title"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--today", type=date.fromisoformat,
                        default=datetime.now(ZoneInfo("Europe/Madrid")).date())
    args = parser.parse_args()
    root = args.root.resolve()
    items = export(root, args.today)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"Exportadas {len(items)} fichas para preflight manual; no publicadas.")


if __name__ == "__main__":
    main()
