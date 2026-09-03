#!/usr/bin/env python3
"""Comprueba que el builder de Editoriales genera exactamente el output V1."""
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
DATA = ROOT / "data" / "editoriales.json"

_spec = importlib.util.spec_from_file_location(
    "build_editoriales", ROOT / "scripts" / "build-editoriales.py"
)
be = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(be)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


print("tests/test-editoriales-builder-parity-v1")

raw = json.loads(DATA.read_text(encoding="utf-8"))
published = [r for r in raw["publishers"] if r.get("publish") is True]
expected_paths = [
    Path("editoriales/index.html"),
    Path("editoriales/editoriales-data.json"),
    Path("editoriales-sitemap.xml"),
    Path(f"{be.METHODOLOGY_SLUG}/index.html"),
]
expected_paths.extend(Path(f"editoriales/{record['slug']}/index.html") for record in published)

with tempfile.TemporaryDirectory() as tmp_dir:
    tmp = Path(tmp_dir)
    be.build(DATA, tmp, date.fromisoformat("2026-08-22"), False)

    for rel in expected_paths:
        generated = (tmp / rel).read_text(encoding="utf-8")
        committed = (ROOT / rel).read_text(encoding="utf-8")
        check(generated == committed, f"{rel.as_posix()} está sincronizado con el builder")

    generated_index = (tmp / "editoriales/index.html").read_text(encoding="utf-8")
    check('class="v1"' in generated_index, "el índice generado mantiene shell V1")
    check("/assets/v1-shell.css?v=2" in generated_index, "el índice generado carga CSS V1")
    check("/styles.css?v=202609-launch-1" not in generated_index, "el índice generado no vuelve al CSS legacy")

print("tests/test-editoriales-builder-parity-v1: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
