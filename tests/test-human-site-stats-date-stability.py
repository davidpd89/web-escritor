#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build-human-site-stats.py"
SPEC = importlib.util.spec_from_file_location("build_human_site_stats_date", MODULE_PATH)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    generated = Path(tmp) / "stats.json"
    generated.write_text(json.dumps({"generated_on": "2026-08-22", "stats": []}), encoding="utf-8")

    resolved = module.resolve_generated_on(None, True, generated)
    assert resolved == "2026-08-22", resolved

    explicit = module.resolve_generated_on("2026-08-21", True, generated)
    assert explicit == "2026-08-21", explicit

    generated.write_text(json.dumps({"generated_on": "no-es-fecha", "stats": []}), encoding="utf-8")
    try:
        module.resolve_generated_on(None, True, generated)
    except ValueError as exc:
        assert "generated_on no es fecha ISO" in str(exc), str(exc)
    else:
        raise AssertionError("un generated_on inválido debe fallar")

print("test-human-site-stats-date-stability: OK")
