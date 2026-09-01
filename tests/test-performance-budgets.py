#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check-performance-budgets.py"
SPEC = importlib.util.spec_from_file_location("performance_budgets", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def fixture_root() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="performance-budget-"))
    write(tmp, "assets/a.css", '@import "/assets/b.css";\n.a{display:block}\n')
    write(tmp, "assets/b.css", ".b{display:block}\n")
    write(
        tmp,
        "assets/main.js",
        'import { value } from "/assets/dep.js";\nimport("/assets/lazy.js");\nconsole.log(value);\n',
    )
    write(tmp, "assets/dep.js", "export const value = 1;\n")
    write(tmp, "assets/lazy.js", "console.log('lazy');\n")
    return tmp


def test_graph_ignores_dynamic_import() -> None:
    root = fixture_root()
    files, errors = MODULE.collect_graph(root, ["assets/a.css", "assets/main.js"])
    assert not errors, errors
    rel = {path.relative_to(root).as_posix() for path in files}
    assert rel == {"assets/a.css", "assets/b.css", "assets/main.js", "assets/dep.js"}, rel
    metrics = MODULE.metrics_for(files)
    assert metrics["request_count"] == 4
    assert metrics["css_bytes"] > 0
    assert metrics["js_bytes"] > 0


def test_report_mode_has_no_budget_violation_without_limits() -> None:
    root = fixture_root()
    manifest = {
        "schema_version": 1,
        "enforcement": "report",
        "budgets": [{"id": "demo", "entrypoints": ["assets/a.css", "assets/main.js"]}],
    }
    report, errors = MODULE.evaluate(root, manifest)
    assert not errors, errors
    assert report["budgets"][0]["violations"] == []


def test_enforce_mode_fails_over_limit() -> None:
    root = fixture_root()
    manifest = {
        "schema_version": 1,
        "enforcement": "enforce",
        "budgets": [
            {
                "id": "demo",
                "entrypoints": ["assets/a.css", "assets/main.js"],
                "limits": {"total_bytes": 1, "request_count": 1},
            }
        ],
    }
    report, errors = MODULE.evaluate(root, manifest)
    assert errors
    violations = report["budgets"][0]["violations"]
    assert any("total_bytes" in item for item in violations)
    assert any("request_count" in item for item in violations)


def test_enforce_requires_limits() -> None:
    root = fixture_root()
    manifest = {
        "schema_version": 1,
        "enforcement": "enforce",
        "budgets": [{"id": "demo", "entrypoints": ["assets/a.css"]}],
    }
    _, errors = MODULE.evaluate(root, manifest)
    assert any("sin limits" in item for item in errors), errors


def test_manifest_rejects_unknown_metric() -> None:
    manifest = {
        "schema_version": 1,
        "enforcement": "report",
        "budgets": [
            {
                "id": "demo",
                "entrypoints": ["assets/a.css"],
                "limits": {"mystery_bytes": 1},
            }
        ],
    }
    errors = MODULE.validate_manifest(manifest)
    assert any("no es metrica soportada" in item for item in errors), errors


if __name__ == "__main__":
    tests = [
        test_graph_ignores_dynamic_import,
        test_report_mode_has_no_budget_violation_without_limits,
        test_enforce_mode_fails_over_limit,
        test_enforce_requires_limits,
        test_manifest_rejects_unknown_metric,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"\n{len(tests)} performance budget test(s) passed.")
