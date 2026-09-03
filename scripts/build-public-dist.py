#!/usr/bin/env python3
"""Build and validate the browser-served artifact for davidportodiaz.com.

Security/publication model: ALLOWLIST-FIRST.

A tracked repository file is not public merely because nobody remembered to
exclude it. The public artifact is composed from explicitly classified web
roots/files, then narrowed by editorial gates and nested exclusions. This keeps
new operational material (docs, QA, migrations, Worker/Wrangler config, package
metadata, etc.) private by default while preserving the existing static runtime.

The same policy renders `.assetsignore` for Cloudflare staging. Staging currently
archives the repository root before Wrangler uploads static assets, so the
`.assetsignore` uses a root deny (`/*`) plus explicit negations for approved
public roots. Cloudflare documents `.assetsignore` as `.gitignore`-format.

Usage:
  python scripts/build-public-dist.py
  python scripts/build-public-dist.py --out dist
  python scripts/build-public-dist.py --check-contents --out dist
  python scripts/build-public-dist.py --emit-assetsignore
  python scripts/build-public-dist.py --check-assetsignore
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".preview-dist"

GATED_REGISTRY_STATUS = {"noindex", "internal", "gated", "deprecated"}

# Approved public namespaces. Adding a new top-level repository directory does
# NOT publish it. A new public content family must be classified here explicitly.
PUBLIC_DIR_PREFIXES = (
    "accesibilidad/",
    "ai/",
    "asistente/",
    "assets/",
    "clubes-de-lectura/",
    "convocatorias-escritores/",
    "cuaderno/",
    "editoriales/",
    "empieza-aqui/",
    "fragmento/",
    "gracias-suscripcion/",
    "herramientas/",
    "las-manecillas-del-recuerdo/",
    "lectores-beta/",
    "libros/",
    "mapa-del-sitio/",
    "metodologia-editorial/",
    "pagefind/",
    "press-kit/",
    "recomendaciones/",
    "recursos/",
    "universo/",
)

# Public root files with a concrete browser, SEO, PWA, legacy-route,
# verification or licensing purpose. Root HTML pages are explicit too: a new
# arbitrary root file cannot become public accidentally.
PUBLIC_ROOT_FILES = {
    "404.html",
    "59347d39b5684876a7ccc84382f31758.txt",
    "CNAME",
    "THIRD_PARTY_NOTICE_SILABAJS.md",
    "autor.html",
    "aviso-legal.html",
    "editoriales-sitemap.xml",
    "eventos.html",
    "favicon.ico",
    "ferias.html",
    "humans.txt",
    "index.html",
    "llms-full.txt",
    "llms.txt",
    "manifest.json",
    "offline.html",
    "premios.html",
    "prensa.html",
    "privacidad.html",
    "robots.txt",
    "samuel-entre-mundos.html",
    "script.js",
    "service-worker.js",
    "sitemap.xml",
    "styles.css",
}

# These live inside otherwise-public namespaces but are build/source material.
PUBLIC_EXCLUDED_DIR_PREFIXES = (
    "assets/manecillas/source/",
    "assets/no usadas/",
)

CAMPAIGN_SOCIAL_ASSETS = (
    "assets/manecillas-social-4x5-aviso.webp",
    "assets/manecillas-social-4x5-disponible.webp",
    "assets/manecillas-social-story-9x16.webp",
)

PUBLIC_EXCLUDED_FILES = {
    "press-kit/package-manifest.json",  # packaging contract, not press content
    *CAMPAIGN_SOCIAL_ASSETS,
}

# Defense in depth inside otherwise-public namespaces. These classes are
# operational/configuration material, never browser-served runtime.
FORBIDDEN_BASENAME_PATTERNS = (
    "wrangler*.jsonc",
    "cloudflare-worker-*.js",
    "package.json",
    "package-lock.json",
    "lighthouserc*.json",
    "*.tfstate",
    ".env",
    ".env.*",
    # Internal engineering docs (ownership, QA commands, env var names,
    # activation architecture) never belong on the public site even when
    # they sit inside an otherwise-public directory. Found live: asistente/
    # README.md served 200 at davidportodiaz.com/asistente/README.md --
    # nothing here blocked bare README.md by basename, only specific
    # infra filenames. THIRD_PARTY_NOTICE_SILABAJS.md is a different
    # basename and stays public via its own PUBLIC_ROOT_FILES entry.
    "README.md",
)
FORBIDDEN_SUFFIXES = (".sql", ".pem", ".key")

# Equivalent gitignore-style patterns emitted after public namespace negations.
ASSETSIGNORE_FORBIDDEN_PATTERNS = (
    "**/wrangler*.jsonc",
    "**/cloudflare-worker-*.js",
    "**/package.json",
    "**/package-lock.json",
    "**/lighthouserc*.json",
    "**/*.tfstate",
    "**/.env",
    "**/.env.*",
    "**/*.sql",
    "**/*.pem",
    "**/*.key",
    "**/README.md",
)

REQUIRED_PUBLIC_FILES = (
    "index.html",
    "ai/index.html",
    "assets/v1-shell.css",
    "manifest.json",
    "service-worker.js",
    "offline.html",
    "robots.txt",
    "sitemap.xml",
    "llms.txt",
    "llms-full.txt",
    "pagefind/pagefind-ui.js",
    "press-kit/david-porto-diaz.json",
    "press-kit/las-manecillas-del-recuerdo.json",
    "press-kit/samuel-entre-mundos.json",
)

ALLOWED_MANIFEST_CATEGORIES = {
    "page",
    "runtime-asset",
    "machine-readable",
    "verification",
    "license",
}


def registry_data(root: Path) -> dict:
    path = root / "data" / "content-registry.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def registry_entries(root: Path) -> list[dict]:
    return registry_data(root).get("entries", [])


def registry_status(entry: dict, data: dict) -> str:
    defaults = data.get("defaults", {})
    return entry.get("status", defaults.get("status", "public"))


def gated_prefixes_from_registry(root: Path) -> tuple[str, ...]:
    """Directories whose registry status says they must not be published."""
    data = registry_data(root)
    prefixes: set[str] = set()
    for entry in data.get("entries", []):
        if registry_status(entry, data) not in GATED_REGISTRY_STATUS:
            continue
        source_file = entry.get("sourceFile")
        if not source_file:
            continue
        parent = str(Path(source_file).parent).replace("\\", "/")
        if parent != ".":
            prefixes.add(parent.rstrip("/") + "/")
    return tuple(sorted(prefixes))


def public_registry_sources(root: Path) -> tuple[str, ...]:
    data = registry_data(root)
    sources: set[str] = set()
    for entry in data.get("entries", []):
        if registry_status(entry, data) in GATED_REGISTRY_STATUS:
            continue
        source_file = entry.get("sourceFile")
        if source_file:
            sources.add(source_file.replace("\\", "/"))
    return tuple(sorted(sources))


def git_tracked_files(root: Path = ROOT) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def forbidden_reason(rel_path: str) -> str | None:
    rel_path = rel_path.replace("\\", "/").lstrip("./")
    path = Path(rel_path)
    basename = path.name
    for pattern in FORBIDDEN_BASENAME_PATTERNS:
        if fnmatch.fnmatch(basename, pattern):
            return f"forbidden tooling/infra class {pattern}"
    if basename.lower().endswith(FORBIDDEN_SUFFIXES):
        return f"forbidden suffix {path.suffix.lower()}"
    if rel_path == "editorial-facts.json":
        return "internal editorial contract"
    if rel_path == "press-kit/package-manifest.json":
        return "internal press-kit build manifest"
    return None


def is_publishable(rel_path: str, root: Path = ROOT) -> bool:
    rel_path = rel_path.replace("\\", "/").lstrip("./")
    if forbidden_reason(rel_path):
        return False
    if rel_path in PUBLIC_EXCLUDED_FILES:
        return False
    if any(rel_path.startswith(prefix) for prefix in PUBLIC_EXCLUDED_DIR_PREFIXES):
        return False
    if any(rel_path.startswith(prefix) for prefix in gated_prefixes_from_registry(root)):
        return False
    return rel_path in PUBLIC_ROOT_FILES or any(
        rel_path.startswith(prefix) for prefix in PUBLIC_DIR_PREFIXES
    )


def classify_public_artifact(rel_path: str) -> str:
    if rel_path == "THIRD_PARTY_NOTICE_SILABAJS.md":
        return "license"
    if rel_path in {"CNAME", "59347d39b5684876a7ccc84382f31758.txt"}:
        return "verification"
    if (
        rel_path.startswith("press-kit/")
        or rel_path in {"robots.txt", "sitemap.xml", "editoriales-sitemap.xml", "humans.txt", "llms.txt", "llms-full.txt"}
    ):
        return "machine-readable"
    if rel_path.endswith(".html"):
        return "page"
    return "runtime-asset"


def build(out_dir: Path, root: Path = ROOT) -> tuple[int, int]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    included = 0
    excluded = 0
    for rel in git_tracked_files(root):
        if not is_publishable(rel, root):
            excluded += 1
            continue
        src = root / rel
        if not src.exists():
            continue
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        included += 1
    return included, excluded


def write_manifest(out_dir: Path) -> Path:
    manifest_path = out_dir.with_name(out_dir.name + "-manifest.json")
    items = []
    for file_path in sorted(p for p in out_dir.rglob("*") if p.is_file()):
        rel = file_path.relative_to(out_dir).as_posix()
        category = classify_public_artifact(rel)
        if category not in ALLOWED_MANIFEST_CATEGORIES:
            raise RuntimeError(f"unclassified public artifact: {rel}")
        items.append({"path": rel, "category": category})
    manifest_path.write_text(
        json.dumps({"schemaVersion": 1, "files": items}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def check_contents(
    out_dir: Path,
    root: Path = ROOT,
    *,
    require_runtime: bool = True,
) -> int:
    """Validate a built tree.

    `require_runtime=False` is only for focused fixture tests that intentionally
    model a partial repository. Production/CLI checks remain strict by default.
    """
    if not out_dir.exists():
        print(f"FAIL: {out_dir} does not exist — run the builder first.", file=sys.stderr)
        return 1

    failures: list[str] = []
    files = [p for p in out_dir.rglob("*") if p.is_file()]
    rel_files = {p.relative_to(out_dir).as_posix() for p in files}

    for rel in sorted(rel_files):
        if not is_publishable(rel, root):
            failures.append(f"unclassified/non-public artifact present in dist: {rel}")
        reason = forbidden_reason(rel)
        if reason:
            failures.append(f"forbidden artifact present in dist: {rel} ({reason})")
        category = classify_public_artifact(rel)
        if category not in ALLOWED_MANIFEST_CATEGORIES:
            failures.append(f"artifact has no approved manifest category: {rel}")

    if require_runtime:
        for required in REQUIRED_PUBLIC_FILES:
            if required not in rel_files:
                failures.append(f"required public runtime artifact missing: {required}")

    # Every public registry source must survive the build; every gated source
    # must stay out. This prevents an allowlist change from silently dropping a
    # legitimate page while still enforcing editorial publication status.
    data = registry_data(root)
    for entry in data.get("entries", []):
        source_file = entry.get("sourceFile")
        if not source_file:
            continue
        source_file = source_file.replace("\\", "/")
        status = registry_status(entry, data)
        if status in GATED_REGISTRY_STATUS:
            if source_file in rel_files:
                failures.append(f"gated registry source present in dist: {source_file}")
        elif source_file not in rel_files:
            failures.append(f"public registry source missing from dist: {source_file}")

    if failures:
        print(f"FAIL — {len(failures)} public-artifact contract issue(s) in {out_dir}:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        f"OK: {out_dir} satisfies the allowlist-first public-artifact contract "
        f"({len(rel_files)} files)."
    )
    return 0


ASSETSIGNORE_HEADER = """# GENERADO por scripts/build-public-dist.py --emit-assetsignore — no editar a mano.
#
# Política allowlist-first. Cloudflare Wrangler documenta `.assetsignore` con
# formato `.gitignore`. Se ignora todo el root y se reabren únicamente los
# namespaces/ficheros clasificados como web pública. Un fichero técnico nuevo
# queda fuera por defecto, aunque nadie conozca todavía su nombre.
#
# Mantener sincronizado: python scripts/build-public-dist.py --check-assetsignore
"""


def assetsignore_lines(root: Path = ROOT) -> list[str]:
    lines = ["/*", ""]
    lines += [f"!/{name}" for name in sorted(PUBLIC_ROOT_FILES)]
    lines.append("")
    lines += [f"!/{prefix.rstrip('/')}/" for prefix in PUBLIC_DIR_PREFIXES]
    lines += [
        "",
        "# Exclusiones dentro de namespaces públicos.",
        *[f"/{prefix}" for prefix in PUBLIC_EXCLUDED_DIR_PREFIXES],
        *[f"/{name}" for name in sorted(PUBLIC_EXCLUDED_FILES)],
        *ASSETSIGNORE_FORBIDDEN_PATTERNS,
    ]
    gated = gated_prefixes_from_registry(root)
    if gated:
        lines += [
            "",
            "# Rutas gated derivadas de data/content-registry.json.",
            *[f"/{prefix}" for prefix in gated],
        ]
    return lines


def render_assetsignore(root: Path = ROOT) -> str:
    return ASSETSIGNORE_HEADER + "\n".join(assetsignore_lines(root)) + "\n"


def emit_assetsignore(root: Path, check_only: bool) -> int:
    path = root / ".assetsignore"
    expected = render_assetsignore(root)
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if check_only:
        if current == expected:
            print("OK: .assetsignore coincide con la allowlist pública del builder.")
            return 0
        reason = "no existe" if current is None else "está desincronizado"
        print(f"FAIL: .assetsignore {reason}. Regenera con --emit-assetsignore.")
        return 1
    path.write_text(expected, encoding="utf-8")
    print(f"ESCRITO {path} ({len(assetsignore_lines(root))} reglas).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--check-contents", action="store_true")
    ap.add_argument("--emit-assetsignore", action="store_true")
    ap.add_argument("--check-assetsignore", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = root / out_dir

    if args.emit_assetsignore or args.check_assetsignore:
        return emit_assetsignore(root, check_only=args.check_assetsignore)
    if args.check_contents:
        return check_contents(out_dir, root)

    included, excluded = build(out_dir, root)
    manifest_path = write_manifest(out_dir)
    print(
        f"BUILT {out_dir}: {included} file(s) included, {excluded} excluded; "
        f"manifest={manifest_path.name}"
    )
    return check_contents(out_dir, root)


if __name__ == "__main__":
    raise SystemExit(main())
