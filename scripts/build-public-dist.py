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
  python scripts/build-public-dist.py --emit-assetsignore  # regenerar
      .assetsignore desde estas mismas constantes
  python scripts/build-public-dist.py --check-assetsignore # (en CI) avisar
      si .assetsignore se ha desincronizado de estas constantes

Las piezas de campana para redes (CAMPAIGN_SOCIAL_ASSETS) quedan siempre
fuera del output publico: ninguna pagina las referencia, se suben a mano a
las redes desde el repo local. No hay ningun gate por fecha aqui -- ver el
comentario de esa constante para por que el anterior era una tarea manual
escondida disfrazada de automatismo.

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
  wired into any workflow by this pass.

STAGING (INTENTIONALLY_CHANGED respecto al plan original): el staging de
Cloudflare sigue construyendo con `git archive HEAD`, porque cambiar su
build command es un ajuste del dashboard y la Workers Builds API rechaza
tanto los tokens de cuenta como el OAuth de wrangler. Pero este script SI
afecta ya al staging real, de forma indirecta: `--emit-assetsignore` genera
el `.assetsignore` de la raiz del repo a partir de las MISMAS constantes de
exclusion de aqui abajo, `git archive` lo deposita en la raiz del directorio
de assets, y ahi `wrangler deploy --assets` lo respeta y no sube nada que
coincida. Verificado en vivo: scripts/, tests/, data/, .env.example,
lecturas/, publicar-web/, editorial-facts.json y cloudflare-worker-subscribe.js
pasaron de HTTP 200 a 404 en la preview sin tocar el dashboard.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".preview-dist"

# Estados del content-registry que significan "no debe llegar a produccion
# publica", a diferencia de status="public" (que puede tener searchIndex o
# sitemap en false -- p.ej. /privacidad.html -- pero SI debe ser accesible
# por URL). "noindex" no es un control de publicacion por si solo: aqui es
# la unica senal que SI lo es, derivada de una unica autoridad.
GATED_REGISTRY_STATUS = {"noindex", "internal", "gated", "deprecated"}


def gated_prefixes_from_registry(root: Path) -> tuple[str, ...]:
    """Deriva las rutas/directorios que NO deben llegar al dist publico a
    partir de la unica autoridad editorial (data/content-registry.json),
    en vez de mantener una segunda lista manual que pueda desincronizarse.
    Devuelve el directorio contenedor del sourceFile de cada entrada gated
    (p.ej. 'donde-empieza-la-jaula/index.html' -> 'donde-empieza-la-jaula/'),
    para que tambien queden fuera assets hermanos no registrados uno a uno.
    """
    registry_path = root / "data" / "content-registry.json"
    if not registry_path.exists():
        return ()
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    defaults = data.get("defaults", {})
    prefixes = set()
    for entry in data.get("entries", []):
        status = entry.get("status", defaults.get("status", "public"))
        if status not in GATED_REGISTRY_STATUS:
            continue
        source_file = entry.get("sourceFile")
        if not source_file:
            continue
        parent = str(Path(source_file).parent)
        prefixes.add("" if parent == "." else parent.replace("\\", "/") + "/")
    return tuple(sorted(p for p in prefixes if p))
# Piezas de campana para redes (4:5 y 9:16). NINGUNA pagina las referencia
# -- comprobado con git grep sobre *.html/*.css/*.js: cero referencias --, se
# suben a mano a Instagram/Facebook desde el repo local. Por tanto no son
# runtime web y se quedan FUERA del output publico de forma permanente.
#
# Antes la variante "disponible" estaba excluida solo hasta la fecha de
# publicacion, como si el 03/09 fuera a hacerse publica sola. No era cierto:
# Cloudflare construye con `git archive HEAD` y nunca ejecuta este generador,
# asi que el .assetsignore desplegado es el que este commiteado. Eso convertia
# el "gate" en una tarea manual escondida justo el dia del lanzamiento --
# exactamente lo que se queria evitar. Como el asset no necesita ser publico
# NUNCA, el gate temporal desaparece en vez de automatizarse.
CAMPAIGN_SOCIAL_ASSETS = (
    "assets/manecillas-social-4x5-aviso.webp",
    "assets/manecillas-social-4x5-disponible.webp",
    "assets/manecillas-social-story-9x16.webp",
)

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


def git_tracked_files(root: Path = ROOT) -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_excluded(rel_path: str, gated_prefixes: tuple[str, ...] = ()) -> bool:
    if rel_path in EXCLUDE_FILES or rel_path in CAMPAIGN_SOCIAL_ASSETS:
        return True
    if any(rel_path.startswith(prefix) for prefix in EXCLUDE_DIR_PREFIXES):
        return True
    return any(rel_path.startswith(prefix) for prefix in gated_prefixes)


