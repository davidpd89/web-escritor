#!/usr/bin/env python3
"""Schema/consistency guard for the two tools-catalog.json files.

Two catalogs exist by design (docs/claude-toolbox: broad agent-tooling;
docs/design-ux-tooling: narrow design/UX/QA scope) -- this test does not
merge them, it only guards each against silent drift: duplicate ids,
missing required fields, and an unknown state/status value.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CATALOGS = [
    {
        "path": ROOT / "docs" / "claude-toolbox" / "tools-catalog.json",
        "state_key": "status",
        "allowed_states": {
            "INSTALL_NOW", "PILOT", "ON_DEMAND", "MONITOR", "DEFER", "REJECT",
        },
        "required_fields": ["id", "name", "status", "source"],
    },
    {
        "path": ROOT / "docs" / "design-ux-tooling" / "tools-catalog.json",
        "state_key": "state",
        "allowed_states": {"RECOMMENDED", "PILOT", "DEFER", "NOT_APPLICABLE"},
        "required_fields": ["id", "name", "state", "role", "source"],
    },
]

for catalog in CATALOGS:
    path = catalog["path"]
    assert path.exists(), f"missing catalog: {path}"
    data = json.loads(path.read_text(encoding="utf-8"))
    tools = data.get("tools")
    assert isinstance(tools, list) and tools, f"{path}: 'tools' must be a non-empty list"

    ids = [t.get("id") for t in tools]
    assert all(ids), f"{path}: every tool needs a non-empty 'id'"
    assert len(ids) == len(set(ids)), f"{path}: duplicate tool ids found"

    for tool in tools:
        for field in catalog["required_fields"]:
            assert tool.get(field), f"{path}: tool {tool.get('id')!r} missing required field {field!r}"
        state = tool.get(catalog["state_key"])
        assert state in catalog["allowed_states"], (
            f"{path}: tool {tool.get('id')!r} has unknown {catalog['state_key']}={state!r}, "
            f"expected one of {sorted(catalog['allowed_states'])}"
        )

    print(f"OK: {path.relative_to(ROOT)} ({len(tools)} tools, {len(set(ids))} unique ids)")

print("PASS tools catalogs schema")
