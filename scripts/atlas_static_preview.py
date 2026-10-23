#!/usr/bin/env python3
"""UNPUBLISHED prototype: static atlas HTML from APPROVED internal snapshot.

No third-party requests, maps, browser framework, search APIs or LLM at runtime.
Does not register URLs in the real site, Pagefind, sitemap or content registry.
Production integration must adapt output to the site's shared shell/builders.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit

SITE = "https://davidportodiaz.com"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MIN_TEXT_LENGTH = 140
RELATION_SUBJECTS = {
    "narrative_explicit": "work",
    "inspiration_documented": "work",
    "filming_location": "adaptation",
    "author_public_history": "author",
    "literary_homage": "work",
    # popular_claim_unverified is deliberately never publicly displayed.
}


def e(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def valid_https_url(value: object) -> bool:
    if not isinstance(value, str) or re.search(r"[\s<>\x00-\x1f]", value):
        return False
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and not parsed.username and not parsed.password
                and parsed.port in (None, 443))
    except ValueError:
        return False


def safe_slug(value: object) -> str:
    if not isinstance(value, str) or not SLUG.fullmatch(value):
        raise ValueError(f"Slug no válido: {value!r}")
    return value


def approved(row: dict) -> bool:
    return row.get("status") == "approved" and bool(row.get("verified_at"))


def text_ready(row: dict) -> bool:
    value = row.get("summary_original")
    return isinstance(value, str) and len(value.strip()) >= MIN_TEXT_LENGTH


def jsonld(value: object) -> str:
    """Escaping '<' prevents authored titles closing a script tag."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def page(title: str, description: str, path: str, content: str, structured: list[dict]) -> str:
    canonical = SITE + path
    desc = description.strip()[:155]
    graph = {"@context": "https://schema.org", "@graph": structured}
    return (
        "<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{e(title)}</title><meta name=\"description\" content=\"{e(desc)}\">"
        f"<link rel=\"canonical\" href=\"{e(canonical)}\">"
        f"<meta property=\"og:url\" content=\"{e(canonical)}\">"
        f"<script type=\"application/ld+json\">{jsonld(graph)}</script></head><body>"
        f"<main id=\"main\">{content}</main></body></html>"
    )


def breadcrumbs(trail: list[tuple[str, str]]) -> tuple[str, dict]:
    text = " / ".join(
        f'<a href="{e(path)}">{e(label)}</a>' if index < len(trail) - 1 else e(label)
        for index, (label, path) in enumerate(trail)
    )
    nav = f'<nav aria-label="Ruta de exploración">{text}</nav>'
    ld = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": index + 1, "name": label, "item": SITE + path}
        for index, (label, path) in enumerate(trail)
    ]}
    return nav, ld


def destination_url(row: dict) -> str:
    return "/atlas-literario/destinos/" + safe_slug(row["slug"]) + "/"


def place_url(row: dict) -> str:
    return "/atlas-literario/lugares/" + safe_slug(row["slug"]) + "/"


def eligible(data: dict) -> tuple[list[dict], list[dict]]:
    """Only editorially approved entities with real text and sources."""
    destinations = [d for d in data.get("destinations", []) if approved(d) and text_ready(d)]
    dest_ids = {d["id"] for d in destinations}
    sources = {s["id"] for s in data.get("sources", [])
               if valid_https_url(s.get("url"))
               and s.get("title") and s.get("retrieved_at") and s.get("evidence_summary")}
    places = [
        p for p in data.get("places", [])
        if approved(p) and text_ready(p) and p.get("destination_id") in dest_ids
        and p.get("source_ids") and all(s in sources for s in p["source_ids"])
    ]
    live_dest_ids = {p["destination_id"] for p in places}
    destinations = [d for d in destinations if d["id"] in live_dest_ids]
    return destinations, places


def place_card(p: dict) -> str:
    return (
        '<article class="atlas-card"><h3><a href="' + e(place_url(p)) + '">'
        + e(p["name"]) + "</a></h3><p>" + e(p["summary_original"][:180]) + "</p></article>"
    )


