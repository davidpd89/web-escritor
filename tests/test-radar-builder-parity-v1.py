#!/usr/bin/env python3
"""Comprueba que el builder de Convocatorias genera shell V1 y salida sincronizada."""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "radar-opportunities.json"

_spec = importlib.util.spec_from_file_location(
    "build_radar", ROOT / "scripts" / "build-radar-opportunities.py"
)
br = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(br)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


print("tests/test-radar-builder-parity-v1")

raw = json.loads(DATA.read_text(encoding="utf-8"))
items = br.load_items(DATA)
watchlist = br.load_watchlist(DATA)
br.ensure_disjoint_ids(items, watchlist)
if watchlist:
    collision = [dict(item) for item in watchlist]
    collision[0]["id"] = items[0]["id"]
    try:
        br.ensure_disjoint_ids(items, collision)
    except ValueError as exc:
        check("ids repetidos entre items y watchlist" in str(exc), "ids duplicados entre radar y watchlist se rechazan")
    else:
        check(False, "ids duplicados entre radar y watchlist se rechazan", "no se lanzó ValueError")
committed_json_raw = json.loads((ROOT / "convocatorias-escritores/opportunities.json").read_text(encoding="utf-8"))
# The committed public artifact owns the test clock; a missing generated_for is a contract failure.
target_date = date.fromisoformat(committed_json_raw["generated_for"])

with tempfile.TemporaryDirectory() as tmp_dir:
    tmp = Path(tmp_dir)
    tmp.mkdir(parents=True, exist_ok=True)

    generated_html = br.build_html(items, target_date, watchlist)
    generated_json = br.public_json(items, target_date, watchlist)
    generated_ics = br.build_ics(items, target_date)

    check(generated_html == (ROOT / "convocatorias-escritores/index.html").read_text(encoding="utf-8"), "convocatorias-escritores/index.html está sincronizado")
    check(generated_json == (ROOT / "convocatorias-escritores/opportunities.json").read_text(encoding="utf-8"), "convocatorias-escritores/opportunities.json está sincronizado")
    expected_ics = (ROOT / "convocatorias-escritores/deadlines.ics").read_text(encoding="utf-8")
    normalized_generated_ics = generated_ics.replace("\r\n", "\n")
    normalized_expected_ics = expected_ics.replace("\r\n", "\n")
    check(normalized_generated_ics == normalized_expected_ics, "convocatorias-escritores/deadlines.ics está sincronizado")

    check('class="v1"' in generated_html, "el HTML generado mantiene shell V1")
    check("/assets/v1-shell.css?v=4" in generated_html, "el HTML generado carga CSS V1")
    check("/styles.css?v=202609-launch-1" not in generated_html, "el HTML generado no vuelve al CSS legacy")

print("tests/test-radar-builder-parity-v1: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
