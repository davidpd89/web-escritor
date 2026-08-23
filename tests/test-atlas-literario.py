#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("atlas_builder", ROOT / "scripts" / "build-atlas-literario.py")
atlas_builder = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = atlas_builder
_spec.loader.exec_module(atlas_builder)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def make_base_data(status: str = "planned") -> dict:
    return {
        "version": 1,
        "updated": "2026-08-22",
        "categories": [{"slug": "bibliotecas", "name": "Bibliotecas"}],
        "items": [
            {
                "status": status,
                "slug": "biblioteca-joanina-coimbra",
                "title": "Biblioteca Joanina",
                "category": "bibliotecas",
                "summary": "Resumen de prueba",
                "country": "Portugal",
                "relationship": "library",
                "certainty": "documented",
                "query_intent": ["biblioteca joanina"],
                "source_urls": ["https://visit.uc.pt/"],
                "verified_date": "2026-08-20" if status == "published" else "",
                "image": {
                    "src": "/assets/joanina.webp" if status == "published" else "",
                    "alt": "Interior de la biblioteca" if status == "published" else "",
                    "credit": "Autor" if status == "published" else "",
                    "license": "CC BY-SA" if status == "published" else "",
                    "source_url": "https://example.com/joanina" if status == "published" else "",
                },
            }
        ],
    }


print("tests/test-atlas-literario")

with tempfile.TemporaryDirectory() as tmp:
    tmp_path = Path(tmp)

    # 1) published sin credit/source/verified_date -> FAIL
    broken = make_base_data(status="published")
    broken["items"][0]["verified_date"] = ""
    broken["items"][0]["image"]["credit"] = ""
    broken_path = tmp_path / "broken.json"
    broken_path.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
    try:
        atlas_builder.load(broken_path)
        check(False, "1. published incompleto debe fallar")
    except ValueError as exc:
        check("verified_date" in str(exc) or "credit" in str(exc), "1. published incompleto -> FAIL", str(exc))

    # 2) planned no genera items publicables
    planned = make_base_data(status="planned")
    planned_path = tmp_path / "planned.json"
    planned_path.write_text(json.dumps(planned, ensure_ascii=False), encoding="utf-8")
    data, cats = atlas_builder.load(planned_path)
    out_dir = tmp_path / "dist"
    published_count = atlas_builder.build(data, cats, out_dir)
    public_json = json.loads((out_dir / "atlas-literario-public.json").read_text(encoding="utf-8"))
    index_html = (out_dir / "index.html").read_text(encoding="utf-8")
    check(published_count == 0, "2. planned -> 0 items publicados", str(published_count))
    check(public_json.get("items") == [], "2. atlas-literario-public.json queda sin items publicables")
    check("Aún no hay artículos publicados" in index_html, "2. index muestra placeholder en ausencia de publicados")

print("tests/test-atlas-literario: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
