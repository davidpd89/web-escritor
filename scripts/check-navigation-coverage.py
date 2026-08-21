#!/usr/bin/env python3
"""Validate canonical navigation coverage against the public site.

Run from the repository root:
    python scripts/check-navigation-coverage.py

The registry answers «what exists». navigation.json answers «what is shown».
This checker prevents public routes/tools from becoming orphaned and prevents
non-public content from leaking into navigation/search surfaces.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "content-registry.json"
NAV_PATH = ROOT / "data" / "navigation.json"
SITEMAP_PATH = ROOT / "sitemap.xml"
TOOLS_PATH = ROOT / "data" / "tools-hub.json"

ALLOWED_STATUS = {"public", "gated", "noindex", "internal", "deprecated"}
ALLOWED_DISCOVERABILITY = {"primary", "secondary", "contextual", "search-only", "sitemap-only"}
REQUIRED_EFFECTIVE_FIELDS = {
    "id", "url", "label", "shortLabel", "type", "territory", "parentId",
    "hubId", "status", "discoverability", "searchIndex", "sitemap",
    "footerEligible", "audience", "jobs", "relatedIds", "sourceFile", "aliases",
}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL: cannot read {path.relative_to(ROOT)}: {exc}") from exc


def normalize_public_url(value: str) -> str:
    parsed = urlparse(value)
    return parsed.path or "/"


def navigation_refs(nav: dict) -> list[tuple[str, str]]:
    refs: list[tuple[str, str]] = []

    for item_id in nav.get("header", []):
        refs.append(("header", item_id))

    for item in nav.get("exploreTerritories", []):
        refs.append(("exploreTerritories.id", item.get("id", "")))
        refs.append(("exploreTerritories.previewId", item.get("previewId", "")))

    for item in nav.get("exploreShortcuts", []):
        refs.append(("exploreShortcuts.targetId", item.get("targetId", "")))

    for item_id in nav.get("exploreUtilities", []):
        refs.append(("exploreUtilities", item_id))

    for group, values in nav.get("footer", {}).items():
        for item_id in values:
            refs.append((f"footer.{group}", item_id))

    for item_id in nav.get("homeMap", []):
        refs.append(("homeMap", item_id))

    for group, values in nav.get("localNavSets", {}).items():
        for item_id in values:
            refs.append((f"localNavSets.{group}", item_id))

    return refs


def main() -> int:
    errors: list[str] = []
    registry_raw = load_json(REGISTRY_PATH)
    nav = load_json(NAV_PATH)
    tools = load_json(TOOLS_PATH)

    defaults = registry_raw.get("defaults", {})
    raw_entries = registry_raw.get("entries")
    if not isinstance(defaults, dict):
        raise SystemExit("FAIL: content-registry defaults must be an object")
    if not isinstance(raw_entries, list):
        raise SystemExit("FAIL: content-registry must contain an entries array")

    entries: list[dict] = []
    for raw in raw_entries:
        if not isinstance(raw, dict):
            errors.append("registry entry must be an object")
            continue
        entries.append({**defaults, **raw})

    by_id: dict[str, dict] = {}
    by_url: dict[str, dict] = {}

    for index, item in enumerate(entries):
        context = f"registry entry #{index + 1}"
        missing = sorted(REQUIRED_EFFECTIVE_FIELDS - set(item))
        if missing:
            errors.append(f"{context}: missing effective fields {', '.join(missing)}")
            continue

        item_id = item["id"]
        url = item["url"]

        if item_id in by_id:
            errors.append(f"duplicate id: {item_id}")
        else:
            by_id[item_id] = item

        if url in by_url:
            errors.append(f"duplicate url: {url}")
        else:
            by_url[url] = item

        if item["status"] not in ALLOWED_STATUS:
            errors.append(f"{item_id}: invalid status {item['status']!r}")
        if item["discoverability"] not in ALLOWED_DISCOVERABILITY:
            errors.append(f"{item_id}: invalid discoverability {item['discoverability']!r}")

        if item["status"] != "public" and (item["searchIndex"] or item["sitemap"]):
            errors.append(f"{item_id}: non-public content cannot be searchIndex/sitemap true")

        if item["status"] == "public" and item["sitemap"] and item_id != "home":
            if not item["parentId"]:
                errors.append(f"{item_id}: public sitemap route has no parentId")
            if not item["hubId"]:
                errors.append(f"{item_id}: public sitemap route has no hubId")

        source = item["sourceFile"]
        if source and not (ROOT / source).is_file():
            errors.append(f"{item_id}: sourceFile does not exist: {source}")

    # Relationships must resolve to canonical IDs.
    for item in entries:
        if "id" not in item:
            continue
        item_id = item["id"]
        for field in ("parentId", "hubId"):
            ref = item.get(field)
            if ref and ref not in by_id:
                errors.append(f"{item_id}: {field} references unknown id {ref}")
        for ref in item.get("relatedIds", []):
            if ref not in by_id:
                errors.append(f"{item_id}: relatedIds references unknown id {ref}")

    # Sitemap ↔ registry is exact for routes declared sitemap=true.
    try:
        root = ET.parse(SITEMAP_PATH).getroot()
    except (OSError, ET.ParseError) as exc:
        raise SystemExit(f"FAIL: cannot parse sitemap.xml: {exc}") from exc

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_urls = {
        normalize_public_url(loc.text.strip())
        for loc in root.findall(".//sm:loc", ns)
        if loc.text and loc.text.strip()
    }
    registry_sitemap_urls = {
        item["url"] for item in entries
        if item.get("status") == "public" and item.get("sitemap") is True
    }

    for url in sorted(sitemap_urls - registry_sitemap_urls):
        errors.append(f"sitemap route missing from registry: {url}")
    for url in sorted(registry_sitemap_urls - sitemap_urls):
        errors.append(f"registry sitemap route missing from sitemap.xml: {url}")

    # Every interactive tool in tools-hub must be classified under tools-hub.
    for tool in tools.get("tools", []):
        href = tool.get("href")
        if not href:
            errors.append(f"tools-hub entry without href: {tool.get('name', '<unnamed>')}")
            continue
        item = by_url.get(href)
        if not item:
            errors.append(f"tools-hub public tool missing from registry: {href}")
            continue
        if item.get("hubId") != "tools-hub":
            errors.append(f"tool not attached to tools-hub: {href}")

    # Every navigation reference resolves to a public canonical entry.
    for surface, ref in navigation_refs(nav):
        if not ref:
            errors.append(f"{surface}: empty registry reference")
            continue
        item = by_id.get(ref)
        if not item:
            errors.append(f"{surface}: unknown registry id {ref}")
            continue
        if item.get("status") != "public":
            errors.append(f"{surface}: non-public registry id exposed: {ref}")

    # Header V1 is intentionally compact and contains only primary territories.
    header = nav.get("header", [])
    if len(header) > 4:
        errors.append(f"header has {len(header)} direct destinations; V1 contract allows 4")
    for ref in header:
        item = by_id.get(ref)
        if item and item.get("discoverability") != "primary":
            errors.append(f"header item is not primary: {ref}")

    # Guard against reintroducing the discarded project name into canonical UI data.
    serialized = (
        json.dumps(registry_raw, ensure_ascii=False) + "\n" +
        json.dumps(nav, ensure_ascii=False)
    ).casefold()
    if "piel" in serialized:
        errors.append("canonical navigation data contains forbidden public token 'PIEL'")

    if errors:
        print(f"FAIL: navigation coverage has {len(errors)} issue(s)")
        for issue in errors:
            print(f" - {issue}")
        return 1

    print(
        "PASS: navigation coverage "
        f"({len(entries)} registry routes, {len(sitemap_urls)} sitemap routes, "
        f"{len(tools.get('tools', []))} interactive tools)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
