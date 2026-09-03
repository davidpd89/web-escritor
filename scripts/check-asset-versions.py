#!/usr/bin/env python3
"""Check that every page references the site's runtime assets
with the SAME cache-busting version string per asset, and that no page
loads a tracked asset completely unversioned.

Why this exists: a real incident (2026-08-20, corrective audit point 6)
had 28 pages still on script.js?v=20260615-stable-1 / styles.css?v=...
(a June version) while script.js/styles.css had changed substantially in
August, including the newsletter contract rewrite — meaning most of the
site was silently serving stale cached JS/CSS to returning visitors via
the service worker. Separately, another ~25 pages loaded
/styles.css with no version query string at all. Neither class of bug
was caught by any existing checker.

A second incident (2026-09-02) hit the exact same class of bug on two
different assets this checker didn't cover yet: v1-fonts.css was loaded
completely unversioned on 71 pages, and v1-home.css?v=9 on index.html
was never bumped across two rounds of real fixes to that file (a font-
display change, then a corner-bracket/divider fix) -- so the author kept
seeing the pre-fix behavior on every reload. Added both to TRACKED_ASSETS
below rather than creating a second, separate checker for them.

A third, distinct failure mode this checker did NOT cover until now
(2026-09-02, GPT audit item 24): the version check above only confirms
every page cites the SAME ?v= for a given asset -- it says nothing about
whether that ?v= still matches the file's actual current bytes. Editing a
tracked asset's content and forgetting to bump TRACKED_ASSETS below is
exactly the same silent-stale-cache bug, just introduced from the other
direction: every page would agree on ?v=1, correctly per this checker,
while every returning visitor's cached ?v=1 response is now wrong. A
content-hash guardrail closes that gap: see HASH_LOCK_PATH below.

This checker has three things it can be pointed at:
  1. The current canonical version per asset, read from TRACKED_ASSETS
     below (kept here instead of a separate config file so there is
     exactly one place to bump each — update the relevant entry AND run
     this checker as part of any release that changes that asset).
  2. Every git-tracked HTML file's actual references to each asset.
  3. A committed hash lockfile (scripts/asset-version-hashes.json) binding
     each asset's *current* version number to a SHA-256 of its bytes at
     the time that version was recorded, so a content edit under an
     unchanged version number fails loudly instead of silently.

Usage:
  python scripts/check-asset-versions.py
    Validates (1)+(2)+(3). Fails if any HTML reference is missing/stale,
    or if a tracked asset's bytes no longer match the hash recorded for
    its current declared version.

  python scripts/check-asset-versions.py --update-hashes
    Recomputes the lockfile entry for every asset whose TRACKED_ASSETS
    version has no matching recorded hash yet (i.e. you just bumped it).
    Run this locally right after bumping a version and commit the
    resulting scripts/asset-version-hashes.json alongside your change --
    this mode never runs unattended in CI, it only ever records a hash
    for a version transition a human just made on purpose.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HASH_LOCK_PATH = ROOT / "scripts" / "asset-version-hashes.json"

# Bump the relevant entry — and only that entry — when cutting a release
# that changes the given asset. Then run this checker; it will list every
# page still on the old version, or still completely unversioned.
TRACKED_ASSETS = {
    "script.js": "202609-launch-1",
    "styles.css": "202609-launch-1",
    "v1-fonts.css": "1",
    "v1-home.css": "11",
    "v1-tokens.css": "1",
    "v1-base.css": "1",
    "v1-shell-base.css": "1",
    "v1-shell-lrb-v2.css": "1",
    "v1-lrb-material-v2.css": "1",
    "v1-home-editorial-v3.css": "1",
    "v1-editorial-interior-v4.css": "1",
    "v1-editorial-interactions-v4.css": "1",
    "v1-site-cohesion-v6.css": "2",
    "v1-reflow-hardening-v7.css": "1",
    "v1-text-resilience-v8.css": "1",
    "v1-shell.css": "3",
    "v1-shell.js": "2",
    "v1-components.css": "3",
    "v1-families.css": "2",
    "newsletter-general.js": "1",
    "v1-tools.css": "4",
    "v1-tools-identity.css": "1",
    "v1-editorial.css": "1",
    "v1-editorial.js": "1",
    "newsletter-popup.css": "1",
    "newsletter-popup.js": "2",
    "v1-no-js-pending.css": "1",
    "cuaderno-index.css": "1",
    "editoriales.css": "2",
    "v1-identity.css": "1",
    "v1-tools-publishing.css": "1",
    "v1-recommendations.css": "2",
    "v1-findability.css": "1",
    "v1-book.css": "2",
    "v1-editoriales-detail.css": "1",
    "assistant.css": "1",
    "assistant.js": "2",
    "v1-legal.css": "2",
    "noveris.css": "1",
    "v1-cuaderno-topics.css": "1",
    "dialogo-espanol.js": "3",
    "v1-beta-readers.css": "1",
    "v1-accessibility-statement.css": "1",
    "v1-ai-authority.css": "1",
    "assistant-embed.css": "2",
    "assistant-embed.js": "1",
    "club-session-builder.css": "2",
    "club-session-builder.js": "1",
    "clubes-samuel.css": "1",
    "radar-convocatorias.css": "1",
    "radar-convocatorias.js": "1",
    "surprise-content.generated.js": "1",
    "surprise-me.js": "1",
    "editoriales.js": "1",
    "v1-events.css": "1",
    "v1-ferias.css": "1",
    "fragmento.css": "1",
    "auditor-pagina-libro.css": "1",
    "auditor-pagina-libro.js": "1",
    "contador-palabras-engine.js": "3",
    "contador-palabras.js": "1",
    "dialogo-convenciones.js": "1",
    "dialogo-espanol.css": "1",
    "pov-distribucion.css": "1",
    "pov-distribucion-engine.js": "2",
    "pov-distribucion.js": "3",
    "entrevista-familiar.css": "1",
    "entrevista-familiar.js": "1",
    "generador-evento-escritor.css": "1",
    "generador-evento-escritor.js": "1",
    "herramientas-index.css": "1",
    "jsonld-escritores.css": "1",
    "jsonld-escritores.js": "1",
    "kit-prensa-escritor.css": "1",
    "kit-prensa-escritor.js": "2",
    "legibilidad-espanol.css": "1",
    "legibilidad-espanol.js": "1",
    "limpiador-manuscritos-engine.js": "1",
    "limpiador-manuscritos.js": "1",
    "analizador-capitulos.css": "1",
    "analizador-capitulos.js": "2",
    "metadatos-libro.css": "1",
    "metadatos-libro.js": "2",
    "nombres-personajes.css": "1",
    "nombres-personajes-engine-compat.js": "1",
    "nombres-personajes.js": "1",
    "mapa-personajes.css": "2",
    "mapa-personajes.js": "2",
    "tipo-lector.css": "2",
    "tipo-lector-engine.js": "1",
    "tipo-lector.js": "1",
    "repeticiones-espanol.css": "1",
    "repeticiones-espanol.js": "2",
    "tarjeta-estoy-leyendo.js": "1",
    "tiempo-lectura-voz-alta.css": "1",
    "tiempo-lectura-voz-alta.js": "2",
    "variedad-lexica.css": "1",
    "variedad-lexica.js": "1",
    "v1-fragments.css": "1",
    "v1-fragments.js": "1",
    "manecillas-funnel.js": "1",
    "manecillas-book.js": "1",
    "v1-editorial-interior-v4.js": "1",
    "reading-list.css": "1",
    "v1-samuel.css": "2",
    "samuel-quiz.js": "2",
    "samuel-buy-modal.js": "1",
    "v1-awards.css": "1",
    "v1-press.css": "1",
    "objeto-heredado.css": "1",
    "objeto-heredado.js": "1",
    "writer-tools.js": "1",
}

# Anchored to an actual href="..."/src="..." attribute value, not a bare
# filename match: several pages mention asset filenames in prose/comments
# (e.g. "Pre-rendered to match assets/v1-editorial-interior-v4.js's
# buildContextNav()") that are not a real <script>/<link> load and must not
# be flagged as unversioned. Anchoring on href=/src= (rather than requiring
# a leading "/" before "assets/", as this used to) also catches root-relative
# refs missing the leading slash -- confirmed live: index.html links
# "assets/v1-shell.css" etc. with no leading "/", which the old /assets/-only
# pattern silently never matched at all, so this script reported "OK" while
# never actually checking a single asset reference on the homepage.
REF_RE = re.compile(r'(?:href|src)=["\']\.?/?assets/(' + '|'.join(re.escape(a) for a in TRACKED_ASSETS) + r')(\?v=([a-zA-Z0-9_.-]+))?(["\'])')


def git_tracked_html():
    result = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            yield ROOT / line


def sha256_of(path: Path) -> str:
    # Normalize line endings before hashing: this repo's local checkouts use
    # core.autocrlf=true (CRLF on disk on Windows), while GitHub Actions
    # checks out the same git-stored LF blob as-is on Linux. Hashing raw
    # bytes made every single text asset "fail" in CI on the very first run
    # of this guardrail (same content, different line-ending bytes) --
    # caught by actually running this PR's own CI, not just locally.
    raw = path.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def resolve_asset_path(asset: str) -> Path | None:
    """Most tracked assets live under assets/, but script.js and styles.css
    are served from the repo root -- REF_RE only ever matches /assets/...
    references so it never touched these two, but the hash guardrail needs
    the real file regardless of where each one lives."""
    under_assets = ROOT / "assets" / asset
    if under_assets.exists():
        return under_assets
    at_root = ROOT / asset
    if at_root.exists():
        return at_root
    return None


def load_hash_lock() -> dict[str, dict[str, str]]:
    if not HASH_LOCK_PATH.exists():
        return {}
    return json.loads(HASH_LOCK_PATH.read_text(encoding="utf-8"))


def update_hashes() -> int:
    """Records a hash for every TRACKED_ASSETS entry whose current version
    has no matching lockfile entry yet -- i.e. a version a human just
    bumped. Never touches an already-recorded (asset, version) pair, so
    running this can't paper over an actual content/version mismatch;
    that always needs a real version bump first."""
    lock = load_hash_lock()
    updated = []
    for asset, version in TRACKED_ASSETS.items():
        asset_path = resolve_asset_path(asset)
        if asset_path is None:
            print(f"SKIP {asset}: file not found under assets/ or repo root", file=sys.stderr)
            continue
        entry = lock.get(asset)
        if entry is not None and entry.get("version") == version:
            continue  # already recorded for this exact version
        lock[asset] = {"version": version, "sha256": sha256_of(asset_path)}
        updated.append(f"{asset}?v={version}")

    HASH_LOCK_PATH.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if updated:
        print(f"Recorded {len(updated)} new hash(es): {', '.join(updated)}")
        print(f"Commit {HASH_LOCK_PATH.relative_to(ROOT)} alongside your change.")
    else:
        print("No new versions to record; lockfile already up to date.")
    return 0


def check_hashes() -> list[str]:
    lock = load_hash_lock()
    errors = []
    for asset, version in TRACKED_ASSETS.items():
        asset_path = resolve_asset_path(asset)
        if asset_path is None:
            errors.append(f"{asset}: file referenced in TRACKED_ASSETS but does not exist under assets/ or repo root")
            continue
        entry = lock.get(asset)
        if entry is None or entry.get("version") != version:
            errors.append(
                f"assets/{asset}: no recorded hash for ?v={version} in {HASH_LOCK_PATH.name} "
                f"-- run `python {Path(__file__).name} --update-hashes` after bumping this version and commit the result"
            )
            continue
        current_hash = sha256_of(asset_path)
        if current_hash != entry.get("sha256"):
            errors.append(
                f"assets/{asset}: file content changed but ?v={version} was not bumped "
                f"(hash {current_hash[:12]}... != recorded {entry.get('sha256', '?')[:12]}...)"
            )
    return errors


def main() -> int:
    if "--update-hashes" in sys.argv:
        return update_hashes()

    errors = []
    scanned = 0
    for path in git_tracked_html():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        rel = path.relative_to(ROOT)
        matches = REF_RE.findall(text)
        if not matches:
            continue
        scanned += 1
        for asset, _qs, version, _quote in matches:
            canonical = TRACKED_ASSETS[asset]
            if not version:
                errors.append(f"{rel}: {asset} loaded with no ?v= at all")
            elif version != canonical:
                errors.append(f"{rel}: {asset}?v={version} (expected ?v={canonical})")

    errors.extend(check_hashes())

    if errors:
        print(f"FAIL — {len(errors)} issue(s) across {scanned} page(s) checked:")
        for e in errors:
            print(f"- {e}")
        return 1

    versions = ", ".join(f"{a}?v={v}" for a, v in TRACKED_ASSETS.items())
    print(f"OK — {scanned} page(s) checked, all tracked asset references and content hashes match ({versions}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
