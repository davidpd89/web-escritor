#!/usr/bin/env python3
"""Internal link graph checker for the static site.

Reports broken internal page links, orphan indexable pages, missing canonicals
and canonical collisions. Uses ERROR / WARNING / INFO severities.

Does not treat assets, feeds, legal/utility pages or noindex routes as graph errors.
See 27_REPOSITORIOS_Y_MEJORAS_IMPLEMENTABLES_2026-08-16.md §14.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

DOMAIN = "https://davidportodiaz.com"

EXCLUDE_DIRS = {
    "node_modules",
    ".git",
    "assets",
    "images",
    "videos",
    "android",
    "tests",
    "_tools",
    "_reddit",
    "_david",
    "WEB DAVID PORTO nuevas ideas",
    "press-kit",
    "data",
    ".preview-dist",
    "dist",
}

ASSET_EXTENSIONS = {
    ".css",
    ".js",
    ".mjs",
    ".json",
    ".xml",
    ".txt",
    ".webp",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".woff",
    ".woff2",
    ".ico",
    ".zip",
    ".ics",
    ".pdf",
}

ORPHAN_OK_PATHS = {
    "/",
    "/privacidad.html",
    "/aviso-legal.html",
    "/offline.html",
    "/samuel-entre-mundos.html",
    "/sitemap.xml",
    "/robots.txt",
    "/llms.txt",
    "/llms-full.txt",
    "/humans.txt",
    "/manifest.json",
    "/cuaderno/feed.xml",
}

ORPHAN_OK_PREFIXES = (
    "/ai/",
    "/assets/",
)


class Finding:
    __slots__ = ("level", "category", "message")

    def __init__(self, level: str, category: str, message: str):
        self.level = level
        self.category = category
        self.message = message


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def should_skip_file(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    if path.name.lower() in {"offline.html", "404.html"}:
        return True
    lower = path.name.lower()
    if lower.endswith((".example.html", ".template.html", ".component.html")):
        return True
    return False


def extract_canonical(text: str) -> str | None:
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*>', text, flags=re.I)
    if not m:
        return None
    h = re.search(r'href=["\']([^"\']+)["\']', m.group(0), flags=re.I)
    return h.group(1).strip() if h else None


def has_noindex(text: str) -> bool:
    m = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*>', text, flags=re.I)
    if not m:
        return False
    c = re.search(r'content=["\']([^"\']+)["\']', m.group(0), flags=re.I)
    return bool(c and "noindex" in c.group(1).lower())


def extract_anchor_links(text: str) -> list[str]:
    links = []
    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\']', text, flags=re.I):
        href = m.group(1).strip()
        if not href or href.startswith("#"):
            continue
        links.append(href.split("#", 1)[0])
    return links


def is_asset_link(link: str) -> bool:
    if link.startswith(("mailto:", "tel:", "javascript:")):
        return True
    path = link
    if link.startswith(DOMAIN):
        path = urlparse(link).path
    elif link.startswith("/"):
        path = link
    else:
        return False
    if path.startswith("/assets/"):
        return True
    if "?" in path:
        path = path.split("?", 1)[0]
    return Path(path).suffix.lower() in ASSET_EXTENSIONS


def resolve_link(src_path: Path, link: str, root: Path) -> str | None:
    if is_asset_link(link):
        return None
    if link.startswith("http://") or link.startswith("https://"):
        if not link.startswith(DOMAIN):
            return None
        return link
    if link.startswith("//"):
        link = "https:" + link
        if not link.startswith(DOMAIN):
            return None
        return link
    if link.startswith("/"):
        return DOMAIN.rstrip("/") + link
    # relative path: resolve against the source file, then express as a
    # domain-relative URL so url_to_file() can handle it uniformly.
    try:
        target_path = (src_path.parent / link).resolve()
    except (OSError, ValueError):
        return None
    try:
        rel = target_path.relative_to(root)
    except ValueError:
        return None
    return DOMAIN.rstrip("/") + "/" + str(rel).replace("\\", "/")


def url_to_file(root: Path, url: str) -> Path | None:
    if not url.startswith(DOMAIN):
        return None
    suffix = url[len(DOMAIN) :]
    if not suffix or suffix == "/":
        candidate = root / "index.html"
        return candidate if candidate.exists() else None
    if suffix.endswith("/"):
        candidate = root / suffix.lstrip("/") / "index.html"
    elif suffix.endswith(".html"):
        candidate = root / suffix.lstrip("/")
    else:
        candidate = root / (suffix.lstrip("/") + "/index.html")
        if candidate.exists():
            return candidate
        candidate = root / (suffix.lstrip("/") + ".html")
    return candidate if candidate.exists() else None


def canonical_to_path(canonical: str | None, fallback: Path, root: Path) -> str:
    if canonical:
        if canonical.startswith(DOMAIN):
            f = url_to_file(root, canonical.rstrip("/") + ("" if canonical.endswith(".html") else ""))
            if canonical.endswith("/"):
                f = url_to_file(root, canonical)
            if f:
                return str(f.resolve())
        if canonical.startswith("/"):
            f = url_to_file(root, DOMAIN + canonical)
            if f:
                return str(f.resolve())
    return str(fallback.resolve())


def orphan_allowed(canonical: str | None, path: Path, root: Path) -> bool:
    if canonical:
        if canonical in ORPHAN_OK_PATHS or canonical.rstrip("/") + "/" in ORPHAN_OK_PATHS:
            return True
        for prefix in ORPHAN_OK_PREFIXES:
            if canonical.startswith(DOMAIN + prefix) or canonical.startswith(prefix):
                return True
    rel = "/" + str(path.relative_to(root)).replace("\\", "/")
    if rel.endswith("/index.html"):
        rel = rel[: -len("index.html")] or "/"
    elif rel.endswith(".html"):
        rel = "/" + path.name if path.parent == root else rel
    return rel in ORPHAN_OK_PATHS


def short(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Check internal HTML link graph")
    ap.add_argument("--root", default=".", help="site root")
    ap.add_argument("--report", action="store_true", help="show inbound/outbound counts")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    files = [p for p in root.rglob("*.html") if not should_skip_file(p, root)]

    pages: dict[str, dict] = {}
    noindex_pages: list[str] = []

    for f in files:
        txt = read_text(f)
        if has_noindex(txt):
            noindex_pages.append(short(f, root))
            continue
        canonical = extract_canonical(txt)
        key = canonical_to_path(canonical, f, root)
        pages[key] = {
            "path": f,
            "canonical": canonical,
            "links": extract_anchor_links(txt),
        }

    incoming: dict[str, list[str]] = defaultdict(list)
    findings: list[Finding] = []

    for key, meta in pages.items():
        src = meta["path"]
        for link in meta["links"]:
            resolved = resolve_link(src, link, root)
            if not resolved:
                continue
            target = url_to_file(root, resolved)
            if target is None and resolved.endswith("/"):
                target = url_to_file(root, resolved + "index.html")
            if target is None and not resolved.endswith(".html"):
                target = url_to_file(root, resolved.rstrip("/") + "/")
            if target and target.exists():
                tkey = str(target.resolve())
                incoming[tkey].append(key)
            else:
                if not is_asset_link(link):
                    findings.append(
                        Finding(
                            "ERROR",
                            "broken",
                            f"{short(src, root)} -> {link} (resolved: {resolved})",
                        )
                    )

    for key, meta in pages.items():
        canon = meta["canonical"]
        path = meta["path"]
        if not canon:
            findings.append(
                Finding("WARNING", "missing-canonical", short(path, root))
            )
        if key not in incoming and not orphan_allowed(canon, path, root):
            label = canon or short(path, root)
            findings.append(
                Finding("WARNING", "orphan", f"{short(path, root)} ({label})")
            )

    canon_map: dict[str, list[str]] = defaultdict(list)
    for key, meta in pages.items():
        if meta["canonical"]:
            canon_map[meta["canonical"]].append(short(meta["path"], root))
    for canon, paths in canon_map.items():
        if len(paths) > 1:
            findings.append(
                Finding(
                    "ERROR",
                    "canonical-collision",
                    f"{canon} claimed by: {', '.join(paths)}",
                )
            )

    if noindex_pages:
        findings.append(
            Finding(
                "INFO",
                "noindex-skipped",
                f"{len(noindex_pages)} pages excluded (noindex): {', '.join(noindex_pages[:8])}"
                + (" …" if len(noindex_pages) > 8 else ""),
            )
        )

    print("INTERNAL GRAPH REPORT")
    print(f"Files scanned: {len(files)}")
    print(f"Indexable pages: {len(pages)}")

    for level in ("ERROR", "WARNING", "INFO"):
        items = [f for f in findings if f.level == level]
        if not items:
            continue
        print(f"\n{level} ({len(items)}):")
        for item in items[:200]:
            print(f"  [{item.category}] {item.message}")
        if len(items) > 200:
            print(f"  … and {len(items) - 200} more")

    if args.report:
        print("\nINBOUND COUNTS (indexable):")
        for key in sorted(pages, key=lambda k: short(Path(k), root)):
            count = len(incoming.get(key, []))
            print(f"  {count:3d}  {short(Path(key), root)}")

    errors = sum(1 for f in findings if f.level == "ERROR")
    warnings = sum(1 for f in findings if f.level == "WARNING")
    print(f"\nSummary: {errors} error(s), {warnings} warning(s)")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
