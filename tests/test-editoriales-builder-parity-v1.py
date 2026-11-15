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
    # El HTML publicado lleva los avisos de caducidad (>90 días) del día real
    # del sitio, igual que exige check-professional-resources. Con
    # max(verified_at) ambas pruebas se contradecían (10/11).
    # Ventana de reloj (site_clock.clock_window): una PR no queda roja porque
    # hoy una ficha cruzó los 90 días; eso lo arregla radar-clock-refresh, que
    # comprueba con RELOJ_ESTRICTO=1.
    sys.path.insert(0, str(ROOT / "scripts"))
    from site_clock import clock_window

    def drift(day: date, out: Path) -> list[str]:
        be.build(DATA, out, day, False)
        return [rel.as_posix() for rel in expected_paths
                if (out / rel).read_text(encoding="utf-8") != (ROOT / rel).read_text(encoding="utf-8")]

    window = clock_window()
    target_date = window[0]
    differing = drift(target_date, tmp)
    for older in window[1:]:
        if not differing:
            break
        with tempfile.TemporaryDirectory() as older_dir:
            if not drift(older, Path(older_dir)):
                print(f"  aviso: generados del {older}, no de hoy ({target_date}); los pondrá al día radar-clock-refresh")
                differing = []
    for rel in expected_paths:
        check(rel.as_posix() not in differing, f"{rel.as_posix()} está sincronizado con el builder")

    # Una fecha de ejecución distinta no debe alterar los archivos si
    # ninguna ficha cruza el umbral de caducidad entre ambas fechas.
    next_date = date.fromordinal(target_date.toordinal() + 1)
    crosses = [r["slug"] for r in published if be.stale(r, target_date) != be.stale(r, next_date)]
    if crosses:
        print(f"  skip determinismo: {', '.join(crosses)} cruza el umbral de 90 días mañana")
    else:
        with tempfile.TemporaryDirectory() as other_dir:
            other = Path(other_dir)
            be.build(DATA, other, next_date, False)
            for rel in expected_paths:
                first_output = (tmp / rel).read_bytes()
                second_output = (other / rel).read_bytes()
                check(
                    first_output == second_output,
                    f"{rel.as_posix()} es determinista entre dos fechas de ejecución",
                )

    generated_index = (tmp / "editoriales/index.html").read_text(encoding="utf-8")
    check('class="v1"' in generated_index, "el índice generado mantiene shell V1")
    check("/assets/v1-shell.css?v=21" in generated_index, "el índice generado carga CSS V1")
    check("/styles.css?v=202609-launch-1" not in generated_index, "el índice generado no vuelve al CSS legacy")

print("tests/test-editoriales-builder-parity-v1: " + ("OK" if not failures else f"{len(failures)} FALLO(S)"))
raise SystemExit(1 if failures else 0)
