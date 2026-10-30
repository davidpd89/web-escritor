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
import hashlib
import html
import json
import os
import re
import shutil
from html.parser import HTMLParser
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

class RobotsMetaParser(HTMLParser):
    """Read noindex tokens regardless of HTML attribute order or quoting."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.noindex = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "meta":
            return
        values = {key.lower(): value or "" for key, value in attrs}
        if values.get("name", "").strip().casefold() not in {"robots", "googlebot", "bingbot"}:
            return
        directives = re.split(r"[,\s]+", values.get("content", "").casefold().strip())
        if "noindex" in directives:
            self.noindex = True


def git_tracked_html(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "*.html"], cwd=root, capture_output=True, text=True, check=True
    )
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def load_registry_by_source(root: Path) -> dict[str, dict]:
    raw = json.loads((root / "data" / "content-registry.json").read_text(encoding="utf-8"))
    defaults = raw.get("defaults", {})
    by_source: dict[str, dict] = {}
    entries = [e for e in raw.get("entries", []) if e.get("sourceFile")]
    # Las entradas de ancla (`/pagina/#seccion`) no son la pagina: un `searchIndex: false` o un
    # estado no publico de un ancla no debe sacar la pagina entera del indice (libros/index.html
    # quedaba fuera del buscador por sus dos anclas de obra). Si la pagina tiene entrada propia,
    # solo cuentan las entradas de pagina.
    has_page_entry = {e["sourceFile"] for e in entries if "#" not in str(e.get("url") or "")}
    for entry in entries:
        source = entry.get("sourceFile")
        if source:
            if source in has_page_entry and "#" in str(entry.get("url") or ""):
                continue
            current = {**defaults, **entry}
            previous = by_source.get(source)
            if previous is not None:
                current = {**previous, **current}
                if previous.get("status", "public") != "public" or current.get("status", "public") != "public":
                    current["status"] = "private"
                if previous.get("searchIndex", True) is False or current.get("searchIndex", True) is False:
                    current["searchIndex"] = False
            by_source[source] = current
    return by_source


def is_noindex(text: str) -> bool:
    if "<meta" not in text.lower():
        return False
    parser = RobotsMetaParser()
    parser.feed(text)
    return parser.noindex


# Internal, non-page HTML: build-time fragments, test fixtures/templates --
# never real site content, whatever content-registry.json says or doesn't
# say. Same notion as build-public-dist.py's EXCLUDE_DIR_PREFIXES (this
# doesn't import that list directly since its scope is "what's on disk in
# the public dist", not "what's a searchable page" -- e.g. scripts/ has no
# HTML there either way, but tests/fixtures/*.html does). The invariant
# "everything indexed is also published" is enforced by
# tests/test-seo-pagefind-public-boundary.py on the real repository.
INTERNAL_DIR_PREFIXES = ("data/", "tests/", "scripts/")


def eligible_pages(root: Path) -> list[str]:
    """Return git-tracked *.html paths eligible for the local search index,
    sorted for deterministic manifest output."""
    by_source = load_registry_by_source(root)
    eligible: list[str] = []
    for rel in git_tracked_html(root):
        if rel.startswith(INTERNAL_DIR_PREFIXES):
            continue
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


def inject_registry_search_title(text: str, entry: dict | None) -> str:
    """Inject the content-registry label as Pagefind's canonical search title."""
    label = str((entry or {}).get("label") or "").strip()
    if not label:
        return text
    tag = (
        '<meta data-pagefind-meta="title[content]" content="'
        + html.escape(label, quote=True)
        + '">'
    )
    return re.sub(r"</head\s*>", tag + "\n</head>", text, count=1, flags=re.I)


def build_src_tree(root: Path, pages: list[str], src_dir: Path) -> None:
    if src_dir.exists():
        shutil.rmtree(src_dir)
    src_dir.mkdir(parents=True)
    by_source = load_registry_by_source(root)
    for rel in pages:
        dst = src_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        source = (root / rel).read_text(encoding="utf-8", errors="ignore")
        dst.write_text(
            inject_registry_search_title(source, by_source.get(rel)),
            encoding="utf-8",
        )


def run_pagefind(src_dir: Path, out_dir: Path) -> None:
    """Run the Pagefind CLI into `out_dir`, which must be a fresh staging dir.

    It never deletes anything: build() points it at a sibling staging
    directory and only promotes that over the live index after validating it,
    so a missing dependency or a failed run leaves the previous index intact.
    """
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


def source_hashes(root: Path, pages: list[str]) -> dict[str, str]:
    """Hash authored HTML plus registry labels injected into Pagefind.

    Newlines are normalised before hashing. Every text file in this repo is
    checked out with CRLF on Windows and LF on Linux, so hashing raw bytes
    made the manifest platform-dependent: an index regenerated on Windows
    was reported stale by CI for all ~200 pages, with no actual content
    difference, which is why regenerating Pagefind had to be done through a
    throwaway workflow instead of locally. CRLF versus LF is not a change in
    indexed content -- Pagefind indexes the text -- so it must not read as
    one here either.
    """
    by_source = load_registry_by_source(root)
    hashes: dict[str, str] = {}
    for rel in pages:
        digest = hashlib.sha256()
        digest.update((root / rel).read_bytes().replace(b"\r\n", b"\n"))
        digest.update(b"\0pagefind-registry-label\0")
        label = str((by_source.get(rel) or {}).get("label") or "").strip()
        digest.update(label.encode("utf-8"))
        hashes[rel] = digest.hexdigest()
    return hashes


