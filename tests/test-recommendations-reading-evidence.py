#!/usr/bin/env python3
"""Regression fixtures for the public claims of personal reading evidence."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "check-recommendations-evidence.py"
spec = importlib.util.spec_from_file_location("reading_evidence_checker", PATH)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def record(reference: object) -> dict:
    return {
        "isbn": "9780000000000",
        "evidenceStatus": "leido",
        "personalReadingStatus": "leido",
        "personalReadingEvidence": {"reference": reference},
    }


GOOD_REFERENCES = (
    "cuaderno de lectura: anotación personal fechada",
    "  ficha privada de lectura  ",
)
BAD_REFERENCES = (
    None,
    "",
    " \t\n ",
    42,
    True,
    ["ficha"],
    "TODO verificar",
)

errors: list[str] = []
with TemporaryDirectory() as temp:
    root = Path(temp)
    for value in GOOD_REFERENCES:
        _, found = checker.validate_authority(
            {"works": [record(value)], "corrections": []}, root
        )
        if found:
            errors.append(f"valid reference {value!r}: {found!r}")

    for value in BAD_REFERENCES:
        _, found = checker.validate_authority(
            {"works": [record(value)], "corrections": []}, root
        )
        expected = (
            "placeholder" if isinstance(value, str) and "TODO" in value
            else "sin personalReadingEvidence.reference"
        )
        if not any(expected in message for message in found):
            errors.append(f"invalid reference {value!r}: expected {expected!r}, got {found!r}")

    pending = {
        "isbn": "9780000000000",
        "evidenceStatus": "pendiente",
        "personalReadingStatus": "pendiente",
    }
    _, found = checker.validate_authority(
        {"works": [copy.deepcopy(pending)], "corrections": []}, root
    )
    if found:
        errors.append(f"pending reading without personal proof: {found!r}")

if errors:
    print("FAIL recommendations reading evidence mutations")
    for item in errors:
        print(" -", item)
    raise SystemExit(1)

print(
    "PASS recommendations reading evidence mutations: "
    f"{len(GOOD_REFERENCES) + 1} valid + {len(BAD_REFERENCES)} invalid"
)
