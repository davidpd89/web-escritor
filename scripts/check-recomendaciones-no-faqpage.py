#!/usr/bin/env python3
"""Gate de regresion (K.2, 2026-08-23): impide reintroducir el nodo
JSON-LD `FAQPage` en la familia `/recomendaciones/` sin una decision
editorial explicita.

La documentacion auditada decidio dejar de mantener ese schema en estas
superficies (no por error de datos, sino por decision de mantenimiento).
El FAQ visible en HTML puede seguir existiendo; lo que no debe reaparecer
es la capa de rich-result FAQPage.

Python standard library only.

Usage:
    python scripts/check-recomendaciones-no-faqpage.py
    python scripts/check-recomendaciones-no-faqpage.py --check
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def tracked_recomendaciones_html(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "recomendaciones/**/*.html", "recomendaciones/*.html"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    return [root / rel for rel in out.split("\0") if rel]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    files = tracked_recomendaciones_html(root)
    errors: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if '"@type":"FAQPage"' in text or '"@type": "FAQPage"' in text:
            rel = path.relative_to(root).as_posix()
            errors.append(f"{rel}: contiene un nodo JSON-LD FAQPage -- decision editorial vigente es no mantener este schema en /recomendaciones/ (ver docs/PENDIENTE-K-GPT-LINEAS-401-600.md K.2).")

    for e in errors:
        print(f"ERROR {e}")

    print(f"\nRecomendaciones FAQPage check: {len(files)} ficheros revisados, {len(errors)} incumplimiento(s).")
    if args.check and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
