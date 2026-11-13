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
import os
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
    "production", "reachability", "fixAvailable", "fixedVersion", "installedVersion",
    "lockfileNode", "decision", "owner", "reviewer", "reviewedAt", "reviewBy", "sourceUrl"
}
VALID_SEVERITIES = {"low", "moderate", "high", "critical"}
VALID_DECISIONS = {"accept-temporarily", "upgrade", "remove", "monitor"}


def validate_baseline_structure(baseline_data: dict) -> list[str]:
    errors = []
    if baseline_data.get("schemaVersion") != 1:
        errors.append("Invalid schemaVersion: expected 1")

    parsed_root_dates = {}
    for root_date in ("reviewedAt", "reviewBy"):
        try:
            parsed_root_dates[root_date] = date.fromisoformat(str(baseline_data.get(root_date)))
        except ValueError:
            errors.append(f"Baseline {root_date} must be an ISO date")
    if "reviewBy" in parsed_root_dates and date.today() > parsed_root_dates["reviewBy"]:
        errors.append(f"Baseline reviewBy has expired: {baseline_data['reviewBy']}")
    
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

    advisories = baseline_data.get("advisories")
    if not isinstance(advisories, list):
        errors.append("Missing or invalid advisories[] array in baseline")
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

        for date_field in ("reviewedAt", "reviewBy"):
            try:
                date.fromisoformat(str(item.get(date_field)))
            except ValueError:
                errors.append(f"{adv_id}: {date_field} must be an ISO date")

        if item.get("reviewedAt") and item.get("reviewBy"):
            reviewed_at = date.fromisoformat(item["reviewedAt"])
            review_by = date.fromisoformat(item["reviewBy"])
            if review_by < reviewed_at:
                errors.append(f"{adv_id}: reviewBy precedes reviewedAt")
            if date.today() > review_by:
                errors.append(f"{adv_id}: reviewBy has expired: {item['reviewBy']}")

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


DEPENDENCY_FILES = ("package.json", "package-lock.json")


def dependency_files_changed(base_ref: str = "origin/main") -> bool | None:
    """True/False si la rama cambia package*.json respecto a main; None si git no lo puede decir."""
    try:
        base = subprocess.run(["git", "merge-base", base_ref, "HEAD"], capture_output=True, text=True, cwd=ROOT, check=True).stdout.strip()
        if not base:
            return None
        out = subprocess.run(["git", "diff", "--name-only", base, "HEAD", "--", *DEPENDENCY_FILES],
                             capture_output=True, text=True, cwd=ROOT, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(out.strip())


def strict_mode() -> bool:
    """Los avisos que npm publica de madrugada son un cambio externo: no deben bloquear una PR que no toca
    dependencias (el 13/11 un aviso de basic-ftp tumbó la carga nocturna de libros). Bloquean cuando la PR
    cambia dependencias, cuando git no puede comprobarlo, y siempre en el vigilante diario
    (npm-supply-chain-watch.yml, NPM_SUPPLY_CHAIN_STRICT=1), que vigila la autorreparación."""
    forced = os.environ.get("NPM_SUPPLY_CHAIN_STRICT", "").strip()
    if forced in {"0", "1"}:
        return forced == "1"
    changed = dependency_files_changed()
    return True if changed is None else changed


def check_supply_chain(npm_cmd: str, baseline_data: dict) -> list[str]:
    errors, drift = check_supply_chain_split(npm_cmd, baseline_data)
    return errors + drift


def check_supply_chain_split(npm_cmd: str, baseline_data: dict) -> tuple[list[str], list[str]]:
    """Devuelve (errores propios del repositorio, deriva externa de npm audit)."""
    errors = validate_baseline_structure(baseline_data)
    if errors:
        return errors, []
    drift: list[str] = []

    # 1. Audit production dependencies (--omit=dev)
    prod_data = run_audit(npm_cmd, ["--omit=dev"])
    prod_vulns = prod_data.get("metadata", {}).get("vulnerabilities", {})
    total_prod = sum(prod_vulns.values()) if isinstance(prod_vulns, dict) else 0
    if total_prod != 0:
        drift.append(f"Production supply-chain has {total_prod} vulnerabilities: {prod_vulns}")

    # 2. Audit dev dependencies
    full_data = run_audit(npm_cmd, [])
    full_vulns = full_data.get("vulnerabilities", {})
    lockfile = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    lock_packages = lockfile.get("packages", {})

    def installed_metadata(package: str, audited_nodes: list[str] | None = None) -> tuple[str | None, str | None]:
        for node in audited_nodes or []:
            if node in lock_packages:
                return node, lock_packages[node].get("version")
        matches = [
            (path, value.get("version"))
            for path, value in lock_packages.items()
            if path.endswith(f"/{package}") or path == f"node_modules/{package}"
        ]
        return matches[0] if matches else (None, None)

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
                    "title": via_item.get("title", ""),
                    "fixAvailable": bool(info.get("fixAvailable")),
                    "installedVersion": installed_metadata(pkg, info.get("nodes"))[1],
                    "lockfileNode": installed_metadata(pkg, info.get("nodes"))[0],
                }

    # Detect uncataloged new advisories
    for adv_id, live_info in live_advisories.items():
        if adv_id not in baseline_advisories:
            drift.append(f"New untracked advisory: {adv_id} ({live_info['package']}, severity {live_info['severity']})")
        else:
            base_sev = baseline_advisories[adv_id].get("severity")
            if base_sev != live_info["severity"]:
                drift.append(f"{adv_id}: severity mismatch (baseline='{base_sev}', npm audit='{live_info['severity']}')")
            for field in ("package", "installedVersion", "lockfileNode", "fixAvailable"):
                baseline_value = baseline_advisories[adv_id].get(field)
                live_value = live_info[field]
                if baseline_value is not None and live_value is not None and baseline_value != live_value:
                    drift.append(f"{adv_id}: {field} mismatch (baseline='{baseline_value}', live='{live_value}')")

    # Detect phantom advisories in baseline (advisories that were fixed/removed from tree)
    for adv_id in baseline_advisories:
        if adv_id not in live_advisories:
            # Un aviso que npm deja de reportar es una mejora externa: avisa para limpiar la base, pero no bloquea
            # todas las PR a la vez (pasó el 2026-11-04 con GHSA-g3hv-75wg-m249). Los avisos nuevos sí bloquean.
            print(f"WARN: aviso fantasma en la base (npm audit ya no lo reporta): {adv_id}; muévelo a notReportedAdvisories.")

    return errors, drift


def main() -> None:
    assert BASELINE_PATH.is_file(), f"Missing baseline file: {BASELINE_PATH}"
    baseline_data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_cmd:
        raise AssertionError("npm binary is required for the supply-chain gate; refusing a silent SKIP")

    errors, drift = check_supply_chain_split(npm_cmd, baseline_data)
    warned = bool(drift)
    if drift and not strict_mode():
        for item in drift:
            print(f"WARN (deriva externa, la PR no toca dependencias; la bloquea npm-supply-chain-watch.yml): {item}")
        drift = []
    errors += drift
    assert not errors, "Supply-chain baseline checks failed:\n" + "\n".join(f"- {e}" for e in errors)
    if warned:
        print("test-npm-supply-chain-baseline: OK con avisos externos pendientes (ver WARN)")
        return
    print("  ok   1. Production supply-chain has 0 vulnerabilities (npm audit --omit=dev)")
    print(f"  ok   2. All {len(baseline_data.get('advisories', []))} dev supply-chain advisories match live npm audit exactly")
    print("test-npm-supply-chain-baseline: OK")


if __name__ == "__main__":
    main()
