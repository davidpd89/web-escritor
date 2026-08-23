#!/usr/bin/env python3
"""Gate de evidencia para /recomendaciones/ (K.1, 2026-08-23).

`data/recommendations-evidence.json` separa dos planos distintos:

- evidencia bibliografica de una edicion/ficha;
- lectura personal del autor de la web.

La autoria, aparecer en una lista o disponer de una ficha propia NO prueban
lectura personal. Este checker falla si una guia publica afirma mas de lo
que respalda el registro o si una fuente marcada como verificada no es
reproducible.

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
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
VALID_STATUSES = {"leido", "consultado", "verificado", "pendiente"}
VALID_READING = {"leido", "pendiente"}
REC_ITEM_RE = re.compile(r'<li class="rec-item([^"]*)"[^>]*data-isbn="(\d+)"[^>]*>(.*?)</li>', re.S)
ISBN_TEXT_RE = re.compile(r'ISBN\s+(\d{10,13})')
PLACEHOLDER_RE = re.compile(r'\b(todo|tbd|pendiente de fuente|example\.com|ejemplo\.com)\b', re.I)


def tracked_recommendation_guides(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "-z", "recomendaciones/**/index.html"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    paths = [root / rel for rel in out.split("\0") if rel]
    return [p for p in paths if "rec-item" in p.read_text(encoding="utf-8", errors="replace")]


def valid_https_url(raw: object) -> bool:
    if not isinstance(raw, str) or not raw or PLACEHOLDER_RE.search(raw):
        return False
    parsed = urlparse(raw)
    return parsed.scheme == "https" and bool(parsed.hostname) and " " not in raw


def load_document(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_authority(data: dict, root: Path) -> tuple[dict[str, dict], list[str]]:
    errors: list[str] = []
    works = data.get("works")
    if not isinstance(works, list):
        return {}, ["data/recommendations-evidence.json: works debe ser una lista"]

    evidence: dict[str, dict] = {}
    for record in works:
        isbn = str(record.get("isbn", ""))
        if not isbn:
            errors.append("data/recommendations-evidence.json: obra sin ISBN identificador")
            continue
        if isbn in evidence:
            errors.append(f"data/recommendations-evidence.json: ISBN duplicado {isbn}")
            continue
        evidence[isbn] = record

        status = record.get("evidenceStatus")
        if status not in VALID_STATUSES:
            errors.append(f"data/recommendations-evidence.json: ISBN {isbn} tiene evidenceStatus invalido: {status!r}")

        reading = record.get("personalReadingStatus")
        if reading not in VALID_READING:
            errors.append(f"data/recommendations-evidence.json: ISBN {isbn} tiene personalReadingStatus invalido/ausente: {reading!r}")

        # Una lectura personal solo puede publicarse si existe evidencia
        # humana explicita. La autoria o relationship=obra-propia no sirven.
        if reading == "leido":
            proof = record.get("personalReadingEvidence")
            if not isinstance(proof, dict) or not proof.get("reference"):
                errors.append(f"data/recommendations-evidence.json: ISBN {isbn} marcado como leido sin personalReadingEvidence.reference")
            elif PLACEHOLDER_RE.search(str(proof.get("reference"))):
                errors.append(f"data/recommendations-evidence.json: ISBN {isbn} tiene referencia de lectura placeholder")

        if status == "leido" and reading != "leido":
            errors.append(f"data/recommendations-evidence.json: ISBN {isbn} usa evidenceStatus='leido' sin lectura personal acreditada")

        # Verificado se limita a hechos bibliograficos y exige fuente web
        # concreta, fecha y alcance explicito.
        if status == "verificado":
            if not record.get("verifiedDate"):
                errors.append(f"data/recommendations-evidence.json: ISBN {isbn} verificado sin verifiedDate")
            else:
                try:
                    date.fromisoformat(str(record["verifiedDate"]))
                except ValueError:
                    errors.append(f"data/recommendations-evidence.json: ISBN {isbn} verifiedDate no ISO")
            scope = record.get("verificationScope")
            if not isinstance(scope, list) or not scope or "isbn" not in scope:
                errors.append(f"data/recommendations-evidence.json: ISBN {isbn} verificado sin verificationScope bibliografico suficiente")
            source = record.get("editionSource")
            if not isinstance(source, dict) or not source.get("type") or not valid_https_url(source.get("url")):
                errors.append(f"data/recommendations-evidence.json: ISBN {isbn} verificado sin editionSource reproducible https")

    corrections = data.get("corrections", [])
    if not isinstance(corrections, list):
        errors.append("data/recommendations-evidence.json: corrections debe ser una lista")
        corrections = []
    seen_corrections: set[str] = set()
    policy_html = root / "recomendaciones" / "politica-de-recomendaciones" / "index.html"
    policy_text = policy_html.read_text(encoding="utf-8", errors="replace") if policy_html.exists() else ""
    for correction in corrections:
        cid = str(correction.get("correction_id", ""))
        required = ["correction_id", "status", "page_url", "corrected_at", "significant_update", "public_note", "source", "summary"]
        for field in required:
            if field not in correction or correction[field] in (None, ""):
                errors.append(f"data/recommendations-evidence.json: correccion {cid or '<sin id>'} sin {field}")
        if cid in seen_corrections:
            errors.append(f"data/recommendations-evidence.json: correction_id duplicado {cid}")
        seen_corrections.add(cid)
        if correction.get("status") not in {"applied", "pending"}:
            errors.append(f"data/recommendations-evidence.json: correccion {cid} status invalido")
        if not valid_https_url(correction.get("page_url")):
            errors.append(f"data/recommendations-evidence.json: correccion {cid} page_url invalida")
        try:
            date.fromisoformat(str(correction.get("corrected_at", "")))
        except ValueError:
            errors.append(f"data/recommendations-evidence.json: correccion {cid} corrected_at no ISO")
        if PLACEHOLDER_RE.search(str(correction.get("source", ""))) or PLACEHOLDER_RE.search(str(correction.get("summary", ""))):
            errors.append(f"data/recommendations-evidence.json: correccion {cid} contiene placeholder")
        if correction.get("status") == "applied" and correction.get("public_note") is True:
            if f'data-correction-id="{cid}"' not in policy_text:
                errors.append(f"recomendaciones/politica-de-recomendaciones/index.html: falta nota publica de la correccion {cid}")
            if correction.get("significant_update") is True:
                corrected = str(correction.get("corrected_at"))
                if corrected not in policy_text or '"dateModified"' not in policy_text:
                    errors.append(f"recomendaciones/politica-de-recomendaciones/index.html: correccion significativa {cid} no reconcilia fecha visible/dateModified")

    return evidence, errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    try:
        data = load_document(root / "data" / "recommendations-evidence.json")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR data/recommendations-evidence.json: {exc}")
        return 1 if args.check else 0

    evidence, errors = validate_authority(data, root)
    guides = tracked_recommendation_guides(root)

    for path in guides:
        rel = path.relative_to(root).as_posix()
        html = path.read_text(encoding="utf-8", errors="replace")

        for m in REC_ITEM_RE.finditer(html):
            item_classes, isbn, body = m.group(1), m.group(2), m.group(3)
            record = evidence.get(isbn)
            if record is None:
                errors.append(f"{rel}: ISBN {isbn} listado pero sin entrada en data/recommendations-evidence.json")
                continue

            visible_isbn = ISBN_TEXT_RE.search(body)
            if visible_isbn and visible_isbn.group(1) != isbn:
                errors.append(f"{rel}: ISBN visible {visible_isbn.group(1)!r} no coincide con data-isbn={isbn!r}")

            claims_verified = "verificad" in body.lower()
            if claims_verified and record.get("evidenceStatus") != "verificado":
                errors.append(f"{rel}: ISBN {isbn} afirma edicion verificada pero la autoridad dice {record.get('evidenceStatus')!r}")

            claims_read = bool(re.search(r'\b(le[ií]do|lectura personal confirmada)\b', re.sub(r'<[^>]+>', ' ', body), re.I))
            if claims_read and record.get("personalReadingStatus") != "leido":
                errors.append(f"{rel}: ISBN {isbn} afirma lectura personal sin evidencia humana acreditada")

            if "rec-item--self" in item_classes and record.get("relationship") != "obra-propia":
                errors.append(f"{rel}: ISBN {isbn} marcado rec-item--self sin relationship='obra-propia' en la autoridad")

        if 'rel="nofollow sponsored' in html and "affiliate-disclosure" not in html:
            errors.append(f"{rel}: usa enlaces patrocinados pero no declara affiliate-disclosure")

    for err in errors:
        print(f"ERROR {err}")
    print(f"\nRecommendations evidence check: {len(guides)} guia(s) revisada(s), {len(errors)} incumplimiento(s).")
    if args.check and errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())