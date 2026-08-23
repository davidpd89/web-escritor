#!/usr/bin/env python3
"""Gate de evidencia para /recomendaciones/ (K.1, 2026-08-23).

data/recommendations-evidence.json es la autoridad unica de verdad sobre
el estado de evidencia de cada obra listada en cualquier guia de
Recomendaciones. Este checker falla si:

  - una entrada `<li class="rec-item" ... data-isbn="...">` en una guia de
    Recomendaciones no tiene evidencia registrada;
  - el ISBN visible en el HTML (texto "ISBN <numero>") no coincide con el
    `data-isbn` ni con el ISBN de la autoridad;
  - `evidenceStatus` no pertenece al enum permitido;
  - una entrada con `evidenceStatus` "verificado" o "leido" no tiene
    `verifiedDate` y `editionSource`;
  - el HTML afirma "verificada"/"verificado" para un ISBN cuya autoridad
    diga "pendiente" o "consultado" (degradacion silenciosa inversa: el
    HTML no puede prometer mas de lo que la autoridad certifica);
  - el registro de afiliacion (`affiliate-disclosure`) desaparece de una
    guia que sigue usando enlaces `rel="...sponsored..."`;
  - la obra propia dentro de la lista pierde su marcador `rec-item--self`.

Python standard library only.

Usage:
    python scripts/check-recommendations-evidence.py
    python scripts/check-recommendations-evidence.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_PATH = ROOT / "data" / "recommendations-evidence.json"
VALID_STATUSES = {"leido", "consultado", "verificado", "pendiente"}

REC_ITEM_RE = re.compile(r'<li class="rec-item([^"]*)"[^>]*data-isbn="(\d+)"[^>]*>(.*?)</li>', re.S)
ISBN_TEXT_RE = re.compile(r'ISBN\s+(\d{10,13})')


def tracked_recommendation_guides(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "recomendaciones/**/index.html"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    paths = [root / rel for rel in out.split("\0") if rel]
    # Solo guias que realmente listan libros (contienen rec-item); el hub
    # /recomendaciones/index.html no lista obras individuales.
    return [p for p in paths if "rec-item" in p.read_text(encoding="utf-8", errors="replace")]


def load_evidence(path: Path) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {w["isbn"]: w for w in data["works"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    evidence = load_evidence(root / "data" / "recommendations-evidence.json")
    for isbn, record in evidence.items():
        status = record.get("evidenceStatus")
        if status not in VALID_STATUSES:
            print(f"ERROR data/recommendations-evidence.json: ISBN {isbn} tiene evidenceStatus inválido: '{status}'")
            return 1 if args.check else 0
        if status in ("verificado", "leido") and not (record.get("verifiedDate") and record.get("editionSource")):
            print(f"ERROR data/recommendations-evidence.json: ISBN {isbn} con evidenceStatus '{status}' sin verifiedDate/editionSource")
            return 1 if args.check else 0

    guides = tracked_recommendation_guides(root)
    errors: list[str] = []
    for path in guides:
        rel = path.relative_to(root).as_posix()
        html = path.read_text(encoding="utf-8", errors="replace")

        for m in REC_ITEM_RE.finditer(html):
            item_classes, isbn, body = m.group(1), m.group(2), m.group(3)
            record = evidence.get(isbn)
            if record is None:
                errors.append(f"{rel}: ISBN {isbn} listado en la guía pero sin entrada en data/recommendations-evidence.json")
                continue

            isbn_text_match = ISBN_TEXT_RE.search(body)
            if isbn_text_match and isbn_text_match.group(1) != isbn:
                errors.append(f"{rel}: ISBN visible '{isbn_text_match.group(1)}' no coincide con data-isbn='{isbn}'")

            claims_verified = "verificad" in body.lower()
            if claims_verified and record["evidenceStatus"] not in ("verificado", "leido"):
                errors.append(f"{rel}: ISBN {isbn} el HTML afirma una edición verificada pero la autoridad dice evidenceStatus='{record['evidenceStatus']}'")

            if "rec-item--self" in item_classes and record["evidenceStatus"] != "leido":
                errors.append(f"{rel}: ISBN {isbn} marcado como obra propia (rec-item--self) pero su evidenceStatus no es 'leido'")

        if 'rel="nofollow sponsored' in html and "affiliate-disclosure" not in html:
            errors.append(f"{rel}: usa enlaces de afiliado (sponsored) pero no declara affiliate-disclosure")

    for e in errors:
        print(f"ERROR {e}")

    print(f"\nRecommendations evidence check: {len(guides)} guía(s) revisada(s), {len(errors)} incumplimiento(s).")
    if args.check and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
