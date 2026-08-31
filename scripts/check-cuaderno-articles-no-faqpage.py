#!/usr/bin/env python3
"""Gate de regresion (2026-08-31): impide reintroducir el nodo JSON-LD
`FAQPage` en los 3 articulos de /cuaderno/ donde se retiro por duplicar,
sin beneficio de rich-result vigente, el FAQ visible en <details>/<summary>
(mismo criterio ya aplicado en /recomendaciones/, ver K.2 en
docs/PENDIENTE-K-GPT-LINEAS-401-600.md).

El FAQ visible en HTML no se toca: lo que no debe reaparecer es la capa de
schema FAQPage en el JSON-LD.

Python standard library only.

Usage:
    python scripts/check-cuaderno-articles-no-faqpage.py
    python scripts/check-cuaderno-articles-no-faqpage.py --check
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FILES = [
    "cuaderno/que-es-el-portal-fantasy/index.html",
    "cuaderno/portal-fantasy-vs-fantasia-epica/index.html",
    "cuaderno/fantasia-juvenil-espanola-portales-magia-coste/index.html",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    errors: list[str] = []
    for rel in FILES:
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: fichero ausente")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if '"@type":"FAQPage"' in text or '"@type": "FAQPage"' in text:
            errors.append(f"{rel}: contiene un nodo JSON-LD FAQPage -- ya se retiro por duplicar el FAQ visible en <details>/<summary> (2026-08-31).")

    for e in errors:
        print(f"ERROR {e}")

    print(f"\nCuaderno articulos FAQPage check: {len(FILES)} ficheros revisados, {len(errors)} incumplimiento(s).")
    if args.check and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
