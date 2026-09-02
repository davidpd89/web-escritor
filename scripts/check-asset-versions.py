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

This checker has two things it can be pointed at:
  1. The current canonical version per asset, read from TRACKED_ASSETS
     below (kept here instead of a separate config file so there is
     exactly one place to bump each — update the relevant entry AND run
     this checker as part of any release that changes that asset).
  2. Every git-tracked HTML file's actual references to each asset.

Usage:
  python scripts/check-asset-versions.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Bump the relevant entry — and only that entry — when cutting a release
# that changes the given asset. Then run this checker; it will list every
# page still on the old version, or still completely unversioned.
TRACKED_ASSETS = {
    "script.js": "202609-launch-1",
    "styles.css": "202609-launch-1",
    "v1-fonts.css": "1",
    "v1-home.css": "10",
    "v1-tokens.css": "1",
    "v1-base.css": "1",
    "v1-shell-base.css": "1",
    "v1-shell-lrb-v2.css": "1",
    "v1-lrb-material-v2.css": "1",
    "v1-home-editorial-v3.css": "1",
    "v1-editorial-interior-v4.css": "1",
    "v1-editorial-interactions-v4.css": "1",
    "v1-site-cohesion-v6.css": "1",
    "v1-reflow-hardening-v7.css": "1",
    "v1-shell.css": "1",
    "v1-shell.js": "1",
    "v1-components.css": "2",
    "v1-families.css": "1",
    "newsletter-general.js": "1",
    "v1-tools.css": "1",
    "v1-tools-identity.css": "1",
    "v1-editorial.css": "1",
    "v1-editorial.js": "1",
    "newsletter-popup.css": "1",
    "newsletter-popup.js": "1",
    "v1-no-js-pending.css": "1",
    "cuaderno-index.css": "1",
    "editoriales.css": "1",
    "v1-identity.css": "1",
    "v1-tools-publishing.css": "1",
    "v1-recommendations.css": "1",
    "v1-findability.css": "1",
    "v1-book.css": "1",
    "v1-editoriales-detail.css": "1",
    "assistant.css": "1",
    "assistant.js": "1",
    "v1-legal.css": "1",
    "noveris.css": "1",
    "v1-cuaderno-topics.css": "1",
    "dialogo-espanol.js": "1",
    "v1-beta-readers.css": "1",
    "v1-accessibility-statement.css": "1",
    "v1-ai-authority.css": "1",
    "assistant-embed.css": "2",
    "assistant-embed.js": "1",
    "club-session-builder.css": "1",
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
    "contador-palabras-engine.js": "1",
    "contador-palabras.js": "1",
    "dialogo-convenciones.js": "1",
    "dialogo-espanol.css": "1",
    "pov-distribucion.css": "1",
    "pov-distribucion-engine.js": "1",
    "pov-distribucion.js": "1",
    "entrevista-familiar.css": "1",
    "entrevista-familiar.js": "1",
    "generador-evento-escritor.css": "1",
    "generador-evento-escritor.js": "1",
    "herramientas-index.css": "1",
    "jsonld-escritores.css": "1",
    "jsonld-escritores.js": "1",
    "kit-prensa-escritor.css": "1",
    "kit-prensa-escritor.js": "1",
    "legibilidad-espanol.css": "1",
    "legibilidad-espanol.js": "1",
    "limpiador-manuscritos-engine.js": "1",
    "limpiador-manuscritos.js": "1",
    "analizador-capitulos.css": "1",
    "analizador-capitulos.js": "1",
    "metadatos-libro.css": "1",
    "metadatos-libro.js": "2",
    "nombres-personajes.css": "1",
    "nombres-personajes-engine-compat.js": "1",
    "nombres-personajes.js": "1",
    "mapa-personajes.css": "1",
    "mapa-personajes.js": "1",
    "tipo-lector.css": "1",
    "tipo-lector-engine.js": "1",
    "tipo-lector.js": "1",
    "repeticiones-espanol.css": "1",
    "repeticiones-espanol.js": "1",
    "tarjeta-estoy-leyendo.js": "1",
    "tiempo-lectura-voz-alta.css": "1",
    "tiempo-lectura-voz-alta.js": "1",
    "variedad-lexica.css": "1",
    "variedad-lexica.js": "1",
    "v1-fragments.css": "1",
    "v1-fragments.js": "1",
    "manecillas-funnel.js": "1",
    "manecillas-book.js": "1",
    "v1-editorial-interior-v4.js": "1",
    "reading-list.css": "1",
    "v1-samuel.css": "1",
    "samuel-quiz.js": "1",
    "samuel-buy-modal.js": "1",
    "v1-awards.css": "1",
    "v1-press.css": "1",
    "objeto-heredado.css": "1",
    "objeto-heredado.js": "1",
    "writer-tools.js": "1",
}

# Anchored to an actual /assets/... attribute value (opening prefix +
# closing quote), not a bare filename match: several pages mention asset
# filenames in prose/comments (e.g. "Pre-rendered to match assets/
# v1-editorial-interior-v4.js's buildContextNav()") that are not a real
# <script>/<link> load and must not be flagged as unversioned.
REF_RE = re.compile(r'/assets/(' + '|'.join(re.escape(a) for a in TRACKED_ASSETS) + r')(\?v=([a-zA-Z0-9_.-]+))?(["\'])')


def git_tracked_html():
    result = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True, check=True)
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            yield ROOT / line


def main() -> int:
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

    if errors:
        print(f"FAIL — {len(errors)} inconsistent/unversioned asset reference(s) across {scanned} page(s) checked:")
        for e in errors:
            print(f"- {e}")
        return 1

    versions = ", ".join(f"{a}?v={v}" for a, v in TRACKED_ASSETS.items())
    print(f"OK — {scanned} page(s) checked, all tracked asset references match ({versions}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
