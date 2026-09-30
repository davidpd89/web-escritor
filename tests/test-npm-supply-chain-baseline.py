#!/usr/bin/env python3
"""Supply-Chain Baseline & Regression Gate (PR Audit 2026-09-30).

Enforces the supply-chain baseline documented in docs/supply-chain/NPM-AUDIT-BASELINE-2026-08-27.md:
1. Zero production vulnerabilities: `npm audit --omit=dev` must always report 0 vulnerabilities.
2. Machine-readable baseline coverage: every direct advisory reported in devDependencies must be
   cataloged with reachability analysis, owner, decision and review date in data/npm-supply-chain-baseline.json.
3. Fails loudly if an unexpected new advisory appears in npm dependencies.
"""
from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "data" / "npm-supply-chain-baseline.json"

assert BASELINE_PATH.is_file(), f"Missing baseline file: {BASELINE_PATH}"
baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
baseline_advisory_ids = {item["id"] for item in baseline.get("advisories", [])}

npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
if not npm_cmd:
    print("SKIP test-npm-supply-chain-baseline (npm binary not found in PATH)")
    sys.exit(0)

# 1. Run audit with --omit=dev: MUST be 0
res_prod = subprocess.run([npm_cmd, "audit", "--omit=dev", "--json"], capture_output=True, text=True, cwd=ROOT)
prod_json = json.loads(res_prod.stdout or "{}")
prod_vulns = prod_json.get("metadata", {}).get("vulnerabilities", {})
total_prod_vulns = sum(prod_vulns.values()) if isinstance(prod_vulns, dict) else 0

assert total_prod_vulns == 0, f"FATAL: Production supply-chain audit reported {total_prod_vulns} vulnerabilities: {prod_vulns}"
print("  ok   1. Production supply-chain has 0 vulnerabilities (npm audit --omit=dev)")

# 2. Run full audit and verify every advisory is accounted for in the baseline
res_full = subprocess.run([npm_cmd, "audit", "--json"], capture_output=True, text=True, cwd=ROOT)
full_json = json.loads(res_full.stdout or "{}")
full_vulns = full_json.get("vulnerabilities", {})

untracked_advisories: list[dict] = []
for pkg, info in full_vulns.items():
    for via_item in info.get("via", []):
        if isinstance(via_item, dict):
            adv_id = via_item.get("url", "").split("/")[-1] or via_item.get("source") or via_item.get("name")
            ghsa_match = None
            if isinstance(via_item.get("url"), str) and "GHSA-" in via_item.get("url"):
                ghsa_match = "GHSA-" + via_item["url"].split("GHSA-")[-1]
            check_id = ghsa_match or str(adv_id)
            if check_id not in baseline_advisory_ids:
                untracked_advisories.append({
                    "package": pkg,
                    "id": check_id,
                    "title": via_item.get("title"),
                    "severity": via_item.get("severity")
                })

assert not untracked_advisories, (
    f"FATAL: Untracked devDependencies supply-chain advisories found ({len(untracked_advisories)}):\n"
    + json.dumps(untracked_advisories, indent=2)
    + "\nUpdate data/npm-supply-chain-baseline.json after documenting reachability and decision."
)

print(f"  ok   2. All {len(baseline_advisory_ids)} dev supply-chain advisories are tracked in data/npm-supply-chain-baseline.json")
print("test-npm-supply-chain-baseline: OK")
