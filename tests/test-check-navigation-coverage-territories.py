#!/usr/bin/env python3
"""Verifica la regla de los 5 territorios estables de Explorar en
scripts/check-navigation-coverage.py (M.1, 2026-08-23).

No reimplementa todo el checker: ejecuta el script real como subproceso
contra copias temporales de data/navigation.json con variaciones
deliberadas, dejando intactos content-registry.json/sitemap.xml/
tools-hub.json reales del repo (los únicos que cambian son las 5
entradas de exploreTerritories, que ya resuelven a IDs públicos
reales).

Uso:
  python tests/test-check-navigation-coverage-territories.py
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check-navigation-coverage.py"
NAV_PATH = ROOT / "data" / "navigation.json"

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def run_with_nav(nav: dict) -> str:
    """Sustituye temporalmente el navigation.json REAL y ejecuta el
    checker REAL desde su ubicacion real (sourceFile de cada entrada del
    registry apunta a rutas relativas a la raiz del repo real; copiar solo
    un subconjunto de ficheros a un directorio temporal rompe esas
    comprobaciones sin relacion con lo que este test quiere verificar).
    Siempre restaura el fichero original, incluso si el checker falla.
    """
    original = NAV_PATH.read_text(encoding="utf-8")
    try:
        NAV_PATH.write_text(json.dumps(nav), encoding="utf-8")
        result = subprocess.run([sys.executable, str(CHECKER)], cwd=ROOT, capture_output=True, text=True)
        return result.stdout
    finally:
        NAV_PATH.write_text(original, encoding="utf-8")


def load_real_nav() -> dict:
    return json.loads(NAV_PATH.read_text(encoding="utf-8"))


def run() -> None:
    real_nav = load_real_nav()

    # Negativo: navigation.json real (ya con los 5 territorios) -> PASS.
    out = run_with_nav(real_nav)
    check(out.startswith("PASS"), "navigation.json real con los 5 territorios estables pasa", out)

    # Positivo: se reintroduce work-manecillas como territorio -> se detecta.
    bad_nav = json.loads(json.dumps(real_nav))
    bad_nav["exploreTerritories"] = [{"id": "work-manecillas", "previewId": "work-manecillas"}] + bad_nav["exploreTerritories"][1:]
    out = run_with_nav(bad_nav)
    check("reintroduces individual works" in out, "reintroducir work-manecillas como territorio se detecta", out)

    # Positivo: se reintroduce work-samuel como territorio -> se detecta.
    bad_nav2 = json.loads(json.dumps(real_nav))
    bad_nav2["exploreTerritories"].append({"id": "work-samuel", "previewId": "work-samuel"})
    out = run_with_nav(bad_nav2)
    check("reintroduces individual works" in out, "reintroducir work-samuel como territorio se detecta", out)

    # Positivo: menos de 5 territorios -> se detecta.
    short_nav = json.loads(json.dumps(real_nav))
    short_nav["exploreTerritories"] = short_nav["exploreTerritories"][:3]
    out = run_with_nav(short_nav)
    check("must be exactly the 5 stable territories" in out, "menos de 5 territorios se detecta", out)

    # Positivo: orden distinto -> se detecta (el contrato exige orden exacto).
    reordered_nav = json.loads(json.dumps(real_nav))
    reordered_nav["exploreTerritories"] = list(reversed(reordered_nav["exploreTerritories"]))
    out = run_with_nav(reordered_nav)
    check("must be exactly the 5 stable territories" in out, "orden distinto de los 5 territorios se detecta", out)

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-navigation-coverage-territories: OK")


if __name__ == "__main__":
    run()
