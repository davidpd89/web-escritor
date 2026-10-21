#!/usr/bin/env python3
"""Exporta únicamente reseñas MODERADAS para el catálogo estático.

Entrada: CSV PRIVADO exportado de 08_RESEÑAS (no subir a GitHub).
Salida: JSON público de reseñas aprobadas y consentidas, sin notas internas.
No accede a Google Sheets, no recopila formularios ni publica HTML.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT = 2000
MAX_TITLE = 120
MAX_NAME = 80
PUBLIC_FIELDS = ("review_id", "libro_id", "isbn13", "nombre_publico",
                 "puntuacion", "titulo_resena", "texto_resena", "fecha_envio")


def approved_rows(rows, books: list[dict]) -> list[dict]:
    allowed = {b["id"]: b.get("isbn13") for b in books if b.get("estado") == "publicado"}
    seen = set()
    out = []
    for idx, row in enumerate(rows, 2):
        if row.get("estado_moderacion", "").strip().casefold() != "aprobada":
            continue
        if row.get("consentimiento_publicacion", "").strip().casefold() != "si":
            continue
        ident = (row.get("resena_id") or "").strip()
        book_id = (row.get("libro_id") or "").strip()
        isbn = (row.get("isbn13") or "").strip()
        name = (row.get("nombre_publico") or "").strip()
        title = (row.get("titulo_resena") or "").strip()
        body = (row.get("texto_resena") or "").strip()
        timestamp = (row.get("fecha_envio") or "").strip()[:10]
        stars = (row.get("puntuacion_1a5") or "").strip()
        if not ident or ident in seen:
            raise ValueError(f"Fila {idx}: ID de reseña duplicado o vacío")
        if book_id not in allowed or isbn != allowed[book_id]:
            raise ValueError(f"Fila {idx}: libro publicado/ISBN no coincidente")
        if not name or len(name) > MAX_NAME or not title or len(title) > MAX_TITLE:
            raise ValueError(f"Fila {idx}: nombre o título inválido")
        if not body or len(body) > MAX_TEXT:
            raise ValueError(f"Fila {idx}: texto inválido")
        if stars not in {"1", "2", "3", "4", "5"}:
            raise ValueError(f"Fila {idx}: puntuación inválida")
        try:
            date.fromisoformat(timestamp)
        except ValueError as exc:
            raise ValueError(f"Fila {idx}: fecha inválida") from exc
        seen.add(ident)
        out.append({
            "review_id": ident, "libro_id": book_id, "isbn13": isbn,
            "nombre_publico": name, "puntuacion": int(stars),
            "titulo_resena": title, "texto_resena": body, "fecha_envio": timestamp,
        })
    return sorted(out, key=lambda r: (r["libro_id"], r["fecha_envio"], r["review_id"]))


def export(csv_path: Path, catalogue: Path, destination: Path) -> int:
    data = json.loads(catalogue.read_text(encoding="utf-8"))
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        reviews = approved_rows(rows, data["libros"])
    payload = {"schema_version": 1, "reviews": reviews}
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if not destination.is_file() or destination.read_text(encoding="utf-8") != text:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
    return len(reviews)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True, help="CSV privado de 08_RESEÑAS")
    p.add_argument("--catalogue", type=Path, default=ROOT / "data/reading-catalogue.json")
    p.add_argument("--output", type=Path, default=ROOT / "data/reading-reviews-approved.json")
    args = p.parse_args()
    print(f"Exportadas {export(args.input, args.catalogue, args.output)} reseñas aprobadas (sin datos privados).")


if __name__ == "__main__":
    main()
