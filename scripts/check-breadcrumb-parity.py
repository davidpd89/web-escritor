#!/usr/bin/env python3
"""Audit breadcrumb integrity without forcing one visual pattern sitewide.

A.6 deliberately separates three things:

* human breadcrumb navigation, when a page chooses to render it;
* ``BreadcrumbList`` structured data, when a page chooses to publish it;
* canonical hierarchy, owned by ``data/content-registry.json``.

Google allows multiple breadcrumb trails and does not require the host or the
current page to be listed. It also requires at least two ``ListItem`` objects
when ``BreadcrumbList`` is used. This checker therefore blocks objective
invalidity/drift, but treats visible-only and JSON-LD-only coverage as
informational rather than manufacturing a sitewide rollout requirement.

Run from the repository root:
    python scripts/check-breadcrumb-parity.py
    python scripts/check-breadcrumb-parity.py --json artifacts/breadcrumbs.json
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://davidportodiaz.com"

JSONLD_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)
CANONICAL_TAG_RE = re.compile(r"<link\b[^>]*>", re.I)
NAV_RE = re.compile(r"<nav\b(?P<attrs>[^>]*)>(?P<body>.*?)</nav>", re.I | re.S)
LI_RE = re.compile(r"<li\b(?P<attrs>[^>]*)>(?P<body>.*?)</li>", re.I | re.S)
A_RE = re.compile(r"<a\b(?P<attrs>[^>]*)>(?P<body>.*?)</a>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>", re.S)

VISIBLE_LABEL_TOKENS = (
    "ruta de navegación",
    "ruta de navegacion",
    "ruta de exploración",
    "ruta de exploracion",
    "migas de pan",
    "breadcrumb",
)


def attr_value(attrs: str, name: str) -> str | None:
    match = re.search(
        rf"\b{re.escape(name)}\s*=\s*([\"'])(.*?)\1",
        attrs,
        re.I | re.S,
    )
    return html_lib.unescape(match.group(2)).strip() if match else None


def plain_text(value: str) -> str:
    return " ".join(html_lib.unescape(TAG_RE.sub(" ", value)).split())


def normalize_url(value: str | None) -> tuple[str | None, str | None]:
    """Return ``(local_path, problem)`` for a breadcrumb URL.

    A missing URL can be valid for the final structured item/current page.
    Relative breadcrumb URLs are rejected rather than resolved heuristically:
    canonical public navigation in this repo uses root-relative/absolute URLs.
    """
    if value is None:
        return None, None
    value = value.strip()
    if not value:
        return None, None

    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        if f"{parsed.scheme}://{parsed.netloc}" != ORIGIN:
            return None, f"external breadcrumb URL {value!r}"
        return parsed.path or "/", None

    if value.startswith("//"):
        return None, f"protocol-relative breadcrumb URL {value!r}"
    if not value.startswith("/"):
        return None, f"non-root-relative breadcrumb URL {value!r}"
    return parsed.path or "/", None


def canonical_path(html: str) -> str | None:
    for tag in CANONICAL_TAG_RE.findall(html):
        rel = attr_value(tag, "rel")
        if not rel or "canonical" not in {token.casefold() for token in rel.split()}:
            continue
        href = attr_value(tag, "href")
        path, problem = normalize_url(href)
        return path if not problem else None
    return None


def iter_nodes(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from iter_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_nodes(item)


def type_contains(node: dict, wanted: str) -> bool:
    raw = node.get("@type")
    values = raw if isinstance(raw, list) else [raw]
    return wanted in values


def item_url_value(value) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("@id", "url"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                return candidate
    return None


def extract_jsonld_breadcrumbs(html: str) -> tuple[list[list[dict]], list[str]]:
    trails: list[list[dict]] = []
    parse_errors: list[str] = []

    for block_index, match in enumerate(JSONLD_RE.finditer(html), start=1):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            # Broader JSON-LD QA owns unrelated malformed blocks. A.6 claims
            # malformed data only when the block itself is breadcrumb-shaped.
            if "BreadcrumbList" in raw:
                parse_errors.append(
                    f"breadcrumb JSON-LD block #{block_index} is not parseable: {exc.msg}"
                )
            continue

        for node in iter_nodes(data):
            if not isinstance(node, dict) or not type_contains(node, "BreadcrumbList"):
                continue
            items = node.get("itemListElement")
            if not isinstance(items, list):
                parse_errors.append("BreadcrumbList itemListElement is not an array")
                continue

            trail: list[dict] = []
            for raw_item in items:
                if not isinstance(raw_item, dict):
                    trail.append(
                        {
                            "position": None,
                            "name": "",
                            "raw_url": None,
                            "url": None,
                            "url_problem": None,
                        }
                    )
                    continue

                raw_url = item_url_value(raw_item.get("item"))
                url, problem = normalize_url(raw_url)
                raw_name = raw_item.get("name")
                trail.append(
                    {
                        "position": raw_item.get("position"),
                        "name": plain_text(raw_name if isinstance(raw_name, str) else ""),
                        "raw_url": raw_url,
                        "url": url,
                        "url_problem": problem,
                    }
                )
            trails.append(trail)

    return trails, parse_errors


def is_breadcrumb_nav(attrs: str) -> bool:
    classes = (attr_value(attrs, "class") or "").casefold()
    label = (attr_value(attrs, "aria-label") or "").casefold()
    return "breadcrumb" in classes or any(token in label for token in VISIBLE_LABEL_TOKENS)


def extract_visible_breadcrumbs(html: str) -> list[list[dict]]:
    trails: list[list[dict]] = []

    for nav in NAV_RE.finditer(html):
        attrs = nav.group("attrs")
        if not is_breadcrumb_nav(attrs):
            continue

        items: list[dict] = []
        for li in LI_RE.finditer(nav.group("body")):
            li_attrs = li.group("attrs")
            body = li.group("body")
            anchor = A_RE.search(body)
            href = attr_value(anchor.group("attrs"), "href") if anchor else None
            url, problem = normalize_url(href)
            aria_current = (attr_value(li_attrs, "aria-current") or "").casefold()
            if anchor and not aria_current:
                aria_current = (
                    attr_value(anchor.group("attrs"), "aria-current") or ""
                ).casefold()

            items.append(
                {
                    "position": len(items) + 1,
                    "name": plain_text(body),
                    "raw_url": href,
                    "url": url,
                    "url_problem": problem,
                    "current": aria_current == "page",
                }
            )

        if items:
            trails.append(items)

    return trails


def load_registry(path: Path) -> tuple[list[dict], dict[str, dict]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    defaults = raw.get("defaults", {})
    entries = [{**defaults, **item} for item in raw.get("entries", [])]
    by_url = {item["url"]: item for item in entries if item.get("url")}
    return entries, by_url


def finding(severity: str, code: str, message: str) -> dict:
    return {"severity": severity, "code": code, "message": message}


def validate_trail(
    trail: list[dict],
    *,
    kind: str,
    route_id: str,
    current_url: str,
    by_url: dict[str, dict],
) -> list[dict]:
    findings: list[dict] = []

    if kind == "jsonld":
        # Google Search requires at least two ListItems for BreadcrumbList.
        if len(trail) < 2:
            findings.append(
                finding(
                    "error",
                    "invalid-jsonld",
                    f"{route_id}: BreadcrumbList has {len(trail)} ListItem(s); Google requires at least 2",
                )
            )

        positions = [item.get("position") for item in trail]
        expected = list(range(1, len(trail) + 1))
        if positions != expected:
            findings.append(
                finding(
                    "error",
                    "order-drift",
                    f"{route_id}: BreadcrumbList positions {positions!r}, expected {expected!r}",
                )
            )

    seen_urls: set[str] = set()
    current_indexes: list[int] = []
    current_flags: list[int] = []

    for index, item in enumerate(trail):
        if not item.get("name"):
            findings.append(
                finding(
                    "error",
                    "missing-name",
                    f"{route_id}: {kind} breadcrumb item #{index + 1} has no name",
                )
            )

        # In Google's BreadcrumbList contract, every non-final ListItem needs
        # ``item``. The final item may omit it and inherit the containing page.
        if kind == "jsonld" and index < len(trail) - 1 and not item.get("raw_url"):
            findings.append(
                finding(
                    "error",
                    "missing-item",
                    f"{route_id}: BreadcrumbList item #{index + 1} is not final and has no item URL",
                )
            )

        problem = item.get("url_problem")
        if problem:
            findings.append(finding("error", "url-drift", f"{route_id}: {problem}"))
            continue

        url = item.get("url")
        if url:
            if url in seen_urls:
                findings.append(
                    finding(
                        "error",
                        "order-drift",
                        f"{route_id}: {kind} breadcrumb repeats {url}",
                    )
                )
            seen_urls.add(url)

            if url == current_url:
                current_indexes.append(index)

            registry_item = by_url.get(url)
            if registry_item is None and url != current_url:
                findings.append(
                    finding(
                        "error",
                        "url-drift",
                        f"{route_id}: {kind} breadcrumb points to unknown canonical route {url}",
                    )
                )
            elif registry_item is not None and registry_item.get("status") != "public":
                findings.append(
                    finding(
                        "error",
                        "url-drift",
                        f"{route_id}: {kind} breadcrumb exposes non-public route {url}",
                    )
                )

        if item.get("current"):
            current_flags.append(index)

    if current_indexes and any(index != len(trail) - 1 for index in current_indexes):
        findings.append(
            finding(
                "error",
                "order-drift",
                f"{route_id}: current canonical {current_url} appears before the end of {kind} breadcrumb",
            )
        )

    if kind == "visible":
        if len(current_flags) > 1:
            findings.append(
                finding(
                    "error",
                    "order-drift",
                    f"{route_id}: visible breadcrumb has multiple aria-current=page items",
                )
            )
        elif current_flags and current_flags[0] != len(trail) - 1:
            findings.append(
                finding(
                    "error",
                    "order-drift",
                    f"{route_id}: visible aria-current=page is not the last breadcrumb item",
                )
            )

    return findings


def linked_intermediate_urls(trail: list[dict], current_url: str) -> list[str]:
    """Return linked intermediate destinations, excluding optional host/current."""
    return [
        item["url"]
        for item in trail
        if item.get("url") and item["url"] not in {"/", current_url}
    ]


def trails_order_compatible(
    visible: list[dict],
    structured: list[dict],
    *,
    current_url: str,
) -> bool:
    """Detect an objective ordering contradiction without demanding identity.

    Google explicitly allows multiple/alternative breadcrumb trails and does
    not require every hierarchy level. Therefore different lengths or labels
    are not drift by themselves. We only fail when at least two destinations
    occur in both trails but their relative order conflicts.
    """
    visible_urls = linked_intermediate_urls(visible, current_url)
    structured_urls = linked_intermediate_urls(structured, current_url)
    common = set(visible_urls) & set(structured_urls)
    if len(common) < 2:
        return True
    return (
        [url for url in visible_urls if url in common]
        == [url for url in structured_urls if url in common]
    )


def audit_route(item: dict, *, root: Path, by_url: dict[str, dict]) -> dict:
    route_id = item["id"]
    source_file = item.get("sourceFile")
    result = {
        "id": route_id,
        "url": item["url"],
        "sourceFile": source_file,
        "coverage": "none",
        "visibleTrails": 0,
        "jsonldTrails": 0,
        "findings": [],
    }

    if not isinstance(source_file, str) or not source_file.endswith(".html"):
        return result

    source_path = root / source_file
    if not source_path.is_file():
        result["findings"].append(
            finding("error", "missing-source", f"{route_id}: sourceFile does not exist: {source_file}")
        )
        return result

    html = source_path.read_text(encoding="utf-8", errors="replace")
    current_url = canonical_path(html) or item["url"]
    if current_url != item["url"]:
        result["findings"].append(
            finding(
                "error",
                "url-drift",
                f"{route_id}: canonical path {current_url!r} differs from registry {item['url']!r}",
            )
        )

    visible = extract_visible_breadcrumbs(html)
    structured, json_errors = extract_jsonld_breadcrumbs(html)
    result["visibleTrails"] = len(visible)
    result["jsonldTrails"] = len(structured)

    if visible and structured:
        result["coverage"] = "visible+jsonld"
    elif visible:
        result["coverage"] = "visible-only"
    elif structured:
        result["coverage"] = "jsonld-only"

    for message in json_errors:
        result["findings"].append(
            finding("error", "invalid-jsonld", f"{route_id}: {message}")
        )

    for trail in visible:
        result["findings"].extend(
            validate_trail(
                trail,
                kind="visible",
                route_id=route_id,
                current_url=current_url,
                by_url=by_url,
            )
        )
    for trail in structured:
        result["findings"].extend(
            validate_trail(
                trail,
                kind="jsonld",
                route_id=route_id,
                current_url=current_url,
                by_url=by_url,
            )
        )

    if visible and not structured:
        result["findings"].append(
            finding(
                "info",
                "missing-jsonld",
                f"{route_id}: visible breadcrumb exists without BreadcrumbList; structured data is optional",
            )
        )
    elif structured and not visible:
        result["findings"].append(
            finding(
                "info",
                "missing-visible",
                f"{route_id}: BreadcrumbList exists without a dedicated visible breadcrumb; this is allowed",
            )
        )

    if visible and structured:
        for visible_index, visible_trail in enumerate(visible, start=1):
            if not any(
                trails_order_compatible(
                    visible_trail,
                    structured_trail,
                    current_url=current_url,
                )
                for structured_trail in structured
            ):
                result["findings"].append(
                    finding(
                        "error",
                        "order-drift",
                        f"{route_id}: visible breadcrumb trail #{visible_index} conflicts with every BreadcrumbList ordering",
                    )
                )

    return result


def run_audit(root: Path, registry_path: Path) -> dict:
    entries, by_url = load_registry(registry_path)
    routes = []

    for item in entries:
        if item.get("status") != "public" or item.get("searchIndex") is not True:
            continue
        source = item.get("sourceFile")
        if not isinstance(source, str) or not source.endswith(".html"):
            continue
        if item.get("url") == "/":
            continue
        routes.append(audit_route(item, root=root, by_url=by_url))

    summary = {
        "routes": len(routes),
        "visible+jsonld": sum(r["coverage"] == "visible+jsonld" for r in routes),
        "visible-only": sum(r["coverage"] == "visible-only" for r in routes),
        "jsonld-only": sum(r["coverage"] == "jsonld-only" for r in routes),
        "none": sum(r["coverage"] == "none" for r in routes),
        "errors": sum(
            f["severity"] == "error" for route in routes for f in route["findings"]
        ),
        "infos": sum(
            f["severity"] == "info" for route in routes for f in route["findings"]
        ),
    }
    return {"schemaVersion": 1, "origin": ORIGIN, "summary": summary, "routes": routes}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit visible/JSON-LD breadcrumb integrity")
    parser.add_argument("--root", default=str(ROOT), help="Repository root")
    parser.add_argument(
        "--registry",
        default="data/content-registry.json",
        help="Registry path relative to --root unless absolute",
    )
    parser.add_argument("--json", help="Optional JSON report output path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    registry_path = Path(args.registry)
    if not registry_path.is_absolute():
        registry_path = root / registry_path

    try:
        report = run_audit(root, registry_path)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"FAIL: breadcrumb audit could not run: {exc}", file=sys.stderr)
        return 2

    for route in report["routes"]:
        for item in route["findings"]:
            prefix = "ERROR" if item["severity"] == "error" else "INFO"
            stream = sys.stderr if item["severity"] == "error" else sys.stdout
            print(f"{prefix}: {item['code']}: {item['message']}", file=stream)

    if args.json:
        out = Path(args.json)
        if not out.is_absolute():
            out = root / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    summary = report["summary"]
    if summary["errors"]:
        print(
            f"FAIL: breadcrumb integrity ({summary['errors']} error(s), {summary['routes']} routes audited)",
            file=sys.stderr,
        )
        return 1

    print(
        "PASS: breadcrumb integrity "
        f"({summary['routes']} routes; "
        f"{summary['visible+jsonld']} visible+jsonld, "
        f"{summary['jsonld-only']} jsonld-only, "
        f"{summary['visible-only']} visible-only, "
        f"{summary['none']} without breadcrumb contract, "
        f"{summary['infos']} info finding(s))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
