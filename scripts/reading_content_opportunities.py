#!/usr/bin/env python3
"""Auditoría offline de calidad y cobertura de libros, autores y editoriales.

No llama a la red, no altera catálogos ni estados ni publica páginas. Su salida
es un informe de oportunidades priorizables, no decisiones de publicación.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_day(raw):
    if not isinstance(raw, str):
        return None
    try:
        if len(raw) != 10 or raw[4] != "-" or raw[7] != "-":
            return None
        return date.fromisoformat(raw)
    except ValueError:
        return None


def parse_instant(raw):
    if not isinstance(raw, str):
        return None
    try:
        result = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except ValueError:
        return None


def audit(catalogue, authors, editoriales, market, today):
    """Use the site's canonical IDs; never join a person by approximate name."""
    books = [b for b in catalogue.get("libros", []) if b.get("estado") == "publicado"]
    authors_by_name = {a["nombre"]: a for a in authors.get("autores", [])}
    publishers_by_slug = {p["slug"]: p for p in editoriales.get("publishers", [])}
    books_by_author = defaultdict(list)
    books_by_publisher = defaultdict(list)
    without_publisher, without_author = [], []
    precise_future, imprecise_date = [], []
    for b in books:
        identifier = b["id"]
        for name in b.get("autores", []):
            books_by_author[name].append(identifier)
            if name not in authors_by_name:
                without_author.append({"libro_id": identifier, "autor": name})
        slug = b.get("editorial_slug")
        if slug in publishers_by_slug and publishers_by_slug[slug].get("publish"):
            books_by_publisher[slug].append(identifier)
        else:
            without_publisher.append({"libro_id": identifier, "sello": b.get("editorial"), "slug": slug})
        release = parse_day(b.get("fecha_publicacion"))
        if release and today < release <= today + timedelta(days=30):
            precise_future.append({"libro_id": identifier, "fecha": release.isoformat()})
        if b.get("fecha_publicacion_parcial") and not release:
            imprecise_date.append(identifier)
    future_by_id = sorted(precise_future, key=lambda entry: (entry["fecha"], entry["libro_id"]))
    missing_bio, weak_author = [], []
    for name, ids in sorted(books_by_author.items()):
        record = authors_by_name.get(name)
        if record is None:
            continue
        if not record.get("biografia_breve") and record.get("tipo") == "bibliografico":
            missing_bio.append({"autor": name, "slug": record["slug"], "libros_en_web": len(ids),
                                "accion": "Buscar fuente primaria; identidad antes de ampliar biografia"})
        if len(ids) == 1 and not record.get("biografia_breve") and record.get("tipo") == "bibliografico":
            weak_author.append(record["slug"])
    stale_publishers, publisher_books = [], []
    for p in editoriales.get("publishers", []):
        if not p.get("publish"):
            continue
        slug = p["slug"]
        publisher_books.append({"slug": slug, "nombre": p["name"],
                                "estado_originales": p.get("status", "unknown"),
                                "libros_en_web": len(books_by_publisher.get(slug, []))})
        verified = parse_day(p.get("verified_at"))
        if not verified or verified > today or (today - verified).days > 90:
            stale_publishers.append({"slug": slug, "nombre": p["name"],
                                     "estado_publicado": p.get("status", "unknown"),
                                     "verificado": p.get("verified_at"),
                                     "accion": "Contrastar fuente primaria; no renovar fecha sin comprobacion"})
    no_offers, expired_offers, live_offers = 0, 0, 0
    by_book = Counter(o.get("libro_id") for o in market.get("offers", []))
    # Cotejo offline deliberadamente conservador: solo existen precios si la
    # respuesta oficial tiene un caduca_en válido posterior a now UTC.
    now = datetime.combine(today, datetime.min.time(), timezone.utc)
    for b in books:
        if not by_book[b["id"]]:
            no_offers += 1
    for offer in market.get("offers", []):
        expiry = parse_instant(offer.get("caduca_en"))
        if expiry and expiry > now:
            live_offers += 1
        else:
            expired_offers += 1
    ratings = Counter(r.get("fuente", "goodreads") for r in market.get("ratings", []))
    return {
        "fecha_de_corte": today.isoformat(),
        "resumen": {
            "libros_publicados": len(books), "autores_con_libros": len(books_by_author),
            "editoriales_publicadas": len(publisher_books), "libros_sin_editorial_enlazable": len(without_publisher),
            "referencias_a_autores_sin_ficha": len(without_author),
            "autores_bibliograficos_sin_bio_verificada": len(missing_bio),
            "autores_de_una_sola_ficha_sin_bio": len(weak_author),
            "editoriales_con_verificacion_caducada": len(stale_publishers),
            "lanzamientos_con_fecha_exacta_30_dias": len(future_by_id),
            "fechas_de_publicacion_parciales": len(imprecise_date),
            "libros_sin_ofertas": no_offers, "ofertas_vigentes_al_inicio_del_dia_utc": live_offers,
            "ofertas_caducadas_o_invalidas": expired_offers,
            "valoraciones_por_proveedor": dict(sorted(ratings.items())),
        },
        "prioridades": {
            "desvinculados_editoriales": sorted(without_publisher, key=lambda r: r["libro_id"]),
            "autores_sin_ficha": sorted(without_author, key=lambda r: (r["autor"], r["libro_id"])),
            "autores_sin_bio": sorted(missing_bio, key=lambda r: (-r["libros_en_web"], r["autor"])),
            "editoriales_con_revision_pendiente": sorted(stale_publishers, key=lambda r: r["slug"]),
            "editoriales_y_libros": sorted(publisher_books, key=lambda r: (-r["libros_en_web"], r["slug"])),
            "proximos_lanzamientos": future_by_id, "fechas_imprecisas": sorted(imprecise_date),
        },
        "advertencias": [
            "Es un informe estatico; no verifica webs ni crea fichas y no acredita ningun estado nuevo.",
            "La fecha de corte no contiene hora: las ofertas se agrupan como referencia, nunca se publica su precio.",
            "Las puntuaciones por proveedor no equivalen a resenas propias ni pueden agregarse como estrellas de la web.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--today", help="YYYY-MM-DD; por defecto, dia de calendario de Madrid")
    args = parser.parse_args()
    if args.today:
        today = parse_day(args.today)
        if today is None:
            parser.error("--today invalido")
    else:
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Europe/Madrid")).date()
    root = args.root
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    result = audit(read("data/reading-catalogue.json"),
                   read("data/reading-authors.json"),
                   read("data/editoriales.json"),
                   read("assets/reading-market.json"), today)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
