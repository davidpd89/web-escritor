#!/usr/bin/env python3
"""Build a safe public-output tree (default: .preview-dist/) containing
ONLY what should actually be served to a browser — not the full
`git archive HEAD` the staging deploy currently uses, which also ships
scripts/, tests/, data/ (build-time sources), internal docs, etc.

Architecture: default-INCLUDE every git-tracked file, then subtract a
short, explicit, reviewed EXCLUDE list — never the other way around.
An allowlist risks silently dropping something a runtime page actually
needs; a reviewed denylist, checked by `--check-contents` below, is
safer and matches this project's "no excluyas datos a ciegas" rule.

Usage:
  python scripts/build-public-dist.py                 # build .preview-dist/
  python scripts/build-public-dist.py --out dist       # custom output dir
  python scripts/build-public-dist.py --check-contents # verify an already
      -built dist dir contains none of the excluded categories (does not
      rebuild; run build first)
  python scripts/build-public-dist.py --date 2026-09-05 # override "today"
      for the manecillas-social-4x5-disponible.webp launch gate (testing
      only; real runs use the real date, same convention as
      apply-manecillas-launch-state.py)

Launch gate: assets/manecillas-social-4x5-disponible.webp stays tracked
in git (it's a prepared, reviewed asset) but is excluded from the public
dist until the actual publication date, so it can never accidentally be
public before the book is out. Everything else that should be gated by
launch date is a separate, human, day-of task — this only protects the
one specific pre-built "now available" social asset.

PRODUCTION OPTIONS (documented only — NOT implemented, GitHub Pages
production is untouched by this script):

  A) Jekyll `exclude:` in a new `_config.yml` at repo root. GitHub Pages
     runs Jekyll by default on a plain repo, and a `_config.yml` with an
     `exclude:` list (mirroring EXCLUDE_DIR_PREFIXES/EXCLUDE_FILES above)
     would stop Pages from publishing scripts/tests/data/etc. Real risk:
     Jekyll processes some file types (front-matter, liquid tags) even
     when not asked to, and a repo with ~550 already-static HTML files
     has not been tested end-to-end under Jekyll's build - a wrong
     exclude or an unexpected Jekyll transform could break pages in
     production with no local warning. Must be tested against a full
     branch preview (e.g. this same Cloudflare Pages staging setup
     pointed at a Jekyll-built output) before ever touching the real
     `main` Pages deploy.

  B) A GitHub Actions workflow that runs this script and deploys
     .preview-dist/ (via actions/upload-pages-artifact +
     actions/deploy-pages, replacing the current implicit "serve the
     branch root" GitHub Pages behavior). Cleaner and more explicit than
     option A (no Jekyll surprises, this exact script is what runs),
     but changes the deploy mechanism itself, which needs a deliberate,
     tested cutover, not a silent switch.

  Both require a human decision and a tested rollout plan; neither is
  wired into any workflow by this pass. The current staging Cloudflare
  Pages preview build (david-porto-preview.davidpd89.workers.dev) is a
  separate, already-working preview channel with its own build - this
  script does not change how that staging deploy currently sources its
  files unless/until someone wires it to consume .preview-dist/ instead
  of `git archive HEAD`.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".preview-dist"
MADRID = ZoneInfo("Europe/Madrid")
MANECILLAS_PUBLICATION_DATE = date(2026, 9, 3)
GATED_DISPONIBLE_ASSET = "assets/manecillas-social-4x5-disponible.webp"

# Directories excluded wholesale (any tracked file whose path starts with
# one of these, using posix-style forward slashes).
EXCLUDE_DIR_PREFIXES = (
    ".claude/",
    ".github/",
    "scripts/",
    "tests/",
    "data/",
    "assets/manecillas/source/",
    "publicar-web/",  # internal build checklist, noindex (point 12)
    "lecturas/",  # fixture content, noindex (point 13)
)

# Individual files excluded by exact repo-relative path.
EXCLUDE_FILES = {
    ".env.example",
    ".gitignore",
    ".lycheeignore",
    ".pa11yci",
    "lighthouserc.json",
    "README.md",
    "editorial-facts.json",  # build-time canonical facts, not fetched by any runtime JS (verified)
    "cloudflare-worker-subscribe.js",  # Cloudflare Worker source, deployed separately, never served by the web host
}


def git_tracked_files() -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_excluded(rel_path: str) -> bool:
    if rel_path in EXCLUDE_FILES:
        return True
    return any(rel_path.startswith(prefix) for prefix in EXCLUDE_DIR_PREFIXES)


def resolve_today(date_arg: str | None) -> date:
    if date_arg:
        return date.fromisoformat(date_arg)
    return __import__("datetime").datetime.now(MADRID).date()


def build(out_dir: Path, today: date) -> tuple[int, int]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    included, excluded = 0, 0
    launch_gated = today < MANECILLAS_PUBLICATION_DATE

    for rel in git_tracked_files():
        if is_excluded(rel):
            excluded += 1
            continue
        if rel == GATED_DISPONIBLE_ASSET and launch_gated:
            excluded += 1
            continue
        src = ROOT / rel
        if not src.exists():
            continue  # tracked but not on disk locally (shouldn't happen, but don't crash)
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        included += 1

    return included, excluded


def check_contents(out_dir: Path, today: date | None = None) -> int:
    if not out_dir.exists():
        print(f"FAIL: {out_dir} does not exist — run the builder first.", file=sys.stderr)
        return 1
    if today is None:
        today = resolve_today(None)
    failures = []
    for prefix in EXCLUDE_DIR_PREFIXES:
        if (out_dir / prefix).exists():
            failures.append(f"excluded directory present in dist: {prefix}")
    for fname in EXCLUDE_FILES:
        if (out_dir / fname).exists():
            failures.append(f"excluded file present in dist: {fname}")
    if today < MANECILLAS_PUBLICATION_DATE and (out_dir / GATED_DISPONIBLE_ASSET).exists():
        failures.append(f"launch-gated asset present before publication date: {GATED_DISPONIBLE_ASSET}")

    if failures:
        print(f"FAIL — {len(failures)} issue(s) in {out_dir}:")
        for f in failures:
            print(f"- {f}")
        return 1
    print(f"OK: {out_dir} contains none of the excluded categories.")
    return 0


ASSETSIGNORE = ROOT / ".assetsignore"
ASSETSIGNORE_HEADER = """# GENERADO por scripts/build-public-dist.py --emit-assetsignore — no editar a mano.
#
# Por qué existe: el build de staging en Cloudflare hace `git archive HEAD` a
# .preview-dist y despliega esa carpeta con `wrangler deploy --assets`, así que
# hasta ahora subía TODO el repo trackeado (scripts/, tests/, data/, ...).
# Cambiar ese comando de build es un ajuste del dashboard de Cloudflare, y la
# Builds API no acepta tokens de cuenta ni OAuth de wrangler. Pero wrangler sí
# respeta un .assetsignore (sintaxis .gitignore) en la raíz del directorio de
# assets, y `git archive` deposita este archivo exactamente ahí. Resultado: las
# mismas exclusiones que build-public-dist.py, aplicadas en el despliegue real,
# sin depender de que nadie toque el dashboard.
#
# Mantener sincronizado: python scripts/build-public-dist.py --check-assetsignore
"""


def assetsignore_lines(today: date) -> list[str]:
    lines = [p.rstrip("/") + "/" for p in EXCLUDE_DIR_PREFIXES]
    lines += sorted(EXCLUDE_FILES)
    lines.append(".assetsignore")
    if today < MANECILLAS_PUBLICATION_DATE:
        # OJO: en sintaxis .gitignore el '#' solo abre comentario a principio
        # de línea; un comentario al final formaría parte del patrón y la regla
        # no coincidiría con nada. Va en su propia línea.
        lines.append(
            f"# LAUNCH GATE: regenerar sin esta regla el {MANECILLAS_PUBLICATION_DATE:%d/%m/%Y}"
        )
        lines.append(GATED_DISPONIBLE_ASSET)
    return lines


def render_assetsignore(today: date) -> str:
    return ASSETSIGNORE_HEADER + "\n".join(assetsignore_lines(today)) + "\n"


def emit_assetsignore(today: date, check_only: bool) -> int:
    expected = render_assetsignore(today)
    current = ASSETSIGNORE.read_text(encoding="utf-8") if ASSETSIGNORE.exists() else None
    if check_only:
        if current == expected:
            print("OK: .assetsignore coincide con las exclusiones de este builder.")
            return 0
        reason = "no existe" if current is None else "está desincronizado"
        print(f"FAIL: .assetsignore {reason}. Regenera con --emit-assetsignore.")
        return 1
    ASSETSIGNORE.write_text(expected, encoding="utf-8")
    print(f"ESCRITO {ASSETSIGNORE} ({len(assetsignore_lines(today))} reglas).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--check-contents", action="store_true", help="Verify an already-built dist, don't rebuild")
    ap.add_argument("--emit-assetsignore", action="store_true", help="Write .assetsignore from this builder's exclude list")
    ap.add_argument("--check-assetsignore", action="store_true", help="Verify .assetsignore matches the exclude list")
    ap.add_argument("--date", help="YYYY-MM-DD, for testing the launch gate only")
    args = ap.parse_args()

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir

    today = resolve_today(args.date)

    if args.emit_assetsignore or args.check_assetsignore:
        return emit_assetsignore(today, check_only=args.check_assetsignore)

    if args.check_contents:
        return check_contents(out_dir, today)

    included, excluded = build(out_dir, today)
    gate_note = " (launch gate ACTIVE — disponible asset withheld)" if today < MANECILLAS_PUBLICATION_DATE else ""
    print(f"BUILT {out_dir}: {included} file(s) included, {excluded} excluded{gate_note}")
    return check_contents(out_dir, today)


if __name__ == "__main__":
    raise SystemExit(main())
