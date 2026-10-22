#!/usr/bin/env python3
"""Offline proof contract for publisher contacts and manuscript-reception status.

Research-only. Reads manually recorded observations and an *independently vetted*
source-host allowlist. Does not fetch webpages, extract email addresses, write
public datasets, or infer manuscript acceptance from a group/contact page.

Usage:
  python scripts/research/gpt_editoriales_contact_evidence.py \
    --observations input-observations.json --trusted-hosts vetted-hosts.json \
    --as-of 2026-10-22

Trusted hosts must be vetted against an official organization page, not supplied
by an untrusted observation itself. Reports contain URLs and status suggestions,
never contact addresses or raw page excerpts. All suggestions require review.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

PURPOSES = {"general_contact", "press_contact", "submissions_open",
            "submissions_paused", "group_submission_channel", "publisher_imprint"}
STATUS_KIND = {"submissions_open": "open", "submissions_paused": "closed"}
STATUS_TTL_DAYS = 45
CONTACT_TTL_DAYS = 180
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DNS = re.compile(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\Z", re.I)


def safe_host(url: object) -> str | None:
    if not isinstance(url, str) or len(url) > 1400 or any(ord(c) < 32 for c in url):
        return None
    try:
        parts = urlsplit(url)
        host = parts.hostname
        if not (parts.scheme == "https" and host and DNS.fullmatch(host)
                and "." in host and ".." not in host and not parts.username
                and not parts.password and parts.port in (None, 443)
                and not parts.fragment and not host.endswith((".local", ".internal",
                    ".test", ".example", ".invalid"))):
            return None
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return host.lower()
    except ValueError:
        return None
    return None


def review(observations: dict, vetted_hosts: dict, *, as_of: date) -> dict:
    if observations.get("schema_version") != 1 or not isinstance(observations.get("observations"), list):
        raise ValueError("observations schema must be version 1 and contain a list")
    if vetted_hosts.get("schema_version") != 1 or not isinstance(vetted_hosts.get("publishers"), dict):
        raise ValueError("host approval schema must be version 1 and contain publishers map")
    approvals = {}
    for slug, entry in vetted_hosts["publishers"].items():
        if not isinstance(slug, str) or not SLUG.fullmatch(slug) or not isinstance(entry, dict):
            raise ValueError("invalid trusted publisher entry")
        allowed = entry.get("hosts")
        if (not isinstance(allowed, list) or not allowed or
                not all(isinstance(v, str) and safe_host("https://" + v) == v for v in allowed)):
            raise ValueError("hosts must be verified lowercase public DNS names")
        approvals[slug] = set(allowed)
    observed_ids = set()
    issues = []
    by_slug = defaultdict(lambda: {
        "general_sources": [], "press_sources": [], "publisher_sources": [],
        "group_submission_sources": [], "submission_status_candidates": []})
    for i, obs in enumerate(observations["observations"]):
        ref = f"observation[{i}]"
        if not isinstance(obs, dict):
            issues.append({"record": ref, "reason": "invalid_record"})
            continue
        ident = obs.get("id")
        slug = obs.get("publisher_slug")
        purpose = obs.get("purpose")
        source_url = obs.get("source_url")
        host = safe_host(source_url)
        scope = obs.get("scope")
        if (not isinstance(ident, str) or not SLUG.fullmatch(ident)
                or ident in observed_ids):
            issues.append({"record": ref, "reason": "missing_or_duplicate_id"})
            continue
        observed_ids.add(ident)
        if not isinstance(slug, str) or not SLUG.fullmatch(slug) or slug not in approvals:
            issues.append({"record": ident, "reason": "publisher_not_approved"})
            continue
        if purpose not in PURPOSES or scope not in {"publisher_specific", "group_general"}:
            issues.append({"record": ident, "reason": "invalid_purpose_or_scope"})
            continue
        if not host or host not in approvals[slug]:
            issues.append({"record": ident, "reason": "source_host_not_approved"})
            continue
        try:
            day = date.fromisoformat(obs["checked_at"])
        except (ValueError, KeyError, TypeError):
            issues.append({"record": ident, "reason": "invalid_date"})
            continue
        age = (as_of - day).days
        if age < 0:
            issues.append({"record": ident, "reason": "future_evidence"})
            continue
        # Explicit human-authored summary: not an automatic keyword extraction.
        summary = obs.get("evidence_summary")
        if not isinstance(summary, str) or not 15 <= len(summary) <= 300:
            issues.append({"record": ident, "reason": "missing_evidence_summary"})
            continue
        if "@" in summary or "@" in source_url:
            issues.append({"record": ident, "reason": "possible_personal_data_or_address"})
            continue
        limit = STATUS_TTL_DAYS if purpose.startswith("submissions_") or purpose == "group_submission_channel" else CONTACT_TTL_DAYS
        expired = age > limit
        evidence = {"id": ident, "source_url": source_url,
                    "checked_at": day.isoformat(), "expired": expired,
                    "purpose": purpose, "scope": scope}
        dest = by_slug[slug]
        if purpose == "general_contact":
            dest["general_sources"].append(evidence)
        elif purpose == "press_contact":
            dest["press_sources"].append(evidence)
        elif purpose == "publisher_imprint":
            dest["publisher_sources"].append(evidence)
        elif purpose == "group_submission_channel":
            dest["group_submission_sources"].append(evidence)
        else:
            evidence["proposed_status"] = STATUS_KIND[purpose] if scope == "publisher_specific" and not expired else "unknown"
            dest["submission_status_candidates"].append(evidence)

    results = []
    for slug, values in sorted(by_slug.items()):
        current = {item["proposed_status"] for item in values["submission_status_candidates"]
                   if item["proposed_status"] != "unknown"}
        if len(current) > 1:
            status = "conflict_review"
        elif current:
            status = next(iter(current))
        else:
            status = "not_inferred"
        result = {"slug": slug, **values, "proposed_manuscript_status": status,
                  "manual_review_required": True, "publication_allowed": False}
        results.append(result)
    return {
        "schema_version": 1, "as_of": as_of.isoformat(),
        "policy": "No group inheritance, no email inference, no automatic publication.",
        "publishers": results, "rejected_observations": issues,
        "writes_to_public_data": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--observations", type=Path, required=True)
    p.add_argument("--trusted-hosts", type=Path, required=True)
    p.add_argument("--as-of", type=date.fromisoformat, required=True)
    opts = p.parse_args(argv)
    try:
        with opts.observations.open(encoding="utf-8") as stream:
            observed = json.load(stream)
        with opts.trusted_hosts.open(encoding="utf-8") as stream:
            trusted = json.load(stream)
        result = review(observed, trusted, as_of=opts.as_of)
    except (OSError, ValueError, TypeError) as exc:
        print(f"Invalid or missing offline evidence: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
