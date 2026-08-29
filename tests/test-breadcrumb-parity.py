#!/usr/bin/env python3
"""Regression tests for A.6 breadcrumb integrity semantics."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_breadcrumb_parity",
    ROOT / "scripts" / "check-breadcrumb-parity.py",
)
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

failures: list[str] = []


def check(condition: bool, label: str, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}{': ' + detail if detail else ''}")
        failures.append(label)


def registry(root: Path, *, extra: list[dict] | None = None) -> Path:
    payload = {
        "entries": [
            {
                "id": "home",
                "url": "/",
                "label": "Inicio",
                "shortLabel": "Inicio",
                "status": "public",
                "searchIndex": False,
                "sourceFile": "index.html",
            },
            {
                "id": "hub",
                "url": "/section/",
                "label": "Sección",
                "shortLabel": "Sección",
                "status": "public",
                "searchIndex": False,
                "sourceFile": "section/index.html",
            },
            {
                "id": "page",
                "url": "/section/page/",
                "label": "Page",
                "shortLabel": "Page",
                "status": "public",
                "searchIndex": True,
                "sourceFile": "section/page/index.html",
            },
        ] + (extra or [])
    }
    path = root / "data/content-registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def make_root(html: str, *, extra: list[dict] | None = None) -> tuple[Path, Path]:
    root = Path(tempfile.mkdtemp())
    page = root / "section/page/index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(html, encoding="utf-8")
    return root, registry(root, extra=extra)


def findings(report: dict) -> list[dict]:
    return [finding for route in report["routes"] for finding in route["findings"]]


CANON = '<link rel="canonical" href="https://davidportodiaz.com/section/page/">'
VISIBLE = (
    '<nav class="editorial-breadcrumb" aria-label="Ruta de navegación"><ol>'
    '<li><a href="/">Inicio</a></li>'
    '<li><a href="/section/">Sección</a></li>'
    '<li aria-current="page">Page</li>'
    '</ol></nav>'
)
JSONLD = (
    '<script type="application/ld+json">'
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Inicio","item":"https://davidportodiaz.com/"},'
    '{"@type":"ListItem","position":2,"name":"Sección","item":"https://davidportodiaz.com/section/"},'
    '{"@type":"ListItem","position":3,"name":"Page"}'
    ']}</script>'
)

print("tests/test-breadcrumb-parity")

# 1. Existing visible + JSON-LD trail passes.
root, reg = make_root(CANON + VISIBLE + JSONLD)
report = mod.run_audit(root, reg)
check(report["summary"]["errors"] == 0, "matching visible + JSON-LD passes", str(findings(report)))
check(report["summary"]["visible+jsonld"] == 1, "matching route classified visible+jsonld")

# 2. JSON-LD-only is valid: no forced duplicate visual row.
root, reg = make_root(CANON + JSONLD)
report = mod.run_audit(root, reg)
check(report["summary"]["errors"] == 0, "JSON-LD-only does not fail")
check(
    any(f["code"] == "missing-visible" and f["severity"] == "info" for f in findings(report)),
    "JSON-LD-only is reported as informational coverage",
)

# 3. Visible-only is also valid; structured data is an optional enhancement.
root, reg = make_root(CANON + VISIBLE)
report = mod.run_audit(root, reg)
check(report["summary"]["errors"] == 0, "visible-only breadcrumb does not fail")
check(
    any(f["code"] == "missing-jsonld" and f["severity"] == "info" for f in findings(report)),
    "visible-only is inventoried as structured-data opportunity",
)

# 4. Google permits omitting host and current page, while still requiring >=2 items.
extra_deep = [
    {
        "id": "category",
        "url": "/category/",
        "label": "Categoría",
        "shortLabel": "Categoría",
        "status": "public",
        "searchIndex": False,
        "sourceFile": "category/index.html",
    }
]
VISIBLE_DEEP = (
    '<nav class="breadcrumb" aria-label="Ruta de navegación"><ol>'
    '<li><a href="/">Inicio</a></li>'
    '<li><a href="/category/">Categoría</a></li>'
    '<li><a href="/section/">Sección</a></li>'
    '<li aria-current="page">Page</li>'
    '</ol></nav>'
)
JSONLD_NO_HOST_CURRENT = (
    '<script type="application/ld+json">'
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Categoría","item":"https://davidportodiaz.com/category/"},'
    '{"@type":"ListItem","position":2,"name":"Sección","item":"https://davidportodiaz.com/section/"}'
    ']}</script>'
)
root, reg = make_root(CANON + VISIBLE_DEEP + JSONLD_NO_HOST_CURRENT, extra=extra_deep)
report = mod.run_audit(root, reg)
check(
    report["summary"]["errors"] == 0,
    "structured trail may omit host/current while keeping two items",
    str(findings(report)),
)

# 5. Different human/structured labels on the same destination are not objective drift.
VISIBLE_LABEL_VARIANT = VISIBLE.replace(">Sección</a>", ">Obras</a>")
JSONLD_LABEL_VARIANT = JSONLD.replace('"name":"Sección"', '"name":"Libros"')
root, reg = make_root(CANON + VISIBLE_LABEL_VARIANT + JSONLD_LABEL_VARIANT)
report = mod.run_audit(root, reg)
check(
    report["summary"]["errors"] == 0,
    "label wording may differ when destination URL is valid",
    str(findings(report)),
)

# 6. Shared destinations in contradictory order are real order drift.
JSONLD_REVERSED = (
    '<script type="application/ld+json">'
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Sección","item":"https://davidportodiaz.com/section/"},'
    '{"@type":"ListItem","position":2,"name":"Categoría","item":"https://davidportodiaz.com/category/"},'
    '{"@type":"ListItem","position":3,"name":"Page"}'
    ']}</script>'
)
root, reg = make_root(CANON + VISIBLE_DEEP + JSONLD_REVERSED, extra=extra_deep)
report = mod.run_audit(root, reg)
check(
    any(f["code"] == "order-drift" and "conflicts" in f["message"] for f in findings(report)),
    "contradictory shared URL order fails",
)

# 7. External breadcrumb destinations fail objective URL integrity.
JSONLD_EXTERNAL = JSONLD.replace(
    "https://davidportodiaz.com/section/",
    "https://example.com/section/",
)
root, reg = make_root(CANON + JSONLD_EXTERNAL)
report = mod.run_audit(root, reg)
check(
    any(f["code"] == "url-drift" and "external" in f["message"] for f in findings(report)),
    "external breadcrumb URL fails",
)

# 8. Current canonical cannot appear before the end of a trail.
JSONLD_CURRENT_EARLY = (
    '<script type="application/ld+json">'
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Page","item":"https://davidportodiaz.com/section/page/"},'
    '{"@type":"ListItem","position":2,"name":"Sección","item":"https://davidportodiaz.com/section/"}'
    ']}</script>'
)
root, reg = make_root(CANON + JSONLD_CURRENT_EARLY)
report = mod.run_audit(root, reg)
check(
    any(f["code"] == "order-drift" and "current canonical" in f["message"] for f in findings(report)),
    "current canonical before trail end fails",
)

# 9. Structured positions are an ordered contract.
JSONLD_BAD_POS = JSONLD.replace('"position":2', '"position":3')
root, reg = make_root(CANON + JSONLD_BAD_POS)
report = mod.run_audit(root, reg)
check(
    any(f["code"] == "order-drift" and "positions" in f["message"] for f in findings(report)),
    "non-consecutive BreadcrumbList positions fail",
)

# Shared extra route for multiple-trail tests.
extra_other = [
    {
        "id": "other",
        "url": "/other/",
        "label": "Other",
        "shortLabel": "Other",
        "status": "public",
        "searchIndex": False,
        "sourceFile": "other/index.html",
    }
]

# 10. Multiple structured trails are supported; one need not duplicate the visible path.
MULTI_JSONLD = (
    '<script type="application/ld+json">['
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Other","item":"https://davidportodiaz.com/other/"},'
    '{"@type":"ListItem","position":2,"name":"Page"}]},'
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Sección","item":"https://davidportodiaz.com/section/"},'
    '{"@type":"ListItem","position":2,"name":"Page"}]}'
    ']</script>'
)
root, reg = make_root(CANON + VISIBLE + MULTI_JSONLD, extra=extra_other)
report = mod.run_audit(root, reg)
check(
    report["summary"]["errors"] == 0,
    "multiple valid BreadcrumbList trails are supported",
    str(findings(report)),
)

# 11. Malformed breadcrumb JSON-LD is owned by this checker.
MALFORMED = (
    '<script type="application/ld+json">'
    '{"@type":"BreadcrumbList","itemListElement":['
    '</script>'
)
root, reg = make_root(CANON + MALFORMED)
report = mod.run_audit(root, reg)
check(
    any(f["code"] == "invalid-jsonld" for f in findings(report)),
    "malformed breadcrumb JSON-LD fails",
)

# 12. A route with no breadcrumb contract remains valid.
root, reg = make_root(CANON)
report = mod.run_audit(root, reg)
check(report["summary"]["errors"] == 0, "no-breadcrumb route remains valid")
check(report["summary"]["none"] == 1, "no-breadcrumb route is inventoried")

# 13. Non-root-relative breadcrumb links are rejected instead of guessed.
VISIBLE_RELATIVE = VISIBLE.replace('href="/section/"', 'href="../"')
root, reg = make_root(CANON + VISIBLE_RELATIVE + JSONLD)
report = mod.run_audit(root, reg)
check(
    any(f["code"] == "url-drift" and "non-root-relative" in f["message"] for f in findings(report)),
    "ambiguous relative breadcrumb URL fails",
)

# 14. Google requires at least two ListItems when BreadcrumbList is used.
JSONLD_ONE_ITEM = (
    '<script type="application/ld+json">'
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Sección","item":"https://davidportodiaz.com/section/"}'
    ']}</script>'
)
root, reg = make_root(CANON + JSONLD_ONE_ITEM)
report = mod.run_audit(root, reg)
check(
    any(f["code"] == "invalid-jsonld" and "at least 2" in f["message"] for f in findings(report)),
    "single-item BreadcrumbList fails",
)

# 15. Every non-final structured ListItem must provide an item URL.
JSONLD_MISSING_NONFINAL_ITEM = (
    '<script type="application/ld+json">'
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Sección"},'
    '{"@type":"ListItem","position":2,"name":"Page"}'
    ']}</script>'
)
root, reg = make_root(CANON + JSONLD_MISSING_NONFINAL_ITEM)
report = mod.run_audit(root, reg)
check(
    any(f["code"] == "missing-item" for f in findings(report)),
    "non-final BreadcrumbList item without URL fails",
)

print(
    "tests/test-breadcrumb-parity: "
    + ("OK" if not failures else f"{len(failures)} FALLO(S)")
)
raise SystemExit(1 if failures else 0)
