#!/usr/bin/env python3
"""Regression for the PRELAUNCH_AVAILABLE checker's cross-entity false
positive (GPT audit, 2026-09-01): 'Las manecillas del recuerdo.{0,180}
disponible' can span across an unrelated mention of Samuel entre mundos,
flagging correct copy ("...Samuel entre mundos ya está disponible") as a
premature Manecillas availability claim. _is_cross_entity_availability()
must suppress that case while still catching a real, unqualified claim.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check-editorial-facts.py"

spec = importlib.util.spec_from_file_location("check_editorial_facts", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)  # type: ignore[union-attr]


def find_violation(text: str) -> bool:
    stripped = module._strip_asset_status_badges(text)
    for pattern in module.PRELAUNCH_AVAILABLE:
        m = pattern.search(stripped)
        if m and not module._is_conditional_availability(stripped, m) and not module._is_cross_entity_availability(m):
            return True
    return False


# PASS: Samuel's own, real availability sits between the Manecillas mention
# and "disponible" -- must NOT be flagged.
should_not_flag = "Las manecillas del recuerdo, con Monza Ediciones. Mientras tanto, Samuel entre mundos ya está disponible en librerías."
assert not find_violation(should_not_flag), "cross-entity Samuel availability must not flag as a Manecillas violation"

# FAIL: a direct, unqualified claim about Manecillas itself must still flag.
should_flag = "Las manecillas del recuerdo ya está disponible en tu librería habitual."
assert find_violation(should_flag), "a real premature Manecillas availability claim must still be caught"

# Conditional/future phrasing guard must still work unaffected.
still_conditional = "Los enlaces de compra de Las manecillas del recuerdo aparecerán en cuanto estén disponibles."
assert not find_violation(still_conditional), "existing conditional-availability guard must be unaffected"

print("test-editorial-facts-cross-entity: all assertions passed")
