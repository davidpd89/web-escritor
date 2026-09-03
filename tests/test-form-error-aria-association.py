#!/usr/bin/env python3
"""Regresion (item 41 de la ronda 2026-09): un campo cuyo error se
comunica via JS (aria-invalid toggled + un mensaje de error escrito en
otro elemento) debe llevar aria-describedby apuntando al id real de ese
elemento, para que un lector de pantalla anuncie el porque, no solo que
el campo es invalido.

Bugs reales encontrados:
1. herramientas/personajes/index.html: los <select> #relation-from y
   #relation-to reciben aria-invalid desde setRelationError() en
   assets/mapa-personajes.js, pero no llevaban aria-describedby hacia
   #relation-error -- a diferencia de #character-name, que si estaba
   correctamente enlazado a #character-error.
2. herramientas/distribucion-pov/index.html: el parrafo de estado
   (data-pov-status) no llevaba ni siquiera un id, asi que ningun
   aria-describedby podia apuntar a el; los dos textarea (#pov-input,
   #pov-input-totals) solo enlazaban su hint de formato, nunca el estado
   de error real que assets/pov-distribucion.js escribe ahi.

Uso:
  python tests/test-form-error-aria-association.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
failures: list[str] = []


def check(condition: bool, label: str) -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


personajes = (ROOT / "herramientas" / "personajes" / "index.html").read_text(encoding="utf-8")
check(
    'id="relation-from" class="tool-select" aria-describedby="relation-error"' in personajes,
    "personajes: #relation-from is describedby relation-error",
)
check(
    'id="relation-to" class="tool-select" aria-describedby="relation-error"' in personajes,
    "personajes: #relation-to is describedby relation-error",
)
check(
    'aria-describedby="character-error"' in personajes,
    "personajes: #character-name is (still) describedby character-error",
)

pov = (ROOT / "herramientas" / "distribucion-pov" / "index.html").read_text(encoding="utf-8")
check('id="pov-status"' in pov, "distribucion-pov: the status paragraph has a real id")
check(
    'id="pov-input" class="tool-textarea" data-pov-input aria-describedby="pov-format pov-status"' in pov,
    "distribucion-pov: #pov-input is describedby its format hint AND pov-status",
)
check(
    'id="pov-input-totals" class="tool-textarea" data-pov-input-totals aria-describedby="pov-format-totals pov-status"' in pov,
    "distribucion-pov: #pov-input-totals is describedby its format hint AND pov-status",
)

print(f"tests/test-form-error-aria-association: {'OK' if not failures else f'{len(failures)} FALLO(S)'}")
raise SystemExit(1 if failures else 0)
