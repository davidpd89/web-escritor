#!/usr/bin/env python3
"""Deterministic sitemap generator for web-escritor.

Writes sitemap.xml using HTTPS canonical domain https://davidportodiaz.com.
Rules (see 27_REPOSITORIOS_Y_MEJORAS_IMPLEMENTABLES_2026-08-16.md §13):
- noindex pages are excluded;
- drafts, examples and local-only folders are excluded;
- canonical URL wins; deduplicate by loc;
- lastmod comes from JSON-LD dateModified when present and parseable;
- omit lastmod when no reliable editorial date exists (never use file mtime);
- output is deterministic; --check compares without writing.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

_PUBLISHER = None


def _publisher():
    global _PUBLISHER
    if _PUBLISHER is None:
        spec = importlib.util.spec_from_file_location(
            "sitemap_publisher_allowlist", Path(__file__).resolve().with_name("build-public-dist.py")
        )
        _PUBLISHER = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_PUBLISHER)
    return _PUBLISHER


DOMAIN = "https://davidportodiaz.com"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

EXCLUDE_DIRS = {
    "node_modules",
    ".git",
    "assets",
    "images",
    "videos",
    "android",
    "tests",
    "lab",  # Preview/prototipos: excluir siempre, aunque falte meta noindex
    "_tools",
    "_reddit",
    "_david",
    "WEB DAVID PORTO nuevas ideas",
    "press-kit",
    "data",
    ".preview-dist",
    "dist",
}

SKIP_BASENAMES = {
    "offline.html",
    "404.html",
}

SKIP_SUFFIXES = (
    ".example.html",
    ".template.html",
    ".component.html",
    ".generated.example.html",
    ".integration.example.html",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_meta(text: str):
    canonical = None
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*>', text, flags=re.I)
    if m:
        h = re.search(r'href=["\']([^"\']+)["\']', m.group(0), flags=re.I)
        if h:
            canonical = h.group(1).strip()

    noindex = False
    for r in re.finditer(r'<meta[^>]+name=["\']robots["\'][^>]*>', text, flags=re.I):
        c = re.search(r'content=["\']([^"\']+)["\']', r.group(0), flags=re.I)
        if c and "noindex" in {directive.strip().lower() for directive in c.group(1).split(",")}:
            noindex = True
            break

    date_modified = extract_date_modified(text)
    return canonical, noindex, date_modified


def extract_date_modified(text: str):
    best = None
    for js in re.finditer(
        r'<script[^>]+type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        text,
        flags=re.I | re.S,
    ):
        try:
            data = json.loads(js.group(1).strip())
        except Exception:
            continue
        pending = [data]
        while pending:
            node = pending.pop()
            if isinstance(node, list):
                pending.extend(reversed(node))
                continue
            if not isinstance(node, dict):
                continue
            dm = node.get("dateModified")
            if isinstance(dm, str) and dm.strip():
                best = dm.strip()
                node_type = node.get("@type")
                if isinstance(node_type, str):
                    node_type = [node_type]
                if isinstance(node_type, list) and any(
                    kind in ("WebPage", "Article", "BlogPosting")
                    for kind in node_type
                ):
                    return best
            graph = node.get("@graph")
            if isinstance(graph, (list, dict)):
                pending.append(graph)
    return best


def normalize_lastmod(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None
        return value
    try:
        if value.endswith("Z"):
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None


def normalize_canonical(canonical: str | None, root: Path, path: Path) -> str | None:
    if canonical:
        if canonical.startswith("//"):
            canonical = "https:" + canonical
        if canonical.startswith("http://"):
            canonical = "https://" + canonical[len("http://") :]
        if canonical.startswith("https://"):
            try:
                parsed = urlsplit(canonical)
                if (
                    parsed.scheme != "https"
                    or parsed.hostname != "davidportodiaz.com"
                    or parsed.username is not None
                    or parsed.password is not None
                    or parsed.port is not None
                ):
                    return None
            except ValueError:
                return None
            return canonical.rstrip("/") + ("/" if canonical.endswith("/") else "")
        if canonical.startswith("/"):
            return (DOMAIN + canonical).rstrip("/") + ("/" if canonical.endswith("/") else "")
        if "://" in canonical or canonical.startswith(("javascript:", "data:", "mailto:")):
            return None

    rel = "/" + str(path.relative_to(root)).replace("\\", "/")
    if rel.endswith("/index.html"):
        rel = rel[: -len("index.html")] or "/"
    elif rel.endswith(".html"):
        rel = rel[:-5]
    if not rel.endswith("/") and rel != "/":
        pass
    return DOMAIN + rel if rel != "/" else DOMAIN + "/"


def should_skip_file(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in EXCLUDE_DIRS or part.startswith('.') for part in rel.parts[:-1]):
        return True
    name = path.name.lower()
    if name in SKIP_BASENAMES:
        return True
    if name == "feed.xml":
        return True
    lower = path.name.lower()
    if any(lower.endswith(sfx) for sfx in SKIP_SUFFIXES):
        return True
    if path.suffix.lower() != ".html":
        return True
    # Reuse the publisher allowlist for nested documents: never announce
    # HTML that the public artifact would not contain. Only applies to a real
    # site root (has index.html); bare fixtures are filtered by noindex only.
    if (root / "index.html").is_file() and not _publisher().is_publishable(rel.as_posix(), root):
        return True
    return False


def collect_urls(root: Path) -> dict[str, str | None]:
    urls: dict[str, str | None] = {}
    # Prune local browser profiles, worktrees and build output before walking.
    # Filtering only after rglob traversed those trees and leaked debug pages.
    candidates = []
    for directory, folders, files in os.walk(root):
        folders[:] = sorted(f for f in folders if f not in EXCLUDE_DIRS and not f.startswith('.'))
        candidates.extend(Path(directory) / f for f in files if f.endswith('.html'))
    for path in sorted(candidates):
        if should_skip_file(path, root):
            continue
        text = read_text(path)
        canonical, noindex, date_modified = extract_meta(text)
        if noindex:
            continue
        loc = normalize_canonical(canonical, root, path)
        if not loc:
            continue
        if loc.startswith(DOMAIN + "/WEB DAVID PORTO"):
            continue
        lastmod = normalize_lastmod(date_modified)
        if loc in urls:
            prev = urls[loc]
            if lastmod and prev:
                urls[loc] = max(lastmod, prev)
            elif lastmod and not prev:
                urls[loc] = lastmod
        else:
            urls[loc] = lastmod
    return dict(sorted(urls.items()))


def render_xml(urls: dict[str, str | None]) -> str:
    urlset = ET.Element("urlset", xmlns=NS)
    for loc, lastmod in urls.items():
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = loc
        if lastmod:
            ET.SubElement(url, "lastmod").text = lastmod
    xml_bytes = ET.tostring(urlset, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


def normalize_xml(text: str) -> str:
    return re.sub(r">\s+<", "><", text.strip())


def parse_existing(path: Path) -> dict[str, str | None]:
    if not path.exists():
        return {}
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError:
        return {}
    out: dict[str, str | None] = {}
    for url in root.findall(f"{{{NS}}}url"):
        loc_el = url.find(f"{{{NS}}}loc")
        if loc_el is None or not loc_el.text:
            continue
        lm_el = url.find(f"{{{NS}}}lastmod")
        out[loc_el.text.strip()] = lm_el.text.strip() if lm_el is not None and lm_el.text else None
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate deterministic sitemap.xml")
    ap.add_argument("--root", default=".", help="site root to scan")
    ap.add_argument("--output", default="sitemap.xml", help="output file")
    ap.add_argument("--check", action="store_true", help="compare with existing output; exit 2 if different")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    urls = collect_urls(root)
    generated = render_xml(urls)

    if args.check:
        existing_raw = output.read_text(encoding="utf-8") if output.exists() else ""
        if normalize_xml(existing_raw) != normalize_xml(generated):
            old = parse_existing(output)
            added = sorted(set(urls) - set(old))
            removed = sorted(set(old) - set(urls))
            changed = sorted(
                loc for loc in set(urls) & set(old) if urls[loc] != old[loc]
            )
            print("SITEMAP OUTDATED", file=sys.stderr)
            if added:
                print(f"  added ({len(added)}):", ", ".join(added[:10]), file=sys.stderr)
            if removed:
                print(f"  removed ({len(removed)}):", ", ".join(removed[:10]), file=sys.stderr)
            if changed:
                print(f"  lastmod changed ({len(changed)}):", ", ".join(changed[:10]), file=sys.stderr)
            return 2
        print(f"SITEMAP OK: {len(urls)} URLs")
        return 0

    output.write_text(generated, encoding="utf-8")
    print(f"GENERATED: {len(urls)} URLs -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
