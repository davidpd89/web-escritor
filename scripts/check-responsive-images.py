#!/usr/bin/env python3
"""Gate de imagenes responsive para HTML publico (H.3, 2026-08-23).

Clasifica, sin aplicar arreglos mecanicos, incumplimientos objetivos de la
politica de imagenes editoriales:

  - MISSING_DIMENSIONS: <img> de contenido sin width/height (provoca CLS:
    el navegador no puede reservar el espacio antes de que la imagen
    cargue). Se excluyen iconos/SVG/decorativos/muy pequenos a proposito
    -- ver EXCLUDE_* mas abajo -- para no generar falsos positivos.
  - SRCSET_WITHOUT_SIZES: <img>/<source> con srcset de varios anchos (con
    descriptor `w`) pero sin atributo sizes -- sin sizes, el navegador no
    puede elegir bien el candidato antes de conocer el layout final.
  - BROKEN_SRCSET_CANDIDATE: un candidato de srcset apunta a un fichero
    que no existe en disco.
  - INCOHERENT_LOADING: fetchpriority="high" combinado con loading="lazy"
    en la misma imagen (contradiccion directa: pedir prioridad alta y
    diferir la carga a la vez no tiene sentido).

No se marcan output de FALSOS POSITIVOS conocidos:
  - <img> dentro de <svg>, con role="presentation"/aria-hidden="true".
  - Extensión .svg (vectorial, no necesita width/height para CLS igual
    que un raster, y muchos se dimensionan por CSS a proposito).
  - Imagenes con ambas dimensiones ya pequenas en el propio markup segun
    otros indicios (data-icon, class que contenga "icon"/"avatar"/"logo").

Python standard library only.

Usage:
    python scripts/check-responsive-images.py              # inventario completo
    python scripts/check-responsive-images.py --check       # exit 1 si hay incumplimientos
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent.parent

SKIP_PARTS = {
    ".git", "node_modules", "WEB DAVID PORTO nuevas ideas", "archive",
    ".codex_work", ".preview-dist", "dist", "lab",
}

IMG_TAG_RE = re.compile(r"<img\b([^>]*)>", re.I)
SOURCE_TAG_RE = re.compile(r"<source\b([^>]*)>", re.I)
ATTR_RE = re.compile(r'([a-zA-Z_-]+)\s*=\s*"([^"]*)"')
ROBOTS_NOINDEX_RE = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']*)["\']', re.I)

ICON_CLASS_HINTS = ("icon", "avatar", "logo", "badge", "emoji")


def parse_attrs(raw: str) -> dict[str, str]:
    return {k.lower(): v for k, v in ATTR_RE.findall(raw)}


def is_noindex(html: str) -> bool:
    m = ROBOTS_NOINDEX_RE.search(html)
    return bool(m and "noindex" in m.group(1).lower())


def is_decorative_or_icon(attrs: dict[str, str], src: str) -> bool:
    if attrs.get("role") == "presentation":
        return True
    if attrs.get("aria-hidden", "").lower() == "true":
        return True
    if src.lower().endswith(".svg"):
        return True
    cls = attrs.get("class", "").lower()
    if any(hint in cls for hint in ICON_CLASS_HINTS):
        return True
    # Iconos/favicons/emblemas tipicos: ambas dimensiones declaradas y
    # pequenas ya es una senal fuerte de que no es contenido editorial.
    try:
        w = int(attrs.get("width", "0") or 0)
        h = int(attrs.get("height", "0") or 0)
        if 0 < w <= 32 and 0 < h <= 32:
            return True
    except ValueError:
        pass
    return False


def resolve_local(url: str, html_path: Path, root: Path) -> Path | None:
    url = url.strip()
    if not url or url.startswith(("http://", "https://", "data:", "//")):
        return None
    clean = unquote(urlparse(url).path)
    if clean.startswith("/"):
        return root / clean.lstrip("/")
    return (html_path.parent / clean).resolve()


def parse_srcset(value: str) -> list[tuple[str, str]]:
    """Devuelve [(url, descriptor)] -- descriptor puede ser '' si no lo lleva."""
    out = []
    for candidate in value.split(","):
        candidate = candidate.strip()
        if not candidate:
            continue
        parts = candidate.split()
        url = parts[0]
        descriptor = parts[1] if len(parts) > 1 else ""
        out.append((url, descriptor))
    return out


def audit_file(path: Path, root: Path) -> list[str]:
    html = path.read_text(encoding="utf-8", errors="replace")
    if is_noindex(html):
        return []  # el gate cubre superficie publica indexable
    rel = path.relative_to(root).as_posix()
    errors: list[str] = []

    for match in IMG_TAG_RE.finditer(html):
        attrs = parse_attrs(match.group(1))
        src = attrs.get("src", "")
        line = html.count("\n", 0, match.start()) + 1

        if not is_decorative_or_icon(attrs, src):
            if not attrs.get("width") or not attrs.get("height"):
                errors.append(f"{rel}:{line}: MISSING_DIMENSIONS img sin width/height: {src or '(sin src)'}")

        loading = attrs.get("loading", "").lower()
        fetchpriority = attrs.get("fetchpriority", "").lower()
        if loading == "lazy" and fetchpriority == "high":
            errors.append(f"{rel}:{line}: INCOHERENT_LOADING loading=lazy junto a fetchpriority=high: {src}")

        srcset = attrs.get("srcset", "")
        if srcset:
            candidates = parse_srcset(srcset)
            has_width_descriptor = any(d.endswith("w") for _, d in candidates)
            if has_width_descriptor and not attrs.get("sizes"):
                errors.append(f"{rel}:{line}: SRCSET_WITHOUT_SIZES srcset con descriptor 'w' sin sizes: {src or candidates[0][0]}")
            for cand_url, _ in candidates:
                target = resolve_local(cand_url, path, root)
                if target is not None and not target.exists():
                    errors.append(f"{rel}:{line}: BROKEN_SRCSET_CANDIDATE {cand_url} -> no existe")

    for match in SOURCE_TAG_RE.finditer(html):
        attrs = parse_attrs(match.group(1))
        line = html.count("\n", 0, match.start()) + 1
        srcset = attrs.get("srcset", "")
        if not srcset:
            continue
        candidates = parse_srcset(srcset)
        for cand_url, _ in candidates:
            target = resolve_local(cand_url, path, root)
            if target is not None and not target.exists():
                errors.append(f"{rel}:{line}: BROKEN_SRCSET_CANDIDATE (source) {cand_url} -> no existe")

    return errors


def tracked_html(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "*.html"], cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    paths = []
    for rel in out.split("\0"):
        if not rel:
            continue
        p = root / rel
        if any(part in SKIP_PARTS for part in Path(rel).parts):
            continue
        paths.append(p)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true", help="exit 1 si hay incumplimientos")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    pages = tracked_html(root)
    all_errors: list[str] = []
    for page in pages:
        all_errors.extend(audit_file(page, root))

    by_kind: dict[str, int] = {}
    for e in all_errors:
        kind = e.split(": ", 2)[1].split(" ", 1)[0]
        by_kind[kind] = by_kind.get(kind, 0) + 1

    for e in all_errors:
        print(f"ERROR {e}")

    print(f"\nResponsive images check: {len(pages)} paginas publicas revisadas, {len(all_errors)} incumplimiento(s).")
    for kind, count in sorted(by_kind.items()):
        print(f"  {kind}: {count}")

    if args.check and all_errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
