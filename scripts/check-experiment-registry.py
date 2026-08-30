#!/usr/bin/env python3
"""Validate the lightweight, versioned experiment registry from Q.3.

The registry is deliberately small. It records decision memory; it does not
create experiments, authorize deploys, or collect analytics. The historical
baseline from PR #135 is valid with an empty experiments array.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "experiments.json"
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_DECISIONS = ["KEEP", "REVERT", "ITERATE", "INCONCLUSIVE"]
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"registry is missing: {path}"]
    except json.JSONDecodeError as exc:
        return [f"invalid JSON in {path}: {exc}"]

    if not isinstance(payload, dict):
        return ["registry root must be a JSON object"]

    if payload.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
        errors.append(
            f"schemaVersion must be {EXPECTED_SCHEMA_VERSION}, got {payload.get('schemaVersion')!r}"
        )

    description = payload.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("description must be a non-empty string")

    decisions = payload.get("allowedDecisions")
    if decisions != EXPECTED_DECISIONS:
        errors.append(
            "allowedDecisions must preserve the Q.3 contract: "
            + ", ".join(EXPECTED_DECISIONS)
        )

    experiments = payload.get("experiments")
    if not isinstance(experiments, list):
        errors.append("experiments must be an array")
        return errors

    seen_ids: set[str] = set()
    for index, experiment in enumerate(experiments):
        label = f"experiments[{index}]"
        if not isinstance(experiment, dict):
            errors.append(f"{label} must be an object")
            continue

        experiment_id = experiment.get("id")
        if not isinstance(experiment_id, str) or not ID_RE.fullmatch(experiment_id):
            errors.append(f"{label}.id must be a stable kebab-case identifier")
        elif experiment_id in seen_ids:
            errors.append(f"duplicate experiment id: {experiment_id}")
        else:
            seen_ids.add(experiment_id)

        # Q.3 requires these to be defined before interpreting a result. Keep
        # the validator intentionally agnostic about how each baseline is
        # represented (text, object or numeric snapshot).
        for field in ("hypothesis", "baseline"):
            if not is_present(experiment.get(field)):
                errors.append(f"{label}.{field} is required and cannot be empty")

        decision = experiment.get("decision")
        if decision is not None and decision not in EXPECTED_DECISIONS:
            errors.append(
                f"{label}.decision must be null/omitted while pending or one of "
                + ", ".join(EXPECTED_DECISIONS)
            )

    return errors


def main() -> int:
    if len(sys.argv) > 2:
        print("usage: check-experiment-registry.py [path]", file=sys.stderr)
        return 2

    path = Path(sys.argv[1]) if len(sys.argv) == 2 else DEFAULT_REGISTRY
    errors = validate(path)
    if errors:
        print("check-experiment-registry: FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"check-experiment-registry: OK ({path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