def build(out_dir: Path, root: Path = ROOT) -> tuple[int, int]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    gated_prefixes = gated_prefixes_from_registry(root)
    included, excluded = 0, 0

    for rel in git_tracked_files(root):
        if is_excluded(rel, gated_prefixes):
            excluded += 1
            continue
        src = root / rel
        if not src.exists():
            continue  # tracked but not on disk locally (shouldn't happen, but don't crash)
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        included += 1

    return included, excluded


def check_contents(out_dir: Path, root: Path = ROOT) -> int:
    if not out_dir.exists():
        print(f"FAIL: {out_dir} does not exist — run the builder first.", file=sys.stderr)
        return 1
    failures = []
    for prefix in EXCLUDE_DIR_PREFIXES:
        if (out_dir / prefix).exists():
            failures.append(f"excluded directory present in dist: {prefix}")
    for fname in EXCLUDE_FILES:
        if (out_dir / fname).exists():
            failures.append(f"excluded file present in dist: {fname}")
    for asset in CAMPAIGN_SOCIAL_ASSETS:
        if (out_dir / asset).exists():
            failures.append(f"campaign social asset present in public dist: {asset}")
    # Deuda 2/3: la comprobacion de publicabilidad se deriva de la MISMA
    # autoridad (content-registry.json), no de una lista paralela. Si una
    # ruta gated (status != public) aparece en el arbol publico -- aunque su
    # propio HTML declare <meta name="robots" content="noindex">, que no es
    # un control de acceso -- el gate falla.
    for prefix in gated_prefixes_from_registry(root):
        if (out_dir / prefix).exists():
            failures.append(f"gated/staging route present in public dist (content-registry status != public): {prefix}")

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


def assetsignore_lines() -> list[str]:
    lines = [p.rstrip("/") + "/" for p in EXCLUDE_DIR_PREFIXES]
    lines += sorted(EXCLUDE_FILES)
    lines.append(".assetsignore")
    lines.append("")
    lines.append("# Piezas de campana para redes: no las usa ninguna pagina, se suben a")
    lines.append("# mano desde el repo local. Permanentes, sin fecha: no hay nada que")
    lines.append("# 'liberar' el dia del lanzamiento.")
    lines += list(CAMPAIGN_SOCIAL_ASSETS)
    gated = gated_prefixes_from_registry(ROOT)
    if gated:
        lines.append("")
        lines.append("# Rutas gated/staging derivadas de data/content-registry.json (status !=")
        lines.append("# public): el staging real de Cloudflare tambien debe respetarlas, no solo")
        lines.append("# el .preview-dist local.")
        lines += [p.rstrip("/") + "/" for p in gated]
    return lines


def render_assetsignore() -> str:
    return ASSETSIGNORE_HEADER + "\n".join(assetsignore_lines()) + "\n"


def emit_assetsignore(check_only: bool) -> int:
    expected = render_assetsignore()
    current = ASSETSIGNORE.read_text(encoding="utf-8") if ASSETSIGNORE.exists() else None
    if check_only:
        if current == expected:
            print("OK: .assetsignore coincide con las exclusiones de este builder.")
            return 0
        reason = "no existe" if current is None else "está desincronizado"
        print(f"FAIL: .assetsignore {reason}. Regenera con --emit-assetsignore.")
        return 1
    ASSETSIGNORE.write_text(expected, encoding="utf-8")
    print(f"ESCRITO {ASSETSIGNORE} ({len(assetsignore_lines())} reglas).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT), help="Repo root to read git-tracked files and content-registry.json from (default: real repo root; override only for isolated tests)")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--check-contents", action="store_true", help="Verify an already-built dist, don't rebuild")
    ap.add_argument("--emit-assetsignore", action="store_true", help="Write .assetsignore from this builder's exclude list")
    ap.add_argument("--check-assetsignore", action="store_true", help="Verify .assetsignore matches the exclude list")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = root / out_dir


    if args.emit_assetsignore or args.check_assetsignore:
        return emit_assetsignore(check_only=args.check_assetsignore)

    if args.check_contents:
        return check_contents(out_dir, root)

    included, excluded = build(out_dir, root)
    gate_note = ""
    print(f"BUILT {out_dir}: {included} file(s) included, {excluded} excluded{gate_note}")
    return check_contents(out_dir, root)


if __name__ == "__main__":
    raise SystemExit(main())
