#!/usr/bin/env python3
"""Resolve an approved Atlas work to an ACTUAL, published reading catalogue URL.

No matching titles/ISBNS by similarity; only exact reading_book_id references.
No network, no data mutations, no new book pages or affiliate URLs.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def canonical_links(atlas: dict, reading: dict) -> dict[str, str]:
    if atlas.get("schema_version") != 1 or reading.get("schema_version") != 1:
        raise ValueError("Ambos snapshots requieren schema_version=1")
    books = reading.get("libros")
    works = atlas.get("works")
    if not isinstance(books, list) or not isinstance(works, list):
        raise ValueError("Faltan libros[] o works[]")
    published = {}
    for book in books:
        if not isinstance(book, dict):
            raise ValueError("Libro del catálogo inválido")
        book_id = book.get("id")
        if not isinstance(book_id, str):
            raise ValueError("ID de libro inválido")
        if book_id in published:
            raise ValueError("ID duplicado en catálogo: " + book_id)
        published[book_id] = book
    links, used = {}, set()
    for work in works:
        if not isinstance(work, dict):
            raise ValueError("Obra Atlas inválida")
        ref = work.get("reading_book_id")
        if ref is None:
            continue
        if not isinstance(ref, str) or not ref.strip():
            raise ValueError("reading_book_id inválido")
        if ref not in published:
            raise ValueError("reading_book_id no existe en catálogo: " + ref)
        book = published[ref]
        if book.get("estado") not in {"listo", "publicado"}:
            raise ValueError("Obra enlazada a libro sin publicación: " + ref)
        # Listo is editorially prepared but not necessarily in HTML: fail closed.
        if book.get("estado") != "publicado":
            raise ValueError("Libro listo todavía no publicado: " + ref)
        slug = book.get("slug")
        if not isinstance(slug, str) or not SLUG.fullmatch(slug):
            raise ValueError("Slug de libro inválido: " + str(slug))
        if ref in used:
            raise ValueError("Dos obras Atlas comparten reading_book_id: " + ref)
        used.add(ref)
        if work.get("status") == "approved":
            wid = work.get("id")
            if not isinstance(wid, str) or wid in links:
                raise ValueError("ID de obra inválido/duplicado")
            links[wid] = "/recomendaciones/libros/" + slug + "/"
    return links


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("atlas", type=Path)
    parser.add_argument("reading", type=Path)
    parser.add_argument("--out", type=Path, help="JSON con links públicos internos, salida nueva")
    args = parser.parse_args()
    if args.out and args.out.exists():
        parser.error("No sobrescribir salida previa")
    links = canonical_links(json.loads(args.atlas.read_text(encoding="utf-8")),
                            json.loads(args.reading.read_text(encoding="utf-8")))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"schema_version": 1, "work_links": links},
                                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(links)} enlaces Atlas→catálogo verificados por ID; ninguna ficha nueva")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
