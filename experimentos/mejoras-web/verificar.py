#!/usr/bin/env python3
"""Comprueba la coherencia mínima del catálogo; solo librería estándar."""
import json
from pathlib import Path

p = Path(__file__).with_name("catalogo.json")
data = json.loads(p.read_text(encoding="utf-8"))
assert data["schema_version"] == 1, "schema_version"
assert len(data["ideas"]) >= 50, "catalogo demasiado pequeno"
canales = {"auditoria_local", "github", "web", "api", "sector"}
familias = set()
ids = set()
for item in data["ideas"]:
    for key in ("id", "area", "titulo", "hipotesis", "superficie",
                "criterio_medicion", "antiduplicacion", "prioridad", "estado", "familia", "canal"):
        assert isinstance(item.get(key), str) and item[key].strip(), (item.get("id"), key)
    assert item["prioridad"] in ("P1", "P2", "P3"), item["id"]
    assert len(item["hipotesis"]) >= 25 and len(item["criterio_medicion"]) >= 20, item["id"]
    assert item["id"] not in ids, f"duplicado: {item['id']}"
    assert item["estado"] in data["estados_posibles"], item["id"]
    assert item["canal"] in canales, item["id"]
    assert item["familia"] == item["id"].split("-")[0], item["id"]
    familias.add(item["familia"])
    ids.add(item["id"])
assert len(familias) >= 20, "Variedad insuficiente"
assert {i["canal"] for i in data["ideas"]} == canales, "Canales incompletos"
print(f"OK: {len(ids)} hipotesis, {len(familias)} familias, {len(canales)} canales; NO prueba las hipotesis.")
