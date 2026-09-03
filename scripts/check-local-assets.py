#!/usr/bin/env python3
"""Validate that local asset references in HTML actually resolve to files.

Checks <script src>, <link rel="stylesheet|icon|apple-touch-icon|manifest|
preload"> href, <img src>, <source src/srcset> for LOCAL references (site-
relative or root-relative paths) and reports any that don't exist on disk.
External (http/https), mailto:, tel:, data:, javascript: and #anchor
references are ignored - this is a local-file existence check only, not a
link checker (see broken-links.yml for external links).

Python standard library only.

Usage:
    python scripts/check-local-assets.py
    python scripts/check-local-assets.py --root .
"""
from __future__ import annotations

import argparse
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

SKIP_PARTS = {
    ".git", ".github", "node_modules", "tests", "vendor",
    "WEB DAVID PORTO nuevas ideas", "archive", ".codex_work",
    ".preview-dist", "dist", ".claude",
}

# Attributes worth checking, per (tag, attribute) -> "single" or "srcset"
CHECKED_ATTRS = {
    ("script", "src"): "single",
    ("img", "src"): "single",
    ("source", "src"): "single",
    ("source", "srcset"): "srcset",
    ("img", "srcset"): "srcset",
    ("link", "href"): "link-href",  # filtered further by rel=
}

RELEVANT_LINK_RELS = {
    "stylesheet", "icon", "apple-touch-icon", "manifest", "preload",
    "shortcut icon", "mask-icon",
}

IGNORED_SCHEMES = {"http", "https", "mailto", "tel", "javascript", "data", "sms"}


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str, int]] = []  # (kind, url, line)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        data = {k.lower(): (v or "") for k, v in attrs}
        line = self.getpos()[0]

        if tag == "link":
            rel = data.get("rel", "").strip().lower()
            href = data.get("href", "")
            if rel in RELEVANT_LINK_RELS and href:
                self.refs.append(("link", href, line))
            return

        if tag == "script":
            src = data.get("src", "")
            if src:
                self.refs.append(("script", src, line))
            return

        if tag == "img":
            src = data.get("src", "")
            if src:
                self.refs.append(("img", src, line))
            srcset = data.get("srcset", "")
            if srcset:
                for entry in srcset.split(","):
                    url = entry.strip().split(" ")[0].strip()
                    if url:
                        self.refs.append(("img-srcset", url, line))
            return

        if tag == "source":
            src = data.get("src", "")
            if src:
                self.refs.append(("source", src, line))
            srcset = data.get("srcset", "")
            if srcset:
                for entry in srcset.split(","):
                    url = entry.strip().split(" ")[0].strip()
                    if url:
                        self.refs.append(("source-srcset", url, line))
            return


def is_local(url: str) -> bool:
    url = url.strip()
    if not url or url.startswith("#"):
        return False
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme.lower() in IGNORED_SCHEMES:
        return False
    if url.startswith("//"):
        return False  # protocol-relative external
    return True


def strip_query_fragment(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path


def resolve_local(url: str, html_path: Path, root: Path) -> Path:
    clean = unquote(strip_query_fragment(url))
    if clean.startswith("/"):
        return root / clean.lstrip("/")
    return (html_path.parent / clean).resolve()


def find_html_files(root: Path):
    for path in sorted(root.rglob("*.html")):
        if any(part in SKIP_PARTS for part in path.relative_to(root).parts):
            continue
        yield path


def is_noindex(text: str) -> bool:
    import re
    m = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']', text, flags=1)
    if not m:
        return False
    return "noindex" in m.group(1).lower()


def audit_file(path: Path, root: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    parser = AssetParser()
    try:
        parser.feed(text)
    except Exception:
        return []

    rel = path.relative_to(root).as_posix()
    errors = []
    seen = set()
    for kind, url, line in parser.refs:
        if not is_local(url):
            continue
        key = (url, kind)
        if key in seen:
            continue
        seen.add(key)
        target = resolve_local(url, path, root)
        if not target.exists():
            errors.append(f"{rel}:{line}: missing local {kind} target: {url} -> {target.relative_to(root) if root in target.parents or target == root else target}")
    return errors


import re as _re

# Local-reference patterns inside JS source that an HTML attribute scan can't
# see: static `from './x.js'`, side-effect `import('./x.js')` dynamic
# imports, `new Worker('./x.js')` and `importScripts('./x.js')` (used inside
# worker files themselves). Each capture group must be the quoted path.
JS_REF_PATTERNS = [
    (_re.compile(r"""from\s+['"](\.\.?/[^'"]+)['"]"""), "static import"),
    (_re.compile(r"""\bimport\(\s*['"](\.\.?/[^'"]+)['"]"""), "dynamic import()"),
    (_re.compile(r"""new\s+Worker\(\s*['"]([^'"]+)['"]"""), "new Worker()"),
    (_re.compile(r"""\bimportScripts\(\s*['"]([^'"]+)['"]"""), "importScripts()"),
]


def audit_js_imports(root: Path) -> list[str]:
    """Local references inside JS source are invisible to an HTML attribute
    scan but are exactly the kind of reference that can 404 or fail to load
    silently at runtime - check every JS file under assets/ (where the
    site's scripts/modules/workers live)."""
    errors = []
    assets_dir = root / "assets"
    if not assets_dir.is_dir():
        return errors
    for js_path in sorted(assets_dir.rglob("*.js")):
        try:
            text = js_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel_js = js_path.relative_to(root).as_posix()
        for pattern, label in JS_REF_PATTERNS:
            for m in pattern.finditer(text):
                ref = m.group(1)
                if not is_local(ref):
                    continue
                target = resolve_local(ref, js_path, root)
                if not target.exists():
                    errors.append(f"{rel_js}: missing {label} target: {ref} -> {target}")
    return errors


def audit_css_urls(root: Path) -> list[str]:
    """CSS `url(...)` referencing a local, non-data path (fonts, background
    images) - the site currently has none pointing off-disk, but this is a
    one-line regex to keep it that way rather than a hypothetical risk."""
    url_re = _re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""")
    errors = []
    for css_path in sorted(root.rglob("*.css")):
        rel = css_path.relative_to(root)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        try:
            text = css_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel_css = rel.as_posix()
        for m in url_re.finditer(text):
            ref = m.group(2).strip()
            if not is_local(ref):
                continue
            target = resolve_local(ref, css_path, root)
            if not target.exists():
                errors.append(f"{rel_css}: missing CSS url() target: {ref} -> {target}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    all_errors: list[str] = []
    scanned = 0
    for path in find_html_files(root):
        scanned += 1
        all_errors.extend(audit_file(path, root))

    js_errors = audit_js_imports(root)
    all_errors.extend(js_errors)

    css_errors = audit_css_urls(root)
    all_errors.extend(css_errors)

    for e in all_errors:
        print(f"ERROR {e}")

    print(
        f"\nLocal asset check: {scanned} HTML files scanned; {len(all_errors)} broken local "
        f"reference(s) (including {len(js_errors)} JS reference target(s) and "
        f"{len(css_errors)} CSS url() target(s))."
    )
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
