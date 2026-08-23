#!/usr/bin/env python3
"""Gate de cuarentena editorial (K.4, 2026-08-23):
/cuaderno/sistema-de-magia-noveris/ quedo noindex porque afirmaba como
hecho una mecanica del sistema de magia de Noveris que contradice otras
versiones de trabajo (coste = perdida de memoria del objeto segun su FAQ,
"coste fisico" segun su propio deck/nota -- una contradiccion interna
real, no solo una discrepancia entre articulos).

Este checker falla si, mientras la pagina siga en cuarentena:

  - deja de ser `noindex`;
  - reaparece cualquiera de las frases factuales conflictivas conocidas
    (verbatim, del contenido original antes de neutralizarlo);
  - reaparece un nodo JSON-LD `FAQPage` en esa URL;
  - la pagina vuelve a aparecer en el sitemap generado.

No impide restaurar el articulo: solo exige que, si se hace, sea una
decision editorial explicita (que retire este mismo checker o lo
actualice), no un cambio accidental. Ver docs/PENDIENTE-K-GPT-LINEAS-401-600.md.

Python standard library only.

Usage:
    python scripts/check-noveris-magic-quarantine.py
    python scripts/check-noveris-magic-quarantine.py --check
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUARANTINED_PATH = "cuaderno/sistema-de-magia-noveris/index.html"

# Frases textuales de las mecanicas en disputa (verbatim del contenido
# original). No se buscan por keyword sueltas (ej. "coste") porque
# generarian falsos positivos con el resto del sitio: se buscan las
# formulaciones factuales concretas que estaban en el articulo cuando se
# puso en cuarentena.
CONFLICTING_CLAIMS = [
    "cada canalización consume esa historia residual de forma irreversible",
    "pérdida de capas de memoria del objeto",
    "borra parte de la historia acumulada de ese objeto",
    "no la energía física del canalizado",
    "coste físico proporcional",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    path = root / QUARANTINED_PATH

    errors: list[str] = []
    if not path.exists():
        print(f"AVISO: {QUARANTINED_PATH} no existe; nada que verificar.")
        return 0

    html = path.read_text(encoding="utf-8", errors="replace")

    if not re.search(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', html, re.I):
        errors.append(f"{QUARANTINED_PATH}: ya no es noindex -- si el canon se resolvio, esta cuarentena debe cerrarse explicitamente en una PR propia, no dejarse en un estado intermedio.")

    for claim in CONFLICTING_CLAIMS:
        if claim.lower() in html.lower():
            errors.append(f"{QUARANTINED_PATH}: reaparece una afirmacion factual conflictiva conocida: '{claim}'")

    if '"@type": "FAQPage"' in html or "'@type': 'FAQPage'" in html:
        errors.append(f"{QUARANTINED_PATH}: reaparece un nodo JSON-LD FAQPage mientras la pagina sigue en cuarentena.")

    sitemap_path = root / "sitemap.xml"
    if sitemap_path.exists():
        sitemap = sitemap_path.read_text(encoding="utf-8", errors="replace")
        if "sistema-de-magia-noveris" in sitemap:
            errors.append("sitemap.xml: la URL en cuarentena aparece en el sitemap generado.")

    for e in errors:
        print(f"ERROR {e}")

    print(f"\nNoveris magic quarantine check: {len(errors)} incumplimiento(s).")
    if args.check and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
