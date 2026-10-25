#!/usr/bin/env python3
"""Extrae SOLO campos bibliográficos de JSON-LD público de una ficha editorial.

No hace HTTP, no rastrea páginas y no publica. Utilizar exclusivamente después
de verificar el dominio editorial, robots y límites de la fuente.
No copiar las sinopsis comerciales completas.
"""
from __future__ import annotations

import json
from html.parser import HTMLParser
from urllib.parse import urlsplit
from typing import Iterator

from reading_intake_core import clean_title, isbn13, edition_date


class _JSONLDScripts(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.entries: list[str] = []
        self.in_script = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            attrs_map = {k.casefold(): (v or "").casefold() for k, v in attrs}
            self.in_script = attrs_map.get("type", "").split(";")[0].strip() == "application/ld+json"
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.in_script:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            if self.in_script and self.parts:
                self.entries.append("".join(self.parts))
            self.in_script = False
            self.parts = []


def _nodes(data: object) -> Iterator[dict]:
    if isinstance(data, list):
        for item in data:
            yield from _nodes(item)
    elif isinstance(data, dict):
        if "@graph" in data:
            yield from _nodes(data["@graph"])
        yield data


def _text(value: object) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        return _text(value.get("name"))
    return None


def _authors(value: object) -> list[str]:
    return list(dict.fromkeys(filter(None, (_text(v) for v in (
        value if isinstance(value, list) else [value]
    )))))


def _image(value: object) -> str | None:
    if isinstance(value, list):
        return next((url for v in value if (url := _image(v))), None)
    if isinstance(value, dict):
        return _image(value.get("url") or value.get("contentUrl"))
    if isinstance(value, str):
        return value.strip()
    return None


def extract_books(html: str, source_url: str, *, expected_isbn: str | None = None) -> list[dict]:
    """Candidates only; book edition matches ISBN and source hostname.

    A Product listing with Book-like attributes is not enough: require @type Book.
    Preserve original edition information, don't fill a missing date from today.
    """
    source = urlsplit(source_url)
    if source.scheme != "https" or not source.hostname:
        raise ValueError("Ficha editorial debe utilizar URL HTTPS pública")
    expected = isbn13(expected_isbn) if expected_isbn else None
    if expected_isbn and not expected:
        raise ValueError("ISBN esperado inválido")
    parser = _JSONLDScripts()
    parser.feed(html)
    results: list[dict] = []
    observed: set[str] = set()
    for block in parser.entries:
        try:
            parsed = json.loads(block)
        except (ValueError, TypeError):
            continue
        for item in _nodes(parsed):
            types = item.get("@type", [])
            if not isinstance(types, list):
                types = [types]
            if not any(str(t).rsplit("/", 1)[-1].casefold() == "book" for t in types):
                continue
            ident = isbn13(str(item.get("isbn", "")))
            if not ident or (expected and ident != expected) or ident in observed:
                continue
            title, authors = _text(item.get("name")), _authors(item.get("author"))
            if not title or not authors:
                continue
            published, precision = edition_date(str(item.get("datePublished") or ""))
            publisher = _text(item.get("publisher"))
            cover = _image(item.get("image"))
            if cover:
                url = urlsplit(cover)
                if url.scheme != "https" or not url.hostname:
                    cover = None
            results.append({
                "isbn13": ident, "titulo": clean_title(title), "autores": authors,
                "editorial": publisher, "fecha_publicacion": published,
                "precision_fecha": precision,
                "portada_fuente_url": cover,
                "url_ficha_editorial": source_url,
                "fuente": "jsonld_editorial",
                "estado": "candidato"
            })
            observed.add(ident)
    return results