TEXT_ARTIFACT_SUFFIXES = (".js", ".css", ".json")


def artifact_hashes(out_dir: Path) -> dict[str, str]:
    """sha256 of the generated Pagefind artifacts (all but the manifest).

    Text artifacts are newline-normalised so CRLF/LF checkouts agree.
    """
    hashes: dict[str, str] = {}
    for path in sorted(out_dir.rglob("*")):
        if not path.is_file() or path.name == MANIFEST_NAME:
            continue
        data = path.read_bytes()
        if path.suffix in TEXT_ARTIFACT_SUFFIXES:
            data = data.replace(b"\r\n", b"\n")
        hashes[path.relative_to(out_dir).as_posix()] = hashlib.sha256(data).hexdigest()
    return hashes


def write_manifest(out_dir: Path, pages: list[str], root: Path) -> None:
    manifest = {
        "schema_version": 4,
        "page_count": len(pages),
        "pages": pages,
        "source_sha256": source_hashes(root, pages),
        "artifact_sha256": artifact_hashes(out_dir),
    }
    (out_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _lock_path(out_dir: Path) -> Path:
    return out_dir.parent / f".{out_dir.name}-build.lock"


def _acquire_lock(out_dir: Path) -> Path | None:
    """Exclusive build lock next to `out_dir` (O_EXCL works on Windows and Linux).

    Concurrent builds share `.pagefind-src` and the promotion step; the
    second one fails instead of deleting the first one's work.
    """
    lock = _lock_path(out_dir)
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print(
            f"FAIL: another Pagefind build holds {lock} -- wait for it, or delete the "
            "lock if no build is running.",
            file=sys.stderr,
        )
        return None
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(f"{os.getpid()}\n")
    return lock


def _promote(staging: Path, out_dir: Path, backup: Path) -> None:
    """Swap `staging` in as `out_dir`, restoring the previous index on failure.

    Only renames onto paths that do not exist: renaming over a non-empty
    directory fails on Windows, so the live index is first moved aside.
    """
    had_previous = out_dir.exists()
    if had_previous:
        os.replace(out_dir, backup)
    try:
        os.replace(staging, out_dir)
    except BaseException:
        if had_previous:
            if out_dir.exists():
                shutil.rmtree(out_dir, ignore_errors=True)
            os.replace(backup, out_dir)
        raise
    if had_previous:
        shutil.rmtree(backup, ignore_errors=True)


def build(root: Path, out_dir: Path, src_dir: Path) -> int:
    pages = eligible_pages(root)
    if not pages:
        print("FAIL: no eligible pages found -- refusing to build an empty index.", file=sys.stderr)
        return 1
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    lock = _acquire_lock(out_dir)
    if lock is None:
        return 1
    staging = out_dir.parent / f".{out_dir.name}.staging-{os.getpid()}"
    backup = out_dir.parent / f".{out_dir.name}.backup-{os.getpid()}"
    try:
        for leftover in (staging, backup):
            if leftover.exists():
                shutil.rmtree(leftover)
        build_src_tree(root, pages, src_dir)
        try:
            run_pagefind(src_dir, staging)
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"FAIL: Pagefind did not run ({exc}); previous index kept.", file=sys.stderr)
            return 1
        finally:
            shutil.rmtree(src_dir, ignore_errors=True)
        if not (staging / "pagefind.js").is_file():
            print("FAIL: Pagefind produced no pagefind.js; previous index kept.", file=sys.stderr)
            return 1
        write_manifest(staging, pages, root)
        if check(root, staging) != 0:
            print("FAIL: new Pagefind output failed validation; previous index kept.", file=sys.stderr)
            return 1
        _promote(staging, out_dir, backup)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
        lock.unlink(missing_ok=True)
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

    committed_hashes = manifest.get("source_sha256")
    current_hashes = source_hashes(root, current_pages)
    if committed_hashes != current_hashes:
        committed_hashes = committed_hashes if isinstance(committed_hashes, dict) else {}
        changed = sorted(
            rel for rel in current_pages
            if committed_hashes.get(rel) != current_hashes.get(rel)
        )
        print(
            "FAIL: pagefind/ is stale -- indexed HTML content changed since last build.",
            file=sys.stderr,
        )
        if changed:
            print(f"  changed eligible page(s): {changed}", file=sys.stderr)
        print("Regenerate with: python scripts/build-pagefind-index.py", file=sys.stderr)
        return 1

    committed_artifacts = manifest.get("artifact_sha256")
    if not isinstance(committed_artifacts, dict) or "pagefind.js" not in committed_artifacts:
        print("FAIL: manifest has no artifact_sha256 for pagefind.js -- regenerate.", file=sys.stderr)
        return 1
    current_artifacts = artifact_hashes(out_dir)
    bad = sorted(
        name for name, digest in committed_artifacts.items()
        if name in current_artifacts and current_artifacts[name] != digest
    )
    if "pagefind.js" not in current_artifacts:
        bad.append("pagefind.js")
    if bad:
        print(f"FAIL: pagefind/ artifact(s) corrupted or modified: {bad}", file=sys.stderr)
        print("Regenerate with: python scripts/build-pagefind-index.py", file=sys.stderr)
        return 1

    print(
        f"PASS: pagefind/ matches the current corpus and source content "
        f"({len(current_pages)} page(s))."
    )
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
