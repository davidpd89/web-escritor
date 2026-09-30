#!/usr/bin/env python3
"""Supply-Chain Baseline & Regression Gate (Hardened 2026-09-30).

Enforces the supply-chain baseline documented in docs/supply-chain/NPM-AUDIT-BASELINE-2026-08-27.md:
1. Zero production vulnerabilities: `npm audit --omit=dev` must execute cleanly and report 0 vulnerabilities.
2. Complete machine-readable metadata: every advisory in data/npm-supply-chain-baseline.json
   must declare all required audit fields (GHSA id, package, severity, reachability, decision, owner, reviewBy).
3. Active synchronization with npm audit:
   - Fails if npm audit fails on network, invalid JSON, or empty response.
   - Fails if an uncataloged new advisory appears.
   - Fails if a known advisory changes severity without updating the baseline.
   - Fails if an advisory disappears from npm audit without updating the baseline (phantom detection).
   - Fails if the baseline review date is stale (>90 days).
"""
from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "data" / "npm-supply-chain-baseline.json"

REQUIRED_FIELDS = {
    "id", "package", "severity", "affectedRange", "dependencyType",
    "production", "reachability", "fixAvailable", "decision", "owner", "reviewBy", "sourceUrl"
}
VALID_SEVERITIES = {"low", "moderate", "high", "critical"}
VALID_DECISIONS = {"accept-temporarily", "upgrade", "remove", "monitor"}


def validate_baseline_structure(baseline_data: dict) -> list[str]:
    errors = []
    if baseline_data.get("schemaVersion") != 1:
        errors.append("Invalid schemaVersion: expected 1")
    
    last_reviewed_str = baseline_data.get("lastReviewed")
    if not last_reviewed_str:
        errors.append("Missing lastReviewed date")
    else:
        try:
            review_date = date.fromisoformat(last_reviewed_str)
            if date.today() - review_date > timedelta(days=90):
                errors.append(f"Supply-chain baseline review is stale (>90 days old): {last_reviewed_str}")
        except ValueError:
            errors.append(f"Invalid lastReviewed date format: {last_reviewed_str}")

    advisories = baseline_data.get("advisories", [])
    if not isinstance(advisories, list) or not advisories:
        errors.append("Missing or empty advisories[] array in baseline")
        return errors

    seen_ids = set()
    for item in advisories:
        adv_id = item.get("id", "")
        if not adv_id.startswith("GHSA-"):
            errors.append(f"Invalid advisory ID format: {adv_id}")
        if adv_id in seen_ids:
            errors.append(f"Duplicate advisory ID in baseline: {adv_id}")
        seen_ids.add(adv_id)

        missing = REQUIRED_FIELDS - set(item.keys())
        if missing:
            errors.append(f"{adv_id}: missing required fields: {sorted(missing)}")

        if item.get("severity") not in VALID_SEVERITIES:
            errors.append(f"{adv_id}: invalid severity '{item.get('severity')}'")

        if item.get("decision") not in VALID_DECISIONS:
            errors.append(f"{adv_id}: invalid decision '{item.get('decision')}'")

        if item.get("production") is not False:
            errors.append(f"{adv_id}: production field must be strictly false for dev vulnerabilities")

        if not str(item.get("reachability", "")).strip():
            errors.append(f"{adv_id}: reachability reasoning must not be empty")

    return errors


def run_audit(npm_cmd: str, args: list[str]) -> dict:
    proc = subprocess.run([npm_cmd, "audit", "--json"] + args, capture_output=True, text=True, cwd=ROOT)
    stdout = (proc.stdout or "").strip()
    if not stdout:
        raise RuntimeError(f"npm audit {' '.join(args)} produced empty output (exit code {proc.returncode}). Stderr: {proc.stderr}")
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"npm audit returned invalid JSON (exit code {proc.returncode}): {exc}\nStdout: {stdout[:500]}") from exc

    if "error" in parsed:
        raise RuntimeError(f"npm audit returned an error payload: {parsed['error']}")

    if "vulnerabilities" not in parsed:
        raise RuntimeError(f"npm audit JSON lacks required 'vulnerabilities' key: {list(parsed.keys())}")

    return parsed


def check_supply_chain(npm_cmd: str, baseline_data: dict) -> list[str]:
    errors = validate_baseline_structure(baseline_data)
    if errors:
        return errors

    # 1. Audit production dependencies (--omit=dev)
    prod_data = run_audit(npm_cmd, ["--omit=dev"])
    prod_vulns = prod_data.get("metadata", {}).get("vulnerabilities", {})
    total_prod = sum(prod_vulns.values()) if isinstance(prod_vulns, dict) else 0
    if total_prod != 0:
        errors.append(f"Production supply-chain has {total_prod} vulnerabilities: {prod_vulns}")

    # 2. Audit dev dependencies
    full_data = run_audit(npm_cmd, [])
    full_vulns = full_data.get("vulnerabilities", {})

    baseline_advisories = {item["id"]: item for item in baseline_data.get("advisories", [])}
    live_advisories: dict[str, dict] = {}

    for pkg, info in full_vulns.items():
        for via_item in info.get("via", []):
            if isinstance(via_item, dict):
                url = via_item.get("url", "")
                adv_id = "GHSA-" + url.split("GHSA-")[-1] if "GHSA-" in url else str(via_item.get("source", ""))
                live_advisories[adv_id] = {
                    "package": pkg,
                    "severity": via_item.get("severity", info.get("severity")),
                    "title": via_item.get("title", "")
                }

    # Detect uncataloged new advisories
    for adv_id, live_info in live_advisories.items():
        if adv_id not in baseline_advisories:
            errors.append(f"New untracked advisory: {adv_id} ({live_info['package']}, severity {live_info['severity']})")
        else:
            base_sev = baseline_advisories[adv_id].get("severity")
            if base_sev != live_info["severity"]:
                errors.append(f"{adv_id}: severity mismatch (baseline='{base_sev}', npm audit='{live_info['severity']}')")

    # Detect phantom advisories in baseline (advisories that were fixed/removed from tree)
    for adv_id in baseline_advisories:
        if adv_id not in live_advisories:
            errors.append(f"Phantom advisory in baseline (no longer reported by npm audit): {adv_id} - clean up baseline.")

    return errors


def main() -> None:
    assert BASELINE_PATH.is_file(), f"Missing baseline file: {BASELINE_PATH}"
    baseline_data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_cmd:
        print("SKIP test-npm-supply-chain-baseline (npm binary not found in PATH)")
        sys.exit(0)

    errors = check_supply_chain(npm_cmd, baseline_data)
    assert not errors, "Supply-chain baseline checks failed:\n" + "\n".join(f"- {e}" for e in errors)
    print("  ok   1. Production supply-chain has 0 vulnerabilities (npm audit --omit=dev)")
    print(f"  ok   2. All {len(baseline_data.get('advisories', []))} dev supply-chain advisories match live npm audit exactly")
    print("test-npm-supply-chain-baseline: OK")


if __name__ == "__main__":
    main()
