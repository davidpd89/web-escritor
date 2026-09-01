#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check-third-party-integrations.py"
SPEC = importlib.util.spec_from_file_location("third_party_integrations", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_current_manifest() -> dict:
    return json.loads((ROOT / "data" / "third-party-integrations.json").read_text(encoding="utf-8"))


def basic_manifest(*, host: str = "tracker.example.test") -> dict:
    return {
        "schema_version": 1,
        "integrations": [
            {
                "id": "example",
                "provider": "Example",
                "layer": "browser",
                "status": "active",
                "purpose": "Test",
                "trigger": "Load",
                "failure_mode": "Fail-open",
                "data_scope": "Aggregate test data",
                "decision": "keep",
                "owner_files": ["app.js", "privacidad.html"],
                "evidence": [
                    {"file": "app.js", "contains": ["https://tracker.example.test/a.js"]},
                    {"file": "privacidad.html", "contains": ["Example provider"]},
                ],
                "browser_hosts": [
                    {"host": host, "directives": ["script-src", "connect-src"]}
                ],
                "privacy_evidence": ["Example provider"],
            }
        ],
    }


def fixture_root(*, csp_host: str = "tracker.example.test", app_text: str | None = None) -> Path:
    root = Path(tempfile.mkdtemp(prefix="third-party-integrations-"))
    write(
        root,
        "index.html",
        '<meta http-equiv="Content-Security-Policy" '
        f'content="default-src \'self\'; script-src \'self\' {csp_host}; '
        f'connect-src \'self\' https://{csp_host}">',
    )
    write(root, "privacidad.html", "Example provider")
    write(root, "app.js", app_text or "https://tracker.example.test/a.js")
    return root


def test_current_registry_matches_current_repo() -> None:
    manifest = load_current_manifest()
    errors = MODULE.evaluate(ROOT, manifest)
    assert not errors, "\n".join(errors)


def test_optional_disabled_requires_activation_gate() -> None:
    manifest = load_current_manifest()
    item = next(entry for entry in manifest["integrations"] if entry["status"] == "optional_disabled")
    item.pop("activation_gate", None)
    errors = MODULE.validate_manifest(manifest)
    assert any("activation_gate" in error for error in errors), errors


def test_server_side_cannot_claim_browser_host() -> None:
    manifest = load_current_manifest()
    item = next(entry for entry in manifest["integrations"] if entry["layer"] == "server_side")
    item["browser_hosts"] = [{"host": "api.example.test", "directives": ["connect-src"]}]
    errors = MODULE.validate_manifest(manifest)
    assert any("server_side no debe declarar browser_hosts" in error for error in errors), errors


def test_missing_csp_host_fails() -> None:
    root = fixture_root(csp_host="other.example.test")
    errors = MODULE.evaluate(root, basic_manifest())
    assert any("no permitido" in error for error in errors), errors


def test_missing_evidence_string_fails() -> None:
    root = fixture_root(app_text="console.log('no external loader here')")
    errors = MODULE.evaluate(root, basic_manifest())
    assert any("falta evidencia" in error for error in errors), errors


def test_optional_disabled_must_not_fake_current_privacy_disclosure() -> None:
    manifest = load_current_manifest()
    item = next(entry for entry in manifest["integrations"] if entry["status"] == "optional_disabled")
    item["privacy_evidence"] = ["Provider disclosed"]
    errors = MODULE.validate_manifest(manifest)
    assert any("no debe fingir disclosure activo" in error for error in errors), errors


if __name__ == "__main__":
    tests = [
        test_current_registry_matches_current_repo,
        test_optional_disabled_requires_activation_gate,
        test_server_side_cannot_claim_browser_host,
        test_missing_csp_host_fails,
        test_missing_evidence_string_fails,
        test_optional_disabled_must_not_fake_current_privacy_disclosure,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"\n{len(tests)} third-party integration test(s) passed.")
