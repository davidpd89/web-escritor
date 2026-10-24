#!/usr/bin/env python3
"""Comprueba la coherencia mínima del catálogo; solo librería estándar."""
import json
from pathlib import Path

p = Path(__file__).with_name("catalogo.json")
data = json.loads(p.read_text(encoding="utf-8"))
assert data["schema_version"] == 1, "schema_version"
assert len(data["ideas"]) >= 8, "catalogo demasiado pequeno"
ids = set()
for item in data["ideas"]:
    for key in ("id", "area", "titulo", "hipotesis", "superficie",
                "criterio_medicion", "antiduplicacion", "prioridad", "estado"):
        assert isinstance(item.get(key), str) and len(item[key].strip()) >= 4, (item.get("id"), key)
    assert item["id"] not in ids, f"duplicado: {item['id']}"
    assert item["estado"] in data["estados_posibles"], item["id"]
    ids.add(item["id"])
print(f"OK: {len(ids)} hipotesis, IDs unicos y contratos completos; NO prueba las hipotesis.")
