#!/usr/bin/env python3
"""Global HTML referential-integrity and page-contract audit.

Covers gaps that link/status/browser smoke tests do not reliably catch:
- duplicate DOM ids;
- broken same-site fragment links (including cross-page anchors);
- <label for> references to missing ids;
- target=_blank links without noopener/noreferrer;
- minimum structural contract for every public HTML route in content-registry:
  lang=es, viewport, exactly one <main>, exactly one <h1>, canonical matching
  the registry URL, and og:url consistency when present.

Standard library only. Designed to scan the full tracked site quickly.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://davidportodiaz.com"

SKIP_PREFIXES = (
    "node_modules/",
    "tests/",
    "lab/",
    ".preview-dist",
    "dist/",
    "WEB DAVID PORTO nuevas ideas/",
)
SKIP_FILES = {"404.html", "offline.html"}

ID_RE = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']', re.I)
HREF_TAG_RE = re.compile(r'<a\b[^>]*\bhref\s*=\s*["\']([^"\']*)["\'][^>]*>', re.I)
LABEL_RE = re.compile(r'<label\b[^>]*\bfor\s*=\s*["\']([^"\']+)["\'][^>]*>', re.I)
CANON_RE = re.compile(r'<link\b[^>]*\brel\s*=\s*["\'][^"\']*\bcanonical\b[^"\']*["\'][^>]*>', re.I)
OG_URL_RE = re.compile(r'<meta\b[^>]*\bproperty\s*=\s*["\']og:url["\'][^>]*>', re.I)
ATTR_HREF_RE = re.compile(r'\bhref\s*=\s*["\']([^"\']+)["\']', re.I)
ATTR_CONTENT_RE = re.compile(r'\bcontent\s*=\s*["\']([^"\']+)["\']', re.I)

def tracked_html() -> list[str]:
    out = subprocess.check_output(["git", "ls-files", "*.html"], cwd=ROOT, text=True)
    files = []
    for raw in out.splitlines():
        path = raw.strip().replace("\\", "/")
        if not path or path in SKIP_FILES or path.endswith((".example.html", ".template.html", ".component.html")):
            continue
        if path.startswith(SKIP_PREFIXES):
            continue
        files.append(path)
    return sorted(files)

def route_for_file(path: str) -> str:
    if path == "index.html":
        return "/"
    if path.endswith("/index.html"):
        return "/" + path[:-len("index.html")]
    return "/" + path

def get_attr(tag: str, name: str) -> str:
    m = re.search(rf'\b{re.escape(name)}\s*=\s*["\']([^"\']*)["\']', tag, re.I)
    return html.unescape(m.group(1).strip()) if m else ""

def canonical_of(source: str) -> str:
    m = CANON_RE.search(source)
    return get_attr(m.group(0), "href") if m else ""

def og_url_of(source: str) -> str:
    m = OG_URL_RE.search(source)
    return get_attr(m.group(0), "content") if m else ""

def normalize_expected_url(route: str) -> str:
    return ORIGIN + (route if route.startswith("/") else "/" + route)

def load_registry() -> tuple[list[dict], dict[str, str]]:
    raw = json.loads((ROOT / "data/content-registry.json").read_text(encoding="utf-8"))
    defaults = raw.get("defaults", {})
    entries = [{**defaults, **x} for x in raw.get("entries", [])]
    public = [
        x for x in entries
        if x.get("status") == "public"
        and isinstance(x.get("sourceFile"), str)
        and x["sourceFile"].endswith(".html")
    ]
    route_to_file = {}
    for x in public:
        route = x.get("url")
        if isinstance(route, str) and route.startswith("/"):
            route_to_file[route] = x["sourceFile"]
            if route != "/" and route.endswith("/"):
                route_to_file[route[:-1]] = x["sourceFile"]
    return public, route_to_file

def resolve_target(source_file: str, href: str, route_to_file: dict[str, str], file_routes: dict[str, str]) -> tuple[str | None, str | None]:
    href = html.unescape(href.strip())
    if "#" not in href or href.startswith(("mailto:", "tel:", "javascript:", "data:")):
        return None, None
    base, fragment = href.split("#", 1)
    if not fragment:
        return None, None
    fragment = unquote(fragment)
    if not base:
        return source_file, fragment
    absolute = urljoin(ORIGIN + route_for_file(source_file), base)
    parsed = urlparse(absolute)
    if f"{parsed.scheme}://{parsed.netloc}" != ORIGIN:
        return None, None
    target_route = parsed.path or "/"
    target = route_to_file.get(target_route)
    if not target:
        target = file_routes.get(target_route) or file_routes.get(target_route.rstrip("/"))
    return target, fragment

def main() -> int:
    errors: list[str] = []
    files = tracked_html()
    sources = {p: (ROOT / p).read_text(encoding="utf-8", errors="replace") for p in files}
    ids = {p: set(ID_RE.findall(s)) for p, s in sources.items()}
    file_routes: dict[str, str] = {}
    for p in files:
        route = route_for_file(p)
        file_routes[route] = p
        if route != "/" and route.endswith("/"):
            file_routes[route[:-1]] = p

    public, route_to_file = load_registry()

    # Global referential checks.
    for path, source in sources.items():
        all_ids = ID_RE.findall(source)
        for ident, count in Counter(all_ids).items():
            if count > 1:
                errors.append(f"{path}: duplicate id #{ident} ({count} occurrences)")

        for m in LABEL_RE.finditer(source):
            ident = html.unescape(m.group(1).strip())
            if ident and ident not in ids[path]:
                errors.append(f"{path}: <label for=\"{ident}\"> points to missing id")

        for m in HREF_TAG_RE.finditer(source):
            tag = m.group(0)
            href = html.unescape(m.group(1).strip())
            if re.search(r'\btarget\s*=\s*["\']_blank["\']', tag, re.I):
                rel = get_attr(tag, "rel").lower().split()
                if "noopener" not in rel or "noreferrer" not in rel:
                    errors.append(f"{path}: target=_blank missing noopener/noreferrer -> {href}")

            target, fragment = resolve_target(path, href, route_to_file, file_routes)
            if target and fragment:
                if target not in ids:
                    # Missing pages are owned by check-internal-graph.py.
                    continue
                if fragment not in ids[target]:
                    errors.append(f"{path}: broken fragment {href} -> {target}#{fragment}")

    # Public page homogeneity contract.
    seen_public_files: set[str] = set()
    for entry in public:
        path = entry["sourceFile"]
        if path in seen_public_files:
            continue
        seen_public_files.add(path)
        source = sources.get(path)
        if source is None:
            errors.append(f"registry public source missing from tracked HTML: {path}")
            continue

        lang = re.search(r'<html\b[^>]*\blang\s*=\s*["\']([^"\']+)["\']', source, re.I)
        if not lang or not lang.group(1).lower().startswith("es"):
            errors.append(f"{path}: public page missing lang=es")

        if not re.search(r'<meta\b[^>]*\bname\s*=\s*["\']viewport["\'][^>]*>', source, re.I):
            errors.append(f"{path}: public page missing viewport meta")

        main_count = len(re.findall(r'<main\b', source, re.I))
        if main_count != 1:
            errors.append(f"{path}: expected exactly one <main>, found {main_count}")

        h1_count = len(re.findall(r'<h1\b', source, re.I))
        if h1_count != 1:
            errors.append(f"{path}: expected exactly one <h1>, found {h1_count}")

        canonical = canonical_of(source)
        expected = normalize_expected_url(entry["url"])
        if canonical != expected:
            errors.append(f"{path}: canonical mismatch {canonical!r} != {expected!r}")

        og_url = og_url_of(source)
        if og_url and og_url != canonical:
            errors.append(f"{path}: og:url {og_url!r} != canonical {canonical!r}")

    if errors:
        print(f"FAIL html reference integrity: {len(errors)} issue(s)")
        for issue in errors[:300]:
            print(" -", issue)
        if len(errors) > 300:
            print(f" - ... and {len(errors)-300} more")
        return 1

    print(
        "PASS html reference integrity: "
        f"{len(files)} tracked HTML files; {len(seen_public_files)} public registry pages"
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
