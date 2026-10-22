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
import unicodedata
from collections import defaultdict
from datetime import date
from html.parser import HTMLParser
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


# Small E6.3 experimental extractor. NOT a generic legal/status classifier.
# Use the HTTP/robots/cache implementation ALREADY in main
# (reading_editorial_sources.CachedHTTP) to supply HTML only after approval.
class _PilotVisibleText(HTMLParser):
    """Visible text only: omit scripts, styles, noscript and SVG metadata."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'noscript', 'svg'}:
            self.ignored += 1
        elif tag in {'p', 'h1', 'h2', 'h3', 'h4', 'li', 'br', 'div'} and not self.ignored:
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag in {'script', 'style', 'noscript', 'svg'}:
            self.ignored = max(0, self.ignored - 1)
        elif tag in {'p', 'h1', 'h2', 'h3', 'h4', 'li', 'div'} and not self.ignored:
            self.parts.append(' ')

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


# These known-page rules are a bounded experiment, not reusable auto-approval.
# Extend only after testing diverse layouts with full real HTML; leave UNKNOWN
# if the source changes or if the explicit statement disappears.
_PILOT_EVIDENCE_RULES = {
    'editorial-anagrama': (r'pausad[ao].{0,90}recepcion de manuscritos', 'paused'),
    'nocturna-ediciones': (r'si desea enviarnos un manuscrito.{0,150}correo electronico', 'open'),
    'minotauro': (r'el proyecto debera enviarse por correo electronico', 'open'),
    'alienta-editorial': (r'alienta editorial acepta la recepcion de manuscritos originales', 'open'),
    'alfaguara': (r'solo recibe manuscritos espontaneos a traves de la web', 'group_only'),
}


def draft_from_html(html, *, slug, source_url, checked_at, source_allowlist):
    """Read one *pre-approved* page. Returns a tentative candidate, never edits."""
    if not isinstance(html, str) or len(html) > 2_000_000 or not html.strip():
        raise ValueError('Missing or oversized HTML')
    if source_allowlist.get(slug) != source_url or slug not in _PILOT_EVIDENCE_RULES:
        raise ValueError('Source or pilot slug not in independently reviewed allowlist')
    if not isinstance(checked_at, str) or date.fromisoformat(checked_at).isoformat() != checked_at:
        raise ValueError('Invalid check date')
    parser = _PilotVisibleText()
    parser.feed(html)
    visible = ' '.join(''.join(parser.parts).split())
    folded = unicodedata.normalize('NFKD', visible.casefold())
    folded = ''.join(c for c in folded if not unicodedata.combining(c))
    pattern, intended = _PILOT_EVIDENCE_RULES[slug]
    found = re.search(pattern, folded)
    suggestion = intended if found else 'unknown'
    scope = 'group_general' if slug == 'alfaguara' else 'publisher_specific'
    return {
        'publisher_slug': slug, 'source_url': source_url,
        'checked_at': checked_at, 'detected': bool(found),
        'suggestion': suggestion, 'scope': scope,
        'manual_review_required': True, 'publish': False,
        # Only a matching phrase is retained; no email/contact information.
        'matching_fragment': visible[found.start():found.end()][:180] if found else '',
        'reason': 'Explicit known-page pattern' if found else 'No matching explicit statement',
    }
