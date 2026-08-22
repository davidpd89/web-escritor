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

with tempfile.TemporaryDirectory() as tmp_dir:
    tmp = Path(tmp_dir)
    tmp.mkdir(parents=True, exist_ok=True)

    generated_html = br.build_html(items, date.fromisoformat("2026-08-22"))
    generated_json = br.public_json(items, date.fromisoformat("2026-08-22"))
    generated_ics = br.build_ics(items, date.fromisoformat("2026-08-22"))

    check(generated_html == (ROOT / "convocatorias-escritores/index.html").read_text(encoding="utf-8"), "convocatorias-escritores/index.html está sincronizado")
    check(generated_json == (ROOT / "convocatorias-escritores/opportunities.json").read_text(encoding="utf-8"), "convocatorias-escritores/opportunities.json está sincronizado")
    expected_ics = (ROOT / "convocatorias-escritores/deadlines.ics").read_text(encoding="utf-8")
    normalized_generated_ics = generated_ics.replace("\r\n", "\n")
    normalized_expected_ics = expected_ics.replace("\r\n", "\n")
    check(normalized_generated_ics == normalized_expected_ics, "convocatorias-escritores/deadlines.ics está sincronizado")

    check('class="v1"' in generated_html, "el HTML generado mantiene shell V1")
    check("/assets/v1-shell.css" in generated_html, "el HTML generado carga CSS V1")
    check("/styles.css?v=202609-launch-1" not in generated_html, "el HTML generado no vuelve al CSS legacy")

print("tests/test-radar-builder-parity-v1: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
