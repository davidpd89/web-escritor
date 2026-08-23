#!/usr/bin/env python3
"""Report binary assets under assets/ that no tracked text file references.

This is the mirror image of scripts/check-local-assets.py: that script
verifies every reference in HTML/CSS/JS resolves to a real file (broken
reference -> fails the page). This script verifies the other direction --
that every real file under assets/ is referenced by *something*.

REPORT-ONLY BY DESIGN -- do not wire --delete into CI or run it without a
human reviewing the list first. An "orphan" here is not automatically dead
weight: the site is mid-redesign, and a real, sizeable share of what this
reports is either (a) social-campaign art documented in
CAMPAIGN_SOCIAL_ASSETS (scripts/build-public-dist.py) -- uploaded to social
platforms by hand, deliberately never linked from any page, permanent by
design -- or (b) photography/art staged ahead of a design pass that hasn't
happened yet and will get wired up later. Confirmed 2026-08-22: do not
delete anything this script finds without checking with the site owner
first, even though the tooling below has a --delete flag for whenever a
real cleanup pass is actually decided.

Method: build one haystack of every git-tracked text-like file in the repo
(HTML/CSS/JS/MJS/JSON/XML/TXT/MD), then check whether each candidate binary
asset's filename appears anywhere in that haystack as a literal substring.
This deliberately over-counts "referenced" (a filename mentioned only in a
comment or a doc still counts) rather than under-count it -- the goal is
zero false positives on real, load-bearing assets, not a byte-perfect
report. A file only gets flagged if its exact name appears nowhere at all
in anything tracked by git. Known false positives on THIS repo today:
every path listed in CAMPAIGN_SOCIAL_ASSETS, by design (see above).

Python standard library only.

Usage:
    python scripts/check-orphan-assets.py              # report only, exit 0 always
    python scripts/check-orphan-assets.py --exclude-campaign-assets
        # same, but does not list the known-intentional social campaign art
    python scripts/check-orphan-assets.py --delete
        # DO NOT run in CI or automation -- manual cleanup tool only, for
        # a future pass once a human has reviewed the report
"""
from __future__ import annotations

import argparse
import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_campaign_social_assets() -> set[str]:
    """Import CAMPAIGN_SOCIAL_ASSETS straight from build-public-dist.py so
    this checker never carries its own, second copy of that list to drift
    out of sync with the one that actually governs the public dist build."""
    spec = importlib.util.spec_from_file_location(
        "build_public_dist", ROOT / "scripts" / "build-public-dist.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return set(module.CAMPAIGN_SOCIAL_ASSETS)

# Extensions worth auditing: the ones that showed up as multi-MB dead weight
# (images). Fonts/audio/video aren't included yet -- add here if a future
# audit finds the same pattern there.
ASSET_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg"}

# Text-like extensions scanned for references. Deliberately broad: a
# filename can legitimately show up in a .json data file (editorial-facts,
# press-kit manifests), a .txt (llms.txt, humans.txt), or a .md doc, not
# just HTML/CSS/JS.
HAYSTACK_EXTENSIONS = {
    ".html", ".css", ".js", ".mjs", ".json", ".xml", ".txt", ".md", ".xsl",
}

# Directories that are never the real, published site and must not
# influence either side of this check: neither as a source of "this file
# exists" nor as a source of "this file is referenced".
SKIP_PARTS = {
    ".git", "node_modules", "WEB DAVID PORTO nuevas ideas", "archive",
    ".codex_work", ".preview-dist", "dist",
}


def git_tracked_files() -> list[Path] | None:
    """Prefer git ls-files over a filesystem walk: it automatically
    excludes gitignored local-only files (drafts, scratch notes, generated
    dist output) without needing to keep SKIP_PARTS in sync with .gitignore
    by hand. Falls back to a filesystem walk if git isn't available."""
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return [ROOT / line for line in out.splitlines() if line.strip()]


def all_tracked_or_walk() -> list[Path]:
    tracked = git_tracked_files()
    if tracked is not None:
        return [p for p in tracked if p.is_file()]
    found = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        found.append(path)
    return found


def build_haystack(files: list[Path]) -> str:
    chunks = []
    for path in files:
        if path.suffix.lower() not in HAYSTACK_EXTENSIONS:
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(chunks)


def find_orphans(root: Path, exclude_campaign_assets: bool = False) -> list[tuple[Path, int]]:
    files = all_tracked_or_walk()
    haystack = build_haystack(files)

    campaign = load_campaign_social_assets() if exclude_campaign_assets else set()

    candidates = [
        p for p in files
        if p.suffix.lower() in ASSET_EXTENSIONS
        and (root / "assets") in p.parents
    ]

    orphans = []
    for path in sorted(candidates):
        rel = path.relative_to(root).as_posix()
        if rel in campaign:
            continue
        if path.name not in haystack:
            orphans.append((path, path.stat().st_size))
    return orphans


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument(
        "--exclude-campaign-assets", action="store_true",
        help="do not list the known-intentional social campaign art (CAMPAIGN_SOCIAL_ASSETS)",
    )
    ap.add_argument(
        "--delete", action="store_true",
        help="MANUAL USE ONLY, never in CI: delete every orphan listed (irreversible outside git history)",
    )
    args = ap.parse_args()
    root = Path(args.root).resolve()

    orphans = find_orphans(root, exclude_campaign_assets=args.exclude_campaign_assets)
    total_bytes = sum(size for _, size in orphans)

    for path, size in orphans:
        rel = path.relative_to(root).as_posix()
        print(f"ORPHAN {rel} ({size / 1024 / 1024:.2f} MB)")

    print(
        f"\nOrphan asset check: {len(orphans)} unreferenced file(s), "
        f"{total_bytes / 1024 / 1024:.1f} MB total. Report-only -- nothing deleted "
        f"unless --delete was passed explicitly."
    )

    if args.delete:
        for path, _ in orphans:
            path.unlink()
        if orphans:
            print(f"DELETED {len(orphans)} file(s), reclaimed {total_bytes / 1024 / 1024:.1f} MB.")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
