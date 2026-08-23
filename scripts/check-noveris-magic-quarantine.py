#!/usr/bin/env python3
"""Gate de cuarentena editorial para /cuaderno/sistema-de-magia-noveris/.

La URL puede conservarse para no romper enlaces, pero mientras no exista una
version editorial confirmada debe ser una cuarentena real: noindex, sin
FAQPage, fuera del sitemap y sin publicar como hechos mecanicas discutidas ni
texto interno de trabajo. La pagina debe ofrecer una explicacion neutra para
un lector y remitir a materiales publicados.

Python standard library only.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUARANTINED_PATH = "cuaderno/sistema-de-magia-noveris/index.html"

CONFLICTING_CLAIMS = [
    "cada canalización consume esa historia residual de forma irreversible",
    "pérdida de capas de memoria del objeto",
    "borra parte de la historia acumulada de ese objeto",
    "no la energía física del canalizado",
    "coste físico proporcional",
]

# Frases que son adecuadas para una nota de trabajo interna, pero no para una
# URL publica a la que puede llegar un lector. No determinan que canon es
# correcto: solo impiden exponer el proceso editorial como si fuera contenido.
INTERNAL_EDITORIAL_COPY = [
    "versiones de trabajo incompatibles",
    "única versión autorizada",
    "resolver el canon",
    "canon pendiente",
    "todo:",
    "pendiente de decidir",
    "instrucción editorial",
]

REQUIRED_READER_COPY = [
    "Contenido temporalmente retirado",
    "La URL se conserva para no romper enlaces",
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
        errors.append(f"{QUARANTINED_PATH}: falta la URL de cuarentena")
        html = ""
    else:
        html = path.read_text(encoding="utf-8", errors="replace")

    if html and not re.search(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', html, re.I):
        errors.append(f"{QUARANTINED_PATH}: la pagina en cuarentena debe seguir siendo noindex")

    lower = html.lower()
    for claim in CONFLICTING_CLAIMS:
        if claim.lower() in lower:
            errors.append(f"{QUARANTINED_PATH}: reaparece afirmacion factual conflictiva: {claim!r}")
    for phrase in INTERNAL_EDITORIAL_COPY:
        if phrase.lower() in lower:
            errors.append(f"{QUARANTINED_PATH}: expone copy editorial interno al lector: {phrase!r}")

    if re.search(r'["\']@type["\']\s*:\s*["\']FAQPage["\']', html, re.I):
        errors.append(f"{QUARANTINED_PATH}: FAQPage no puede reaparecer durante la cuarentena")

    for phrase in REQUIRED_READER_COPY:
        if phrase.lower() not in lower:
            errors.append(f"{QUARANTINED_PATH}: falta copy publico de cuarentena: {phrase!r}")

    for href in ("/libros/samuel-entre-mundos/", "/fragmento/"):
        if f'href="{href}"' not in html:
            errors.append(f"{QUARANTINED_PATH}: falta salida segura hacia {href}")

    sitemap_path = root / "sitemap.xml"
    if sitemap_path.exists() and "sistema-de-magia-noveris" in sitemap_path.read_text(encoding="utf-8", errors="replace"):
        errors.append("sitemap.xml: la URL de Noveris en cuarentena aparece en el sitemap")

    for err in errors:
        print(f"ERROR {err}")
    print(f"\nNoveris magic quarantine check: {len(errors)} incumplimiento(s).")
    if args.check and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())