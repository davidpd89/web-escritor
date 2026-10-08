#!/usr/bin/env python3
"""Mutation tests for static aria-labelledby references on public forms.

These cases are intentionally authored without depending on any current page.
The public-document checker uses the same Parser for real sitemap routes.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "check-public-document-form-contract.py"
spec = importlib.util.spec_from_file_location("public_document_form_contract", PATH)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
# dataclass needs the module registered when evaluating its annotations.
import sys
sys.modules[spec.name] = checker
spec.loader.exec_module(checker)


def findings(markup: str) -> list[str]:
    document = (
        '<!doctype html><html lang="es"><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '</head><body><main>' + markup + '</main></body></html>'
    )
    parser = checker.Parser("fixture.html")
    parser.feed(document)
    parser.close()
    return parser.finish()


GOOD_CASES = {
    "previously declared target": (
        '<span id="search-name">Buscar libros</span>'
        '<input aria-labelledby="search-name">'
    ),
    "forward reference": (
        '<input aria-labelledby="search-name">'
        '<span id="search-name">Buscar libros</span>'
    ),
    "multiple existing targets": (
        '<input aria-labelledby="subject-name subject-help">'
        '<span id="subject-name">Asunto</span>'
        '<span id="subject-help">obligatorio</span>'
    ),
    "direct aria label": '<input aria-label="Buscar libros">',
    "explicit associated label": (
        '<label for="query">Consulta</label><input id="query">'
    ),
    "native button text": '<button type="button">Buscar</button>',
}

BAD_CASES = {
    "missing sole target": (
        '<input aria-labelledby="unknown-id">', "unknown-id"
    ),
    "one missing among two references": (
        '<span id="existing">Buscar libros</span>'
        '<input aria-labelledby="existing absent">', "absent"
    ),
    "case-sensitive target": (
        '<span id="Search">Buscar libros</span>'
        '<input aria-labelledby="search">', "search"
    ),
    "comment is not a target": (
        '<!-- <span id="phantom">Buscar</span> -->'
        '<input aria-labelledby="phantom">', "phantom"
    ),
    "dangling reference even with a fallback aria-label": (
        '<input aria-label="Buscar libros" aria-labelledby="gone">', "gone"
    ),
    "placeholder does not name input": (
        '<input placeholder="Buscar libros">', "no accessible name"
    ),
}

failures: list[str] = []
for label, markup in GOOD_CASES.items():
    errors = findings(markup)
    if errors:
        failures.append(f"{label}: unexpectedly rejected: {errors!r}")

for label, (markup, expected) in BAD_CASES.items():
    errors = findings(markup)
    if not any(expected in error for error in errors):
        failures.append(f"{label}: expected {expected!r}, got {errors!r}")

if failures:
    print("FAIL public form accessible-name reference mutations")
    for issue in failures:
        print(" -", issue)
    raise SystemExit(1)

print(
    "PASS public form accessible-name reference mutations: "
    f"{len(GOOD_CASES)} positive + {len(BAD_CASES)} negative"
)
