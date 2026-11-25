#!/usr/bin/env python3
"""The ruleset-required merge gate must cover universal engine contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
workflow = (ROOT / ".github" / "workflows" / "required-merge-gate.yml").read_text(encoding="utf-8")
# Los contratos Python viven en un script común con main-contratos.yml (main tras cada fusión): la puerta debe
# llamarlo en los dos modos, y el script cuenta como parte de la puerta.
for modo in ("guion", "subrayado"):
    assert f"bash scripts/run-python-contracts.sh {modo}" in workflow, f"La puerta ya no corre los contratos ({modo})"
workflow += (ROOT / "scripts" / "run-python-contracts.sh").read_text(encoding="utf-8")

required_fragments = [
    "name: Required merge gate",
    "scripts/requirements.txt",
    "for f in tests/test-*.py",
    # Los underscore-named corren un fichero por proceso, en paralelo; debe recorrerlos todos.
    "for f in tests/test_*.py",
    'python -m unittest discover -s tests -p "${f##*/}"',
    "for f in tests/*.mjs",
    "python tests/test-release-identity.py",
    "python tests/test-public-artifact-contract.py",
    "python tests/test-staging-publication-gate.py",
    "python scripts/build-public-dist.py --check-contents",
]
missing = [fragment for fragment in required_fragments if fragment not in workflow]
assert not missing, (
    "Required merge gate lost universal/release contracts that main's ruleset relies on: "
    + ", ".join(missing)
)

print("PASS required merge gate universal coverage")

tools_workflow = (ROOT / ".github/workflows/tool-tests.yml").read_text(encoding="utf-8")
assert "python -m unittest discover -s tests -p 'test_*.py'" in tools_workflow, (
    "Tool engine tests must include underscore-named Python contracts"
)
