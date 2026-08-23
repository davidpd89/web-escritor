#!/usr/bin/env python3
"""Build the local Pagefind search index consumed by `assets/assistant.js`
(`pagefindFallback()` already does `import('/pagefind/pagefind.js')` and
falls back to `rankLocalSources()` if that import fails -- see docs/
PENDIENTE-AF-ASSISTANT-PAGEFIND-LOCAL-SEARCH.md). Before this script, that
import failed on every request because `/pagefind/` never existed.

Corpus of truth (AF.1 -- no second manual route list):
- eligible source = every git-tracked *.html file;
- EXCLUDED if its `data/content-registry.json` entry (matched by
  `sourceFile`) has `status` != "public" (gated/staging -- same signal as
  `donde-empieza-la-jaula/`, whatever the future canonical helper for that
  ends up being named);
- EXCLUDED if that entry has `searchIndex: false` (privacidad.html,
  aviso-legal.html, /ai/, the Noveris-quarantine article, etc.);
- EXCLUDED if the page's OWN `<meta name="robots" content="...noindex...">`
  says so -- this is what catches structural pages with no registry entry
  at all (404.html, offline.html, samuel-entre-mundos.html redirect stub,
  herramientas/auditor-web/ internal report, lab/** design lab) without a
  second hardcoded filename list that could drift from the pages themselves;
- everything else defaults to INCLUDED (matches this repo's established
  "default-include, explicit-exclude" rule from build-public-dist.py).

Usage:
  python scripts/build-pagefind-index.py            # rebuild pagefind/
  python scripts/build-pagefind-index.py --check    # verify pagefind/ is
      not stale against the current eligible-pages corpus (does not rebuild)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "content-registry.json"
SRC_DIR = ROOT / ".pagefind-src"
OUT_DIR = ROOT / "pagefind"
MANIFEST_NAME = "eligible-manifest.json"

# Repeated shell chrome present identically on every page (header, the
# sitewide Explorar dialog, footer). <nav>/<footer>/<script>/<form> are
# already skipped by Pagefind itself; `<dialog>` is not, and without this
# every single search result would also match "Explorar" navigation text.
EXCLUDE_SELECTORS = "header.site-header, dialog.explore-dialog, footer.site-footer"

ROBOTS_NOINDEX_RE = re.compile(
    r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex', re.IGNORECASE
)


def git_tracked_html(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "*.html"], cwd=root, capture_output=True, text=True, check=True
    )
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def load_registry_by_source(root: Path) -> dict[str, dict]:
    raw = json.loads((root / "data" / "content-registry.json").read_text(encoding="utf-8"))
    defaults = raw.get("defaults", {})
    by_source: dict[str, dict] = {}
    for entry in raw.get("entries", []):
        source = entry.get("sourceFile")
        if source:
            by_source[source] = {**defaults, **entry}
    return by_source


def is_noindex(text: str) -> bool:
    return bool(ROBOTS_NOINDEX_RE.search(text))


def eligible_pages(root: Path) -> list[str]:
    """Return git-tracked *.html paths eligible for the local search index,
    sorted for deterministic manifest output."""
    by_source = load_registry_by_source(root)
    eligible: list[str] = []
    for rel in git_tracked_html(root):
        if rel.startswith("data/"):
            continue  # build-time fragment (e.g. injected into autor.html), not a standalone page
        entry = by_source.get(rel)
        if entry is not None:
            if entry.get("status", "public") != "public":
                continue
            if entry.get("searchIndex", True) is False:
                continue
        text = (root / rel).read_text(encoding="utf-8", errors="ignore")
        if is_noindex(text):
            continue
        eligible.append(rel)
    return eligible


def build_src_tree(root: Path, pages: list[str], src_dir: Path) -> None:
    if src_dir.exists():
        shutil.rmtree(src_dir)
    src_dir.mkdir(parents=True)
    for rel in pages:
        dst = src_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, dst)


def run_pagefind(src_dir: Path, out_dir: Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    subprocess.run(
        [
            "npx", "--no-install", "pagefind",
            "--site", str(src_dir),
            "--output-path", str(out_dir),
            "--exclude-selectors", EXCLUDE_SELECTORS,
        ],
        cwd=ROOT,
        check=True,
        shell=(sys.platform == "win32"),
    )


def write_manifest(out_dir: Path, pages: list[str]) -> None:
    manifest = {"schema_version": 1, "page_count": len(pages), "pages": pages}
    (out_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def build(root: Path, out_dir: Path, src_dir: Path) -> int:
    pages = eligible_pages(root)
    if not pages:
        print("FAIL: no eligible pages found -- refusing to build an empty index.", file=sys.stderr)
        return 1
    build_src_tree(root, pages, src_dir)
    try:
        run_pagefind(src_dir, out_dir)
    finally:
        shutil.rmtree(src_dir, ignore_errors=True)
    write_manifest(out_dir, pages)
    print(f"BUILT {out_dir}: {len(pages)} page(s) indexed.")
    return 0


def check(root: Path, out_dir: Path) -> int:
    if not out_dir.exists():
        print(f"FAIL: {out_dir} does not exist -- run `python scripts/build-pagefind-index.py` first.", file=sys.stderr)
        return 1
    required = ["pagefind.js", MANIFEST_NAME]
    missing = [name for name in required if not (out_dir / name).exists()]
    if missing:
        print(f"FAIL: {out_dir} is missing required file(s): {', '.join(missing)}", file=sys.stderr)
        return 1
    manifest = json.loads((out_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    committed_pages = manifest.get("pages", [])
    current_pages = eligible_pages(root)
    if committed_pages != current_pages:
        added = sorted(set(current_pages) - set(committed_pages))
        removed = sorted(set(committed_pages) - set(current_pages))
        print("FAIL: pagefind/ is stale -- eligible pages changed since last build.", file=sys.stderr)
        if added:
            print(f"  newly eligible, not yet indexed: {added}", file=sys.stderr)
        if removed:
            print(f"  indexed but no longer eligible: {removed}", file=sys.stderr)
        print("Regenerate with: python scripts/build-pagefind-index.py", file=sys.stderr)
        return 1
    print(f"PASS: pagefind/ matches the current corpus ({len(current_pages)} page(s)).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="Verify pagefind/ isn't stale; does not rebuild.")
    ap.add_argument("--root", default=str(ROOT), help="Repo root (for isolated tests).")
    ap.add_argument("--out", default=None, help="Output dir (defaults to <root>/pagefind).")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out).resolve() if args.out else root / "pagefind"
    src_dir = root / ".pagefind-src"

    if args.check:
        return check(root, out_dir)
    return build(root, out_dir, src_dir)


if __name__ == "__main__":
    raise SystemExit(main())
