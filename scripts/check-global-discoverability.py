#!/usr/bin/env python3
"""Global public-content discoverability and shell contract.

The public registry answers what exists, sitemap.xml answers what search engines
receive, and authored V1 HTML remains the normal runtime shell. Purpose-built
machine/print surfaces may use a documented minimal shell; this checker records
those exceptions instead of silently forcing them into the general template.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://davidportodiaz.com"
OUT = ROOT / "artifacts" / "global-discoverability" / "inventory.json"

INTERNAL_PREFIXES = ("publicar-web/", "lecturas/", "herramientas/auditor-web/")
LAB_PREFIXES = ("lab/",)
GATED_PREFIXES = ("donde-empieza-la-jaula/",)
GENERATED_ROUTE_PREFIXES = (
    "editoriales/duermevela-ediciones/",
    "editoriales/minotauro/",
    "editoriales/nocturna-ediciones/",
    "cuaderno/temas/",
)
MINIMAL_SHELL_EXCEPTIONS = {
    "ai/index.html": "machine-readable authority surface with intentional minimal navigation",
    "clubes-de-lectura/samuel-entre-mundos/guia-imprimible/index.html": "print-first public utility with intentional minimal shell",
}
EXPECTED_HEADER = ["/libros/", "/cuaderno/", "/herramientas/"]
EXPECTED_EXPLORE_TERRITORY_IDS = [
    "works-hub",
    "author",
    "notebook-hub",
    "tools-hub",
    "press",
]
REQUIRED_WORK_IDS = ("work-manecillas", "work-samuel")
LEGAL_PUBLIC_NOINDEX = {"/privacidad.html", "/aviso-legal.html"}


def tracked_files() -> list[str]:
    output = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    return [line.strip() for line in output.splitlines() if line.strip()]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def canonical(html: str) -> str:
    for tag in re.findall(r"<link\b[^>]*>", html, re.I):
        if re.search(r"\brel\s*=\s*['\"]canonical['\"]", tag, re.I):
            match = re.search(r"\bhref\s*=\s*['\"]([^'\"]+)['\"]", tag, re.I)
            return match.group(1).strip() if match else ""
    return ""


def robots(html: str) -> str:
    for tag in re.findall(r"<meta\b[^>]*>", html, re.I):
        if re.search(r"\bname\s*=\s*['\"]robots['\"]", tag, re.I):
            match = re.search(r"\bcontent\s*=\s*['\"]([^'\"]+)['\"]", tag, re.I)
            return match.group(1).lower().replace(" ", "") if match else ""
    return ""


def route_for_file(path: str) -> str:
    if path == "index.html":
        return "/"
    if path.endswith("/index.html"):
        return "/" + path[: -len("index.html")]
    return "/" + path


def classify(path: str, html: str) -> str:
    if path.startswith("data/"):
        return "GENERATED"
    if path.startswith(LAB_PREFIXES):
        return "LAB"
    if path.startswith(GATED_PREFIXES):
        return "GATED"
    if path.startswith(INTERNAL_PREFIXES):
        return "PRIVATE/INTERNAL"
    if path == "404.html":
        return "404"
    if path == "offline.html":
        return "PUBLIC_UTILITY"
    if path == "samuel-entre-mundos.html":
        return "REDIRECT"
    if "noindex" in robots(html):
        return "PUBLIC_NOINDEX"
    return "PUBLIC_INDEXABLE"


def hrefs_in(source: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"<a\b[^>]*\bhref\s*=\s*['\"]([^'\"]+)['\"]", source, re.I)]


def normalize_local_href(value: str) -> str | None:
    value = value.strip()
    if not value or value.startswith("#") or re.match(r"^(?:mailto:|tel:|javascript:|data:)", value, re.I):
        return None
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        if f"{parsed.scheme}://{parsed.netloc}" != ORIGIN:
            return None
        return parsed.path or "/"
    if value.startswith("//"):
        return None
    return parsed.path or "/"


def sitemap_urls() -> set[str]:
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    urls = set()
    for loc in root.findall(".//sm:loc", namespace):
        if not loc.text:
            continue
        parsed = urlparse(loc.text.strip())
        if f"{parsed.scheme}://{parsed.netloc}" != ORIGIN:
            raise AssertionError(f"external canonical in sitemap: {loc.text.strip()}")
        urls.add(parsed.path or "/")
    return urls


def load_registry() -> tuple[list[dict], dict[str, dict]]:
    raw = json.loads((ROOT / "data/content-registry.json").read_text(encoding="utf-8"))
    defaults = raw.get("defaults", {})
    entries = [{**defaults, **item} for item in raw.get("entries", [])]
    return entries, {item["id"]: item for item in entries}


def main() -> int:
    errors: list[str] = []
    tracked = tracked_files()
    html_files = [path for path in tracked if path.endswith(".html")]
    inventory = []

    for path in html_files:
        html = read(path)
        classification = classify(path, html)
        inventory.append({
            "path": path,
            "route": route_for_file(path),
            "classification": classification,
            "robots": robots(html),
            "canonical": canonical(html),
            "generatedRoute": path.startswith(GENERATED_ROUTE_PREFIXES),
            "minimalShellReason": MINIMAL_SHELL_EXCEPTIONS.get(path),
            "v1": bool(re.search(r"<html\b[^>]*class=['\"][^'\"]*\bv1\b", html, re.I)),
            "hasHeader": "site-header" in html,
            "hasFooter": "site-footer" in html,
            "hasSkip": "skip-link" in html,
            "hasExplore": "data-explore-dialog" in html,
        })

    counts = Counter(item["classification"] for item in inventory)
    sitemap = sitemap_urls()
    entries, by_id = load_registry()
    registry_sitemap = {
        item["url"]
        for item in entries
        if item.get("status") == "public" and item.get("sitemap") is True
    }
    if sitemap != registry_sitemap:
        errors.append(
            "sitemap/registry drift: "
            f"sitemap-only={sorted(sitemap - registry_sitemap)} "
            f"registry-only={sorted(registry_sitemap - sitemap)}"
        )

    indexable_canonicals = set()
    for item in inventory:
        if item["classification"] != "PUBLIC_INDEXABLE":
            continue
        value = item["canonical"]
        if not value:
            errors.append(f"{item['path']}: indexable HTML lacks canonical")
            continue
        parsed = urlparse(value)
        if f"{parsed.scheme}://{parsed.netloc}" == ORIGIN:
            indexable_canonicals.add(parsed.path or "/")
    if indexable_canonicals != sitemap:
        errors.append(
            "tracked indexable HTML/sitemap drift: "
            f"html-only={sorted(indexable_canonicals - sitemap)} "
            f"sitemap-only={sorted(sitemap - indexable_canonicals)}"
        )

    map_html = read("mapa-del-sitio/index.html")
    main_match = re.search(r"<main\b[\s\S]*?</main>", map_html, re.I)
    map_hrefs = {normalize_local_href(href) for href in hrefs_in(main_match.group(0) if main_match else "")}
    map_hrefs.discard(None)
    required_map = sitemap | LEGAL_PUBLIC_NOINDEX
    missing_map = sorted(required_map - map_hrefs)
    if missing_map:
        errors.append("site map missing public human routes: " + ", ".join(missing_map))
    for forbidden in ("/donde-empieza-la-jaula/", "/lecturas/", "/publicar-web/", "/herramientas/auditor-web/"):
        if forbidden in map_hrefs:
            errors.append(f"site map exposes non-public route: {forbidden}")

    navigation = json.loads((ROOT / "data/navigation.json").read_text(encoding="utf-8"))
    nav_header = []
    for item_id in navigation.get("header", []):
        item = by_id.get(item_id)
        if not item:
            errors.append(f"navigation header unknown id: {item_id}")
            continue
        nav_header.append(item["url"])
    if nav_header != EXPECTED_HEADER:
        errors.append(f"navigation header contract is {nav_header}, expected runtime {EXPECTED_HEADER}")
    if navigation.get("runtimeOwnership", {}).get("shell") != "authored-static-v1-html":
        errors.append("navigation runtime ownership is not documented")

    # Explorar owns five stable top-level territories. Individual books are
    # not promoted to territory status; their findability is guaranteed by
    # the Obras hierarchy + direct static links in the Obras hub and global
    # footer. This keeps one semantic IA instead of duplicating a second menu.
    territory_ids = [item.get("id") for item in navigation.get("exploreTerritories", [])]
    if territory_ids != EXPECTED_EXPLORE_TERRITORY_IDS:
        errors.append(
            "navigation Explore territories drift: "
            f"{territory_ids}, expected {EXPECTED_EXPLORE_TERRITORY_IDS}"
        )

    territory_urls: list[str] = []
    for item_id in EXPECTED_EXPLORE_TERRITORY_IDS:
        item = by_id.get(item_id)
        if not item:
            errors.append(f"Explore territory missing from registry: {item_id}")
            continue
        if item.get("status") != "public":
            errors.append(f"Explore territory is not public: {item_id}")
        territory_urls.append(item["url"])

    works_hub = by_id.get("works-hub")
    required_work_urls: list[str] = []
    if not works_hub:
        errors.append("works-hub missing from registry")
    else:
        if works_hub.get("url") != "/libros/":
            errors.append(f"works-hub canonical URL drift: {works_hub.get('url')}")
        if works_hub.get("status") != "public" or works_hub.get("discoverability") != "primary":
            errors.append("works-hub must remain a public primary destination")

    for work_id in REQUIRED_WORK_IDS:
        work = by_id.get(work_id)
        if not work:
            errors.append(f"required work missing from registry: {work_id}")
            continue
        required_work_urls.append(work["url"])
        if work.get("status") != "public":
            errors.append(f"{work_id}: required work is not public")
        if work.get("type") != "work" or work.get("territory") != "obras":
            errors.append(f"{work_id}: required work is not classified inside Obras")
        if work.get("parentId") != "works-hub" or work.get("hubId") != "works-hub":
            errors.append(f"{work_id}: required work is not a child of works-hub")
        if work.get("searchIndex") is not True or work.get("sitemap") is not True:
            errors.append(f"{work_id}: required work must remain indexable and in sitemap")
        if work["url"] not in sitemap:
            errors.append(f"{work_id}: canonical work URL missing from sitemap: {work['url']}")

    footer_work_ids = navigation.get("footer", {}).get("Obra", [])
    for work_id in REQUIRED_WORK_IDS:
        if work_id not in footer_work_ids:
            errors.append(f"footer.Obra must keep direct access to {work_id}")

    if works_hub and works_hub.get("sourceFile") in tracked:
        works_html = read(works_hub["sourceFile"])
        works_main = re.search(r"<main\b[\s\S]*?</main>", works_html, re.I)
        works_main_hrefs = {
            normalize_local_href(href)
            for href in hrefs_in(works_main.group(0) if works_main else "")
        }
        works_main_hrefs.discard(None)
        missing_work_links = sorted(set(required_work_urls) - works_main_hrefs)
        if missing_work_links:
            errors.append("works-hub main content missing direct work links: " + ", ".join(missing_work_links))
    elif works_hub:
        errors.append(f"works-hub source missing from git: {works_hub.get('sourceFile')}")

    missing_work_map = sorted(set(required_work_urls) - map_hrefs)
    if missing_work_map:
        errors.append("site map missing canonical works: " + ", ".join(missing_work_map))

    registry_sources = {
        item["sourceFile"]
        for item in entries
        if item.get("status") == "public"
        and item.get("sitemap") is True
        and item.get("sourceFile", "").endswith(".html")
    }
    shell_sources = sorted(registry_sources | {"privacidad.html", "aviso-legal.html", "404.html"})
    for path in shell_sources:
        if path not in tracked:
            errors.append(f"shell source missing from git: {path}")
            continue
        if path in MINIMAL_SHELL_EXCEPTIONS:
            continue
        html = read(path)
        for token, label in (("skip-link", "skip link"), ("site-header", "V1 header"), ("site-footer", "V1 footer"), ("data-explore-dialog", "Explore dialog")):
            if token not in html:
                errors.append(f"{path}: missing {label}")
        nav_match = re.search(r"<nav\b[^>]*class=['\"][^'\"]*primary-nav[^'\"]*['\"][^>]*>([\s\S]*?)</nav>", html, re.I)
        if nav_match:
            actual = [normalize_local_href(href) for href in hrefs_in(nav_match.group(1))]
            actual = [href for href in actual if href]
            if actual != EXPECTED_HEADER:
                errors.append(f"{path}: primary nav drift {actual}")
        else:
            errors.append(f"{path}: primary nav missing")

        explore_match = re.search(r"<nav\b[^>]*class=['\"][^'\"]*explore-list[^'\"]*['\"][^>]*>([\s\S]*?)</nav>", html, re.I)
        if explore_match:
            actual_explore = [normalize_local_href(href) for href in hrefs_in(explore_match.group(1))]
            actual_explore = [href for href in actual_explore if href]
            actual_territories = actual_explore[: len(territory_urls)]
            if actual_territories != territory_urls:
                errors.append(
                    f"{path}: Explore top-level territories drift {actual_territories}; "
                    f"expected {territory_urls}"
                )
            promoted_works = sorted(set(required_work_urls) & set(actual_territories))
            if promoted_works:
                errors.append(f"{path}: individual works promoted to top-level Explore territories {promoted_works}")
        else:
            errors.append(f"{path}: Explore list missing")

        footer_match = re.search(
            r"<nav\b[^>]*aria-label=['\"]Obra['\"][^>]*>([\s\S]*?)</nav>",
            html,
            re.I,
        )
        if footer_match:
            footer_hrefs = {
                normalize_local_href(href)
                for href in hrefs_in(footer_match.group(1))
            }
            footer_hrefs.discard(None)
            missing_footer_works = sorted(set(required_work_urls) - footer_hrefs)
            if missing_footer_works:
                errors.append(
                    f"{path}: global Obra footer missing direct canonical works {missing_footer_works}"
                )
        else:
            errors.append(f"{path}: global Obra footer missing")

    shell_js = read("assets/v1-shell.js")
    for token in ("showModal()", "data-explore-close", "opener", "/asistente/"):
        if token not in shell_js:
            errors.append(f"v1-shell.js missing Explore contract token: {token}")

    page404 = read("404.html")
    for route in ("/", "/libros/", "/cuaderno/", "/herramientas/", "/mapa-del-sitio/"):
        if f'href="{route}"' not in page404 and f"href='{route}'" not in page404:
            errors.append(f"404 rescue missing: {route}")
    if "noindex" not in robots(page404):
        errors.append("404 must remain noindex")

    robots_txt = read("robots.txt")
    if "Sitemap: https://davidportodiaz.com/sitemap.xml" not in robots_txt:
        errors.append("robots.txt lacks canonical sitemap declaration")
    disallows = [
        line.split(":", 1)[1].strip()
        for line in robots_txt.splitlines()
        if line.strip().lower().startswith("disallow:") and line.split(":", 1)[1].strip()
    ]
    for route in sorted(sitemap):
        for rule in disallows:
            prefix = rule.rstrip("*")
            if prefix == "/" or (prefix and route.startswith(prefix)):
                errors.append(f"robots.txt may block indexable route {route} via {rule}")

    for machine in ("llms.txt", "llms-full.txt", "humans.txt", "ai/index.html"):
        if machine not in tracked:
            errors.append(f"machine-readability surface missing: {machine}")
    authority_text = "\n".join(read(path) for path in ("index.html", "autor.html", "ai/index.html", "llms-full.txt") if (ROOT / path).exists())
    for entity_id in ("#author", "#website", "#book-manecillas", "#book-samuel"):
        if entity_id not in authority_text:
            errors.append(f"canonical entity id not found on authority surfaces: {entity_id}")

    global_search_markers = []
    for path in html_files:
        if path.startswith(("lab/", "asistente/", "data/")):
            continue
        html = read(path).lower()
        if "pagefind-ui" in html or "data-pagefind" in html:
            global_search_markers.append(path)
    search_state = "IMPLEMENTADO" if global_search_markers else "POSPUESTO"
    if search_state == "POSPUESTO" and re.search(r"buscar (?:en|por) (?:la )?web", page404, re.I):
        errors.append("404 references a global search UI that is not implemented")

    styles_consumers = [path for path in html_files if re.search(r"href=['\"]/styles\.css(?:\?|['\"])", read(path), re.I)]
    script_consumers = [path for path in html_files if re.search(r"src=['\"]/script\.js(?:\?|['\"])", read(path), re.I)]
    legacy = {
        "styles.css": {"classification": "ACTIVE_TRANSITIONAL" if styles_consumers else "UNUSED_PROVEN", "consumers": styles_consumers},
        "styles.min.css": {"classification": "ACTIVE_TRANSITIONAL" if "styles.min.css" in tracked else "UNUSED_PROVEN", "consumers": []},
        "script.js": {"classification": "ACTIVE_REQUIRED" if script_consumers else "UNUSED_PROVEN", "consumers": script_consumers},
    }

    report = {
        "schemaVersion": 1,
        "inventorySource": "git ls-files + robots/canonical + content-registry + sitemap",
        "counts": dict(sorted(counts.items())),
        "routes": inventory,
        "minimalShellExceptions": MINIMAL_SHELL_EXCEPTIONS,
        "sitemapCount": len(sitemap),
        "registrySitemapCount": len(registry_sitemap),
        "mapHumanRouteCount": len(map_hrefs),
        "searchState": search_state,
        "searchMarkers": global_search_markers,
        "legacy": legacy,
        "robotsDisallowRules": disallows,
        "errors": errors,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        print(f"FAIL: global discoverability has {len(errors)} issue(s)")
        for issue in errors:
            print(" -", issue)
        print(f"Inventory: {OUT.relative_to(ROOT)}")
        return 1

    print(
        "PASS: global discoverability "
        f"({len(inventory)} tracked HTML artifacts; {len(sitemap)} indexable; "
        f"search={search_state}; map={len(map_hrefs)} human destinations)"
    )
    print(f"Inventory: {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())