#!/usr/bin/env python3
"""Regresion (item "campos muertos en JSON" de la ronda 2026-09): los
campos `eligibility` y `submission_mode` de data/radar-opportunities.json
deben aparecer en la tarjeta HTML cuando existen.

Bug real encontrado: estos dos campos llevaban contenido editorial real
(requisitos de participacion, como presentar la obra) para 3 de las
convocatorias del dataset real, pero scripts/build-radar-opportunities.py
nunca los leia -- ni validate() ni card() los mencionaban. Un escritor
visitando /convocatorias-escritores/ veia el premio y la fecha limite, pero
tenia que salir al enlace de la fuente oficial para saber si podia
participar o como presentarse, aunque esa informacion ya estaba
investigada y escrita en el propio dataset.

Uso:
  python tests/test-radar-card-eligibility-fields.py
"""
from __future__ import annotations

import importlib.util
import io
import sys
from datetime import date
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("build_radar", ROOT / "scripts" / "build-radar-opportunities.py")
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)

failures: list[str] = []


def check(condition: bool, label: str) -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


base_item = {
    "id": "test-item", "title": "Premio de prueba", "type": "concurso",
    "organizer": "Entidad de prueba", "deadline": "2099-01-01",
    "genres": ["novela"], "source_url": "https://example.com/bases",
    "verified_at": "2026-01-01", "published": True, "fee_eur": None,
}

with_fields = {**base_item, "eligibility": "Solo personas mayores de edad.", "submission_mode": "Envio por correo postal."}
card_with = br.card(with_fields)
check("Quién puede participar" in card_with, "card() shows 'Quién puede participar' when eligibility is set")
check("Solo personas mayores de edad." in card_with, "card() includes the actual eligibility text")
check("Cómo presentarse" in card_with, "card() shows 'Cómo presentarse' when submission_mode is set")
check("Envio por correo postal." in card_with, "card() includes the actual submission_mode text")

card_without = br.card(base_item)
check("Quién puede participar" not in card_without, "card() omits the eligibility row entirely when absent (no empty <dd>)")
check("Cómo presentarse" not in card_without, "card() omits the submission_mode row entirely when absent (no empty <dd>)")

# The real dataset should still build without error with these fields active.
items = br.load_items(ROOT / "data" / "radar-opportunities.json")
html = br.build_html(items, date.fromisoformat("2026-08-22"))
real_with_eligibility = [i for i in items if i.get("eligibility")]
check(len(real_with_eligibility) > 0, "the real dataset has at least one item with eligibility (sanity check)")
for item in real_with_eligibility:
    if not item.get("published"):
        continue
    check(
        br.esc(item["eligibility"]) in html or item["deadline"] < "2026-08-22",
        f"{item['id']}: its eligibility text appears in the real generated HTML (or the item is already expired)",
    )

print(f"tests/test-radar-card-eligibility-fields: {'OK' if not failures else f'{len(failures)} FALLO(S)'}")
raise SystemExit(1 if failures else 0)
