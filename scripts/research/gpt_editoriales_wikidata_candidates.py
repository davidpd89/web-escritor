#!/usr/bin/env python3
"""Read-only Wikidata publisher candidate adapter; NEVER publish/mutate directories.

Input is an explicitly supplied, already-authorized Wikibase JSON snapshot
(Special:EntityData/Qxxx.json or wbgetentities). No network client or secrets.
Candidates contain only entity identity and possible official website, NOT
contact emails or manuscript status. Review matching against existing slugs.
Wikidata structured statements are CC0; official websites must be checked live
and separately for ownership/control before acceptance.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

QID = re.compile(r"Q[1-9][0-9]*\Z")
IGNORED_HOSTS = {"localhost"}
PROPERTIES = {"website": "P856", "parent": "P749", "country": "P17", "class": "P31"}


def clean_key(raw: object) -> str:
    if not isinstance(raw, str):
        return ""
    folded = unicodedata.normalize("NFKD", raw.casefold())
    return " ".join(re.findall(r"[a-z0-9]+",
                               "".join(c for c in folded if not unicodedata.combining(c))))


def safe_website(url: object) -> str | None:
    if not isinstance(url, str) or any(ord(c) < 32 for c in url):
        return None
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        if parsed.scheme != "https" or not host or parsed.username or parsed.password:
            return None
        if parsed.port not in (None, 443) or parsed.fragment or host in IGNORED_HOSTS:
            return None
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*[a-z0-9]", host, flags=re.I):
            return None
        if "." not in host or ".." in host or host.endswith((".local", ".internal", ".test", ".invalid", ".example")):
            return None
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            return None
        return url
    except ValueError:
        return None


def _statements(entity: dict, prop: str) -> list[dict]:
    claims = entity.get("claims") or {}
    rows = claims.get(prop, [])
    if not isinstance(rows, list):
        return []
    valid = [row for row in rows if isinstance(row, dict)
             and row.get("rank") != "deprecated"
             and isinstance(row.get("mainsnak"), dict)
             and row["mainsnak"].get("snaktype") == "value"]
    preferred = [row for row in valid if row.get("rank") == "preferred"]
    return preferred if preferred else valid


def _values(entity: dict, prop: str) -> list[object]:
    vals = []
    for row in _statements(entity, prop):
        value = (row["mainsnak"].get("datavalue") or {}).get("value")
        if value is not None:
            vals.append(value)
    return vals


def _qids(entity: dict, prop: str) -> list[str]:
    found = []
    for value in _values(entity, prop):
        if isinstance(value, dict):
            ident = value.get("id")
            if isinstance(ident, str) and QID.fullmatch(ident) and ident not in found:
                found.append(ident)
    return found


def _label(entity: dict) -> str | None:
    labels = entity.get("labels") or {}
    for lang in ("es", "en"):
        record = labels.get(lang) or {}
        value = record.get("value") if isinstance(record, dict) else None
        if isinstance(value, str) and 2 <= len(value.strip()) <= 120:
            return value.strip()
    return None


def candidates(snapshot: dict, directory: dict) -> dict:
    """Interpret only explicitly provided entities; suggest identity, never auto-merge."""
    entities = snapshot.get("entities")
    rows = directory.get("publishers")
    if not isinstance(entities, dict) or not isinstance(rows, list):
        raise ValueError("Expected Wikibase entities and directory publishers")
    name_index: dict[str, list[str]] = {}
    host_index: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("slug"), str):
            raise ValueError("Directory record lacks slug")
        key = clean_key(row.get("name"))
        if key:
            name_index.setdefault(key, []).append(row["slug"])
        website = safe_website(row.get("website_url"))
        if website:
            host_index.setdefault(urlsplit(website).hostname or "", []).append(row["slug"])
    result = []
    rejected = []
    for key, item in sorted(entities.items()):
        if not QID.fullmatch(key) or not isinstance(item, dict) or item.get("id") != key:
            rejected.append(str(key))
            continue
        label = _label(item)
        if not label:
            rejected.append(key)
            continue
        websites = sorted(set(filter(None, (safe_website(v) for v in _values(item, PROPERTIES["website"])))) )
        raw_websites = _values(item, PROPERTIES["website"])
        refs = set(name_index.get(clean_key(label), []))
        for website in websites:
            refs.update(host_index.get(urlsplit(website).hostname or "", []))
        result.append({
            "wikidata_id": key,
            "label": label,
            "aliases": [s.get("value") for s in (item.get("aliases") or {}).get("es", [])
                        if isinstance(s, dict) and isinstance(s.get("value"), str)
                        and len(s["value"]) <= 120][:8],
            "identity_source": f"https://www.wikidata.org/wiki/{key}",
            "website_candidates": websites[:5],
            "has_invalid_or_unusable_website_claims": len(raw_websites) != len(websites),
            "possible_existing_slugs": sorted(refs),
            "parent_qids": _qids(item, PROPERTIES["parent"]),
            "country_qids": _qids(item, PROPERTIES["country"]),
            "class_qids": _qids(item, PROPERTIES["class"]),
            "manual_review_required": True,
            "contact_publication_authorized": False,
            "manuscript_status": "not_inferred",
        })
    return {"schema_version": 1, "source": "wikidata_cc0_offline",
            "data_license": "CC0-1.0",
            "entities_checked": len(entities),
            "candidates": result,
            "rejected_ids": rejected,
            "writes_to_public_catalogue": False}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", required=True, type=Path,
                   help="Manually exported/supplied Wikibase JSON snapshot")
    p.add_argument("--directory", required=True, type=Path,
                   help="Existing data/editoriales.json (read-only)")
    args = p.parse_args(argv)
    try:
        with args.snapshot.open(encoding="utf-8") as h:
            snapshot = json.load(h)
        with args.directory.open(encoding="utf-8") as h:
            directory = json.load(h)
        report = candidates(snapshot, directory)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Invalid or absent offline inputs: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
