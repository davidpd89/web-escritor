#!/usr/bin/env python3
"""Regression tests for the five-territory + Obras findability contract.

The contract is deliberately stronger than «five strings in Explore»: the two
published works must remain canonical, indexable children of works-hub, linked
from the Obras hub itself and directly available from the global Obra footer.
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
REGISTRY_PATH = ROOT / "data" / "content-registry.json"
WORKS_PATH = ROOT / "libros" / "index.html"

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def run_with_state(
    *,
    nav: dict | None = None,
    registry: dict | None = None,
    works_html: str | None = None,
) -> tuple[int, str]:
    originals = {
        NAV_PATH: NAV_PATH.read_text(encoding="utf-8"),
        REGISTRY_PATH: REGISTRY_PATH.read_text(encoding="utf-8"),
        WORKS_PATH: WORKS_PATH.read_text(encoding="utf-8"),
    }
    try:
        if nav is not None:
            NAV_PATH.write_text(json.dumps(nav, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if registry is not None:
            REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if works_html is not None:
            WORKS_PATH.write_text(works_html, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(CHECKER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout + result.stderr
    finally:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def registry_entry(registry: dict, item_id: str) -> dict:
    return next(item for item in registry["entries"] if item.get("id") == item_id)


def run() -> None:
    real_nav = load_json(NAV_PATH)
    real_registry = load_json(REGISTRY_PATH)
    real_works = WORKS_PATH.read_text(encoding="utf-8")

    code, out = run_with_state()
    check(code == 0 and out.startswith("PASS"), "estado real cumple 5 territorios + findability de ambas obras", out)

    bad_top_level = json.loads(json.dumps(real_nav))
    bad_top_level["exploreTerritories"] = [
        {"id": "work-manecillas", "previewId": "work-manecillas"},
        *bad_top_level["exploreTerritories"][1:],
    ]
    code, out = run_with_state(nav=bad_top_level)
    check(
        code != 0 and "individual works as top-level territories" in out,
        "reintroducir Manecillas como territorio top-level falla",
        out,
    )

    short_nav = json.loads(json.dumps(real_nav))
    short_nav["exploreTerritories"] = short_nav["exploreTerritories"][:4]
    code, out = run_with_state(nav=short_nav)
    check(code != 0 and "exactly the 5 stable territories" in out, "menos de cinco territorios falla", out)

    reordered_nav = json.loads(json.dumps(real_nav))
    reordered_nav["exploreTerritories"] = list(reversed(reordered_nav["exploreTerritories"]))
    code, out = run_with_state(nav=reordered_nav)
    check(code != 0 and "exactly the 5 stable territories" in out, "orden top-level distinto falla", out)

    missing_footer = json.loads(json.dumps(real_nav))
    missing_footer["footer"]["Obra"] = [
        item_id for item_id in missing_footer["footer"]["Obra"] if item_id != "work-samuel"
    ]
    code, out = run_with_state(nav=missing_footer)
    check(
        code != 0 and "footer.Obra must keep direct canonical access to work-samuel" in out,
        "quitar Samuel del acceso directo global falla",
        out,
    )

    broken_parent = json.loads(json.dumps(real_registry))
    registry_entry(broken_parent, "work-samuel")["parentId"] = "home"
    code, out = run_with_state(registry=broken_parent)
    check(
        code != 0 and "work-samuel: required work must remain a child of works-hub" in out,
        "romper la jerarquía Obras → Samuel falla",
        out,
    )

    hidden_work = json.loads(json.dumps(real_registry))
    registry_entry(hidden_work, "work-manecillas")["searchIndex"] = False
    code, out = run_with_state(registry=hidden_work)
    check(
        code != 0 and "work-manecillas: required work must remain indexable and in sitemap" in out,
        "degradar la indexabilidad de Manecillas falla",
        out,
    )

    main_start = real_works.find("<main")
    main_end = real_works.find("</main>", main_start)
    check(main_start >= 0 and main_end >= 0, "la página Obras contiene main")
    if main_start >= 0 and main_end >= 0:
        before = real_works[:main_start]
        main = real_works[main_start:main_end]
        after = real_works[main_end:]
        bad_main = main.replace(
            'href="/libros/samuel-entre-mundos/"',
            'href="/fragmento/"',
        )
        check(bad_main != main, "fixture puede retirar el enlace canónico de Samuel en Obras")
        code, out = run_with_state(works_html=before + bad_main + after)
        check(
            code != 0 and "works-hub main content missing direct canonical work links" in out,
            "Obras sin enlace HTML directo a Samuel falla",
            out,
        )

    if failures:
        print(f"\n{len(failures)} FALLO(S)")
        raise SystemExit(1)
    print("\ntests/test-check-navigation-coverage-territories: OK")


if __name__ == "__main__":
    run()
