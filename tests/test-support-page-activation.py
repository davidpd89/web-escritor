#!/usr/bin/env python3
"""build-support-page.py: sin enlace no hay ruta; con enlace válido cumple el gate de activación."""
from __future__ import annotations

import importlib.util
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load("build_support_page", "scripts/build-support-page.py")
gate = load("support_gate", "tests/test-support-release-gate.py")

assert builder.check(ROOT) == [], "el repositorio sin enlace debe estar en estado no activado"
assert gate.release_errors(ROOT) == []

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / "data").mkdir()
    for name in ("content-registry.json", "navigation.json"):
        shutil.copy(ROOT / "data" / name, root / "data" / name)
    for bad in ("https://www.paypal.com.evil.test/ncp/payment/ABC", "http://www.paypal.com/ncp/payment/ABC",
                "https://www.paypal.me/alguien", "https://www.paypal.com/ncp/payment/ABC?x=1"):
        try:
            builder.activate(root, bad)
        except ValueError:
            continue
        raise AssertionError("URL no válida aceptada: " + bad)
    assert not (root / "apoyar").exists()
    builder.activate(root, "https://www.paypal.com/ncp/payment/ABC123")
    builder.activate(root, "https://www.paypal.com/ncp/payment/ABC123")  # idempotente
    assert gate.release_errors(root) == [], gate.release_errors(root)
    assert builder.check(root) == []
    html = (root / "apoyar/index.html").read_text(encoding="utf-8")
    assert html.count("support-method") >= 1 and "noindex" not in html
    registry = builder.read_json(root / "data/content-registry.json")
    assert sum(e["id"] == "support-project" for e in registry["entries"]) == 1
print("PASS: /apoyar/ solo existe con un enlace de PayPal válido y cumple el gate")
