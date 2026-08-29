#!/usr/bin/env python3
"""Regression tests for A.6 breadcrumb parity semantics."""

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


def registry(
    root: Path,
    *,
    aliases: list[str] | None = None,
    extra: list[dict] | None = None,
) -> Path:
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
                "aliases": aliases or [],
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


def make_root(
    html: str,
    *,
    aliases: list[str] | None = None,
    extra: list[dict] | None = None,
) -> tuple[Path, Path]:
    root = Path(tempfile.mkdtemp())
    page = root / "section/page/index.html"
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(html, encoding="utf-8")
    return root, registry(root, aliases=aliases, extra=extra)


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

# 3. A family that renders a visible breadcrumb must keep structured parity.
root, reg = make_root(CANON + VISIBLE)
report = mod.run_audit(root, reg)
check(
    any(f["code"] == "missing-jsonld" and f["severity"] == "error" for f in findings(report)),
    "visible-only breadcrumb fails missing-jsonld",
)

# 4. Google permits omitting Home and/or the current page from BreadcrumbList.
JSONLD_INTERMEDIATE_ONLY = (
    '<script type="application/ld+json">'
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Sección","item":"https://davidportodiaz.com/section/"}'
    ']}</script>'
)
root, reg = make_root(CANON + VISIBLE + JSONLD_INTERMEDIATE_ONLY)
report = mod.run_audit(root, reg)
check(
    report["summary"]["errors"] == 0,
    "structured trail may omit Home/current item",
    str(findings(report)),
)

# 5. Registry aliases allow human/structured labels to differ without fake drift.
VISIBLE_OBRAS = VISIBLE.replace(">Sección</a>", ">Obras</a>")
JSONLD_LIBROS = JSONLD.replace('"name":"Sección"', '"name":"Libros"')
root, reg = make_root(CANON + VISIBLE_OBRAS + JSONLD_LIBROS, aliases=["Obras", "Libros"])
report = mod.run_audit(root, reg)
check(report["summary"]["errors"] == 0, "registry aliases reconcile breadcrumb labels", str(findings(report)))

# 6. Intermediate URL sequence drift fails.
extra = [{
    "id": "other",
    "url": "/other/",
    "label": "Other",
    "shortLabel": "Other",
    "status": "public",
    "searchIndex": False,
    "sourceFile": "other/index.html",
}]
JSONLD_OTHER = JSONLD.replace(
    '"name":"Sección","item":"https://davidportodiaz.com/section/"',
    '"name":"Other","item":"https://davidportodiaz.com/other/"',
)
root, reg = make_root(CANON + VISIBLE + JSONLD_OTHER, extra=extra)
report = mod.run_audit(root, reg)
check(
    any(f["code"] == "order-drift" for f in findings(report)),
    "visible/structured intermediate drift fails",
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

# 10. Multiple structured trails are supported when one matches the visible path.
MULTI_JSONLD = (
    '<script type="application/ld+json">['
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Other","item":"https://davidportodiaz.com/other/"}]},'
    '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
    '{"@type":"ListItem","position":1,"name":"Sección","item":"https://davidportodiaz.com/section/"}]}'
    ']</script>'
)
root, reg = make_root(CANON + VISIBLE + MULTI_JSONLD, extra=extra)
report = mod.run_audit(root, reg)
check(
    report["summary"]["errors"] == 0,
    "multiple BreadcrumbList trails are allowed when one matches",
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

print(
    "tests/test-breadcrumb-parity: "
    + ("OK" if not failures else f"{len(failures)} FALLO(S)")
)
raise SystemExit(1 if failures else 0)
