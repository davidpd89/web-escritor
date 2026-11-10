#!/usr/bin/env python3
"""Genera data/bot-books.json: el índice compacto del catálogo que usan los bots de comunidad.

Solo lleva lo que necesita el buscador (bots/book-finder.mjs): texto para buscar, categorías,
edad, precios por formato y enlaces. Uso: python scripts/build-bot-index.py
"""
import json
import pathlib
import re
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "reading-catalogue.json"
OUT = ROOT / "data" / "bot-books.json"
WEB = "https://davidportodiaz.com"


def edad_minima(texto):
    m = re.search(r"(\d+)", texto or "")
    return int(m.group(1)) if m else None


def main():
    cat = json.loads(SRC.read_text(encoding="utf-8"))
    nombres = {c["id"]: c["nombre"] for c in cat["categorias"] if c.get("activa", True)}
    por_libro = {}
    for rel in cat["libro_categorias"]:
        if rel["categoria_id"] in nombres:
            por_libro.setdefault(rel["libro_id"], []).append(rel["categoria_id"])
    libros = []
    for b in cat["libros"]:
        if b.get("estado") != "publicado":
            continue
        formatos = {}
        for f in b.get("formatos_compra") or []:
            if f.get("url") and f.get("precio_centimos"):
                formatos[f["formato"]] = {"precio": f["precio_centimos"], "url": f["url"]}
        libros.append({
            "id": b["id"],
            "titulo": b["titulo"],
            "autores": b.get("autores") or [],
            "editorial": b.get("editorial"),
            "anio": b.get("anio_publicacion"),
            "sinopsis": b.get("sinopsis_breve") or b.get("descripcion_breve") or "",
            "categorias": sorted(por_libro.get(b["id"], [])),
            "edad_min": edad_minima(b.get("edad_recomendada")),
            "edad": b.get("edad_recomendada"),
            "paginas": b.get("numero_paginas"),
            "formatos": formatos,
            "amazon": b.get("url_amazon_afiliada") or b.get("amazon_busqueda_isbn"),
            "web": f"{WEB}/lecturas/#q={quote(b['titulo'])}",
            "portada": f"{WEB}/{b['portada_local'].lstrip('/')}" if b.get("portada_local") else None,
            "fecha": b.get("fecha_publicacion"),
        })
    out = {"schema_version": 1, "categorias": nombres, "libros": libros}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print(f"{OUT.relative_to(ROOT)}: {len(libros)} libros, {OUT.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