def destination_page(d: dict, places: list[dict]) -> str:
    url = destination_url(d)
    nav, crumbs = breadcrumbs([("Atlas literario", "/atlas-literario/"),
                              (d["name"], url)])
    cards = "".join(place_card(p) for p in places)
    body = (
        nav + '<span data-pagefind-filter="atlas_entity:destination"></span>'
        + '<span data-pagefind-filter="atlas_country:' + e(d["country_iso2"]) + '"></span>'
        + '<span data-pagefind-filter="atlas_city:' + e(d["id"]) + '"></span>'
        + '<header><h1>' + e(d["name"]) + '</h1><p>' +
        e(d["summary_original"]) + '</p></header><section aria-label="Lugares literarios">'
        + cards + '</section>'
    )
    schema = {"@type": "CollectionPage", "@id": SITE + url,
              "name": "Lugares literarios en " + d["name"],
              "url": SITE + url,
              "hasPart": [{"@type": "Place", "name": p["name"], "url": SITE + place_url(p)}
                          for p in places]}
    return page("Viajes literarios en " + d["name"], d["summary_original"],
                url, body, [crumbs, schema])


def place_page(p: dict, d: dict, sources: dict, relations: list[dict]) -> str:
    url = place_url(p)
    nav, crumbs = breadcrumbs([
        ("Atlas literario", "/atlas-literario/"), (d["name"], destination_url(d)),
        (p["name"], url),
    ])
    evidence = "".join(
        f'<li><a href="{e(sources[s]["url"])}" rel="noopener noreferrer">'
        + e(sources[s]["title"]) + '</a></li>'
        for s in p.get("source_ids", [])
        if s in sources and valid_https_url(sources[s].get("url"))
    )
    def relation_html(r: dict) -> str:
        title = e(r["subject_name"])
        url = r.get("catalogue_url")
        if isinstance(url, str) and re.fullmatch(
            r"/recomendaciones/libros/[a-z0-9]+(?:-[a-z0-9]+)*/", url
        ):
            return "<li><a href=\"" + e(url) + "\">" + title + "</a></li>"
        return "<li>" + title + "</li>"

    relation_text = (('<section><h2>Obras y autores relacionados</h2><ul>' +
                     "".join(relation_html(r) for r in relations) +
                     "</ul></section>") if relations else "")
    facet_pairs = [("atlas_entity", "place"), ("atlas_country", d["country_iso2"]),
                   ("atlas_city", d["id"])]
    for r in relations:
        facet_pairs.append(({"work": "atlas_work", "author": "atlas_author",
                            "adaptation": "atlas_adaptation"}[r["subject_type"]], r["subject_id"]))
        facet_pairs.append(("atlas_relation", r["relation"]))
    facet_markup = "".join('<span data-pagefind-filter="' + e(k + ":" + v) + '"></span>'
                           for k, v in dict.fromkeys(facet_pairs))
    map_link = ""
    lat, lon = p.get("latitude"), p.get("longitude")
    geo: dict = {}
    if (p.get("geo_precision") in {"point", "building"}
            and isinstance(lat, (int, float)) and not isinstance(lat, bool)
            and isinstance(lon, (int, float)) and not isinstance(lon, bool)
            and -90 <= lat <= 90 and -180 <= lon <= 180):
        geo = {"geo": {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon}}
        target = "https://www.openstreetmap.org/?" + urlencode(
            {"mlat": lat, "mlon": lon, "zoom": 16}
        )
        map_link = '<p><a href="' + e(target) + '" rel="noopener noreferrer">Ver en el mapa</a></p>'
    body = (nav + facet_markup + '<article><h1>' + e(p["name"]) + '</h1><p>' +
            e(p["summary_original"]) + '</p>' + map_link + relation_text +
            '<section><h2>Fuentes</h2><ul>' + evidence + '</ul></section></article>')
    structured = {"@type": "Place", "@id": SITE + url, "name": p["name"],
                  "description": p["summary_original"], "url": SITE + url, **geo}
    return page(p["name"] + " — Atlas literario", p["summary_original"],
                url, body, [crumbs, structured])


