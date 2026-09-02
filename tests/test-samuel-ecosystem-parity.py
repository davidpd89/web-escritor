#!/usr/bin/env python3
"""Regression contract for the public Samuel entre mundos ecosystem."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "libros/samuel-entre-mundos/index.html"
FRAGMENT = ROOT / "fragmento/index.html"
NOVERIS = ROOT / "universo/noveris/index.html"
CLUB = ROOT / "clubes-de-lectura/samuel-entre-mundos/index.html"
PRINT_GUIDE = ROOT / "clubes-de-lectura/samuel-entre-mundos/guia-imprimible/index.html"
QUIZ_JS = ROOT / "assets/samuel-quiz.js"
FACTS = ROOT / "editorial-facts.json"

for path in (BOOK, FRAGMENT, NOVERIS, CLUB, PRINT_GUIDE, QUIZ_JS, FACTS):
    assert path.exists(), f"missing required Samuel ecosystem file: {path.relative_to(ROOT)}"

book_html = BOOK.read_text(encoding="utf-8")
fragment_html = FRAGMENT.read_text(encoding="utf-8")
noveris_html = NOVERIS.read_text(encoding="utf-8")
club_html = CLUB.read_text(encoding="utf-8")
guide_html = PRINT_GUIDE.read_text(encoding="utf-8")
quiz_js = QUIZ_JS.read_text(encoding="utf-8")
facts = json.loads(FACTS.read_text(encoding="utf-8"))
samuel = facts["books"]["samuelEntreMundos"]


def jsonld_documents(html: str) -> list[dict]:
    docs = []
    for raw in re.findall(r'<script\s+type="application/ld\+json">\s*([\s\S]*?)\s*</script>', html, flags=re.I):
        docs.append(json.loads(raw))
    return docs


def graph_nodes(html: str) -> list[dict]:
    nodes: list[dict] = []
    for doc in jsonld_documents(html):
        graph = doc.get("@graph")
        if isinstance(graph, list):
            nodes.extend(x for x in graph if isinstance(x, dict))
        elif isinstance(doc, dict):
            nodes.append(doc)
    return nodes


def node_with_type(html: str, node_type: str) -> dict:
    for node in graph_nodes(html):
        value = node.get("@type")
        if value == node_type or isinstance(value, list) and node_type in value:
            return node
    raise AssertionError(f"JSON-LD node missing: {node_type}")


book = node_with_type(book_html, "Book")
assert book["isbn"] == samuel["isbn"] == "9791387659776"
assert book["datePublished"] == str(samuel["publicationYear"]) == "2025"
assert book["numberOfPages"] == samuel["numberOfPages"] == 422
assert book["bookFormat"] == "https://schema.org/Paperback"
assert "award" not in book, "Juan Andrés Teno must not be attributed to Samuel without a verified submitted work"
assert "aggregateRating" not in book
assert "review" not in book, "third-party marketplace reviews must remain attributed editorial excerpts, not Book.review structured data"
assert "typicalAgeRange" not in book
assert "suggestedMinAge" not in book
assert "Ninguna ha sido resumida ni editada" not in book_html, "abbreviated review excerpts must not be described as unedited/full reviews"
assert "Extractos abreviados de reseñas publicadas en Amazon España" in book_html, "visible review stream must disclose that marketplace quotes are excerpts"

for html, label in ((book_html, "book"), (club_html, "club"), (guide_html, "print guide")):
    lowered = html.lower()
    assert "typicalagerange" not in lowered, f"{label}: unsupported age-range schema returned"
    assert "aggregaterating" not in lowered, f"{label}: volatile aggregate rating returned"
    assert not re.search(r"\b12\s*(?:a|-|–|—)\s*18\s*años\b", lowered), f"{label}: unsupported 12–18 age claim returned"

assert "la editorial no publica un rango de edad oficial" in club_html.lower()
assert "la editorial no publica un rango de edad oficial" in book_html.lower()

publisher_url = samuel["purchaseUrls"]["publisher"]
amazon_url = samuel["purchaseUrls"]["amazonEs"]
casa_canonical = samuel["purchaseUrls"]["casaDelLibro"]
assert publisher_url in book_html, "official publisher purchase URL missing"
assert amazon_url in book_html, "canonical Amazon purchase URL missing"
assert casa_canonical in book_html, "Casa del Libro ISBN URL missing"
assert re.search(r'href="https://www\.amazon\.es/dp/B0GB6LGQFH\?tag=davidporto-21"[^>]*rel="[^"]*sponsored[^"]*nofollow[^"]*noopener[^"]*noreferrer', book_html), "Amazon link rel contract missing"
assert "Comprar en la editorial" in book_html
# Purchase-channel parity belongs to the visible human UI, not to FAQ/Review
# structured data. Keep this contract valid even when obsolete schema is retired.
for channel in ("Libros Indie", "Amazon España", "Casa del Libro"):
    assert re.search(rf">\s*{re.escape(channel)}\s*<", book_html), f"visible purchase channel missing: {channel}"

assert 'id="samuel-quiz-app"' in book_html and "data-samuel-quiz" in book_html
assert 'id="quiz-noveris-app"' not in book_html, "legacy global quiz hook would double-initialize the local quiz"
assert "quiz-subscribe-form" not in book_html, "quiz must not export result through newsletter subscription"
assert "Tus respuestas y tu resultado no se envían a terceros" in book_html
assert "/assets/samuel-quiz.js?v=1" in book_html
for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "postNewsletter", "_gcEvent"):
    assert forbidden not in quiz_js, f"local quiz contains outbound/analytics primitive: {forbidden}"
assert "https://davidportodiaz.com/libros/samuel-entre-mundos/#quiz-noveris" in quiz_js
assert "https://davidportodiaz.com/universo/noveris/#quiz" not in quiz_js

# Human ecosystem traversal: every major companion has a route back into the book ecosystem.
assert 'href="/fragmento/"' in book_html
assert 'href="/universo/noveris/"' in book_html
assert 'href="/clubes-de-lectura/samuel-entre-mundos/"' in book_html
assert 'href="/libros/samuel-entre-mundos/"' in fragment_html
assert 'href="/libros/samuel-entre-mundos/"' in noveris_html
assert 'href="/libros/samuel-entre-mundos/"' in club_html
assert 'href="/libros/samuel-entre-mundos/"' in guide_html
assert 'href="/clubes-de-lectura/samuel-entre-mundos/"' in guide_html

# Literary text is protected byte-for-byte against the PR base when CI provides it.
base_sha = os.environ.get("PR_BASE_SHA") or os.environ.get("BASE_SHA")
if base_sha:
    before = subprocess.check_output(
        ["git", "show", f"{base_sha}:fragmento/index.html"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    pattern = re.compile(r'<article class="fragment-reading fragment-text" data-nosnippet>([\s\S]*?)</article>')
    before_match = pattern.search(before)
    after_match = pattern.search(fragment_html)
    assert before_match and after_match, "fragment literary article not found"
    assert after_match.group(1) == before_match.group(1), "fragment literary prose changed byte-for-byte"

print("samuel-ecosystem-parity: OK")