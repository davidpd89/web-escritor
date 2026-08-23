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
import re
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
CANONICAL_EXPLORE_TERRITORIES = ["works-hub", "author", "notebook-hub", "tools-hub", "press"]
REQUIRED_WORK_IDS = ("work-manecillas", "work-samuel")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL: cannot read {path.relative_to(ROOT)}: {exc}") from exc


def normalize_public_url(value: str) -> str:
    parsed = urlparse(value)
    return parsed.path or "/"


def hrefs_in(source: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(
            r"<a\b[^>]*\bhref\s*=\s*['\"]([^'\"]+)['\"]",
            source,
            re.I,
        )
    ]


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

    # Explorar representa exactamente cinco territorios estables. Las obras
    # individuales son destinos de contenido dentro del territorio Obras, no
    # territorios paralelos. Su acceso directo se preserva en el footer global
    # y su jerarquía/rastreabilidad se comprueba contra registry + /libros/.
    explore_territory_ids = [item.get("id", "") for item in nav.get("exploreTerritories", [])]
    if explore_territory_ids != CANONICAL_EXPLORE_TERRITORIES:
        errors.append(
            "exploreTerritories must be exactly the 5 stable territories "
            f"{CANONICAL_EXPLORE_TERRITORIES} in that order; got {explore_territory_ids}"
        )

    forbidden_found = set(REQUIRED_WORK_IDS) & set(explore_territory_ids)
    if forbidden_found:
        errors.append(
            f"exploreTerritories reintroduces individual works as top-level territories: {sorted(forbidden_found)} "
            "-- individual works belong under works-hub, not as their own Explorar territory"
        )

    works_hub = by_id.get("works-hub")
    if not works_hub:
        errors.append("works-hub missing from registry")
    else:
        if works_hub.get("url") != "/libros/":
            errors.append(f"works-hub canonical URL must be /libros/, got {works_hub.get('url')!r}")
        if works_hub.get("status") != "public":
            errors.append("works-hub must remain public")
        if works_hub.get("discoverability") != "primary":
            errors.append("works-hub must remain primary")
        if works_hub.get("parentId") != "home" or works_hub.get("hubId") != "works-hub":
            errors.append("works-hub hierarchy drift")

    required_work_urls: list[str] = []
    for work_id in REQUIRED_WORK_IDS:
        item = by_id.get(work_id)
        if not item:
            errors.append(f"required work missing from registry: {work_id}")
            continue
        required_work_urls.append(item["url"])
        if item.get("status") != "public":
            errors.append(f"{work_id}: required work must remain public")
        if item.get("type") != "work" or item.get("territory") != "obras":
            errors.append(f"{work_id}: required work must remain classified in Obras")
        if item.get("parentId") != "works-hub" or item.get("hubId") != "works-hub":
            errors.append(f"{work_id}: required work must remain a child of works-hub")
        if item.get("discoverability") != "secondary":
            errors.append(f"{work_id}: required work must remain a secondary destination inside Obras")
        if item.get("searchIndex") is not True or item.get("sitemap") is not True:
            errors.append(f"{work_id}: required work must remain indexable and in sitemap")
        if item["url"] not in sitemap_urls:
            errors.append(f"{work_id}: canonical URL missing from sitemap: {item['url']}")

    footer_obras = nav.get("footer", {}).get("Obra", [])
    for work_id in REQUIRED_WORK_IDS:
        if work_id not in footer_obras:
            errors.append(f"footer.Obra must keep direct canonical access to {work_id}")

    if works_hub and works_hub.get("sourceFile"):
        works_source = ROOT / works_hub["sourceFile"]
        if works_source.is_file():
            works_html = works_source.read_text(encoding="utf-8", errors="replace")
            main_match = re.search(r"<main\b[\s\S]*?</main>", works_html, re.I)
            main_hrefs = {
                normalize_public_url(href)
                for href in hrefs_in(main_match.group(0) if main_match else "")
                if not urlparse(href).netloc or urlparse(href).netloc == "davidportodiaz.com"
            }
            missing_works = sorted(set(required_work_urls) - main_hrefs)
            if missing_works:
                errors.append("works-hub main content missing direct canonical work links: " + ", ".join(missing_works))
        else:
            errors.append(f"works-hub sourceFile does not exist: {works_hub['sourceFile']}")

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