def pages_from(data: dict, reading_links: dict[str, str] | None = None) -> dict[str, str]:
    destinations, places = eligible(data)
    if not destinations:
        return {}  # Nunca generar hub indexable vacío
    ids = {d["id"]: d for d in destinations}
    src = {s["id"]: s for s in data.get("sources", [])}
    titles = {}
    for category, field in (("works", "title"), ("authors", "name"), ("adaptations", "title")):
        titles[category] = {v["id"]: v.get(field, "") for v in data.get(category, []) if approved(v)}
    valid_works = set(titles["works"])
    valid_authors = set(titles["authors"])
    valid_adaptations = set(titles["adaptations"])
    approved_places = {p["id"] for p in places}
    rels = [
        r for r in data.get("relationships", [])
        if approved(r) and r.get("place_id") in approved_places
        and ((r.get("subject_type") == "work" and r.get("subject_id") in valid_works)
             or (r.get("subject_type") == "author" and r.get("subject_id") in valid_authors)
             or (r.get("subject_type") == "adaptation" and r.get("subject_id") in valid_adaptations))
        and RELATION_SUBJECTS.get(r.get("relationship_type")) == r.get("subject_type")
        and bool(r.get("evidence_note"))
        and isinstance(r.get("source_ids"), list) and r["source_ids"]
        and all(source in src and valid_https_url(src[source].get("url"))
                and src[source].get("title") and src[source].get("retrieved_at")
                and src[source].get("evidence_summary") for source in r["source_ids"])
    ]
    name_tables = {"work": titles["works"], "author": titles["authors"],
                   "adaptation": titles["adaptations"]}
    pages: dict[str, str] = {}
    for d in destinations:
        url = destination_url(d)
        if url in pages:
            raise ValueError("URL de destino duplicada: " + url)
        ps = [p for p in places if p["destination_id"] == d["id"]]
        pages[url] = destination_page(d, ps)
    for p in places:
        url = place_url(p)
        if url in pages:
            raise ValueError("URL de lugar duplicada: " + url)
        matched = [
            dict(r,
                 subject_name=name_tables[r["subject_type"]][r["subject_id"]],
                 catalogue_url=(reading_links or {}).get(r["subject_id"])
                 if r["subject_type"] == "work" else None)
            for r in rels if r["place_id"] == p["id"]
        ]
        pages[url] = place_page(p, ids[p["destination_id"]], src, matched)
    cards = "".join('<li><a href="' + e(destination_url(d)) + '">'
                    + e(d["name"]) + '</a></li>' for d in destinations)
    home_url = "/atlas-literario/"
    home = '<h1>Atlas de viajes literarios</h1><p>Destinos con lugares verificados.</p><ul>' + cards + '</ul>'
    pages[home_url] = page("Atlas literario mundial", "Lugares y viajes literarios investigados.",
                           home_url, home, [{"@type": "CollectionPage", "name": "Atlas literario mundial",
                                           "url": SITE + home_url}])
    return pages


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("snapshot", type=Path, help="Snapshot editorial APROBADO")
    p.add_argument("--out", type=Path, required=True, help="Ruta de PREVIEW, no directorio web")
    p.add_argument("--reading-catalogue", type=Path,
                   help="Catálogo actual de obras; enlazar solo IDs publicados")
    args = p.parse_args()
    if "atlas-preview" not in args.out.parts:
        p.error("Salida restringida a un directorio que incluya atlas-preview")
    data = json.loads(args.snapshot.read_text(encoding="utf-8"))
    reading_links = None
    if args.reading_catalogue:
        from atlas_reading_crosslinks import canonical_links
        reading = json.loads(args.reading_catalogue.read_text(encoding="utf-8"))
        reading_links = canonical_links(data, reading)
    for url, content in pages_from(data, reading_links).items():
        relative = url.removeprefix("/")
        target = args.out / relative / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    print("Atlas preview generado; NO modifica main, sitemap ni sitio publicado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
