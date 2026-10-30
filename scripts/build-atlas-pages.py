#!/usr/bin/env python3
'''Atlas literario: catálogo filtrable de destinos, lugares y rutas.

Un solo grafo (destinos, lugares, obras, autores, relaciones, rutas y fuentes) en
`data/atlas/catalogue.json`, validado con `scripts/atlas_contract_check.py`, más una
capa editorial en `data/atlas/editorial.json` con el texto propio de las fichas.
Genera `/atlas-literario/` (catálogo con filtros, como Libros recomendados) y una
página por destino, lugar o ruta con contenido editorial. Los lugares sin ficha
propia aparecen en el catálogo y en la página de su destino o ruta.

Uso:
  python scripts/build-atlas-pages.py --data data/atlas/catalogue.json --root .
  python scripts/build-atlas-pages.py --data data/atlas/catalogue.json --root . --check
'''
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from site_shell import inject_shell_auto  # noqa: E402


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_topics = _load("build_topic_collections", "build-topic-collections.py")
_contract = _load("atlas_contract_check", "atlas_contract_check.py")
esc = _topics.esc
SITE = _topics.SITE

ATLAS_URL = f"{SITE}/atlas-literario/"
CSS_OLD = '<link rel="stylesheet" href="/assets/v1-cuaderno-topics.css?v=1"><link rel="stylesheet" href="/assets/cuaderno-index.css?v=1">'
CSS_PAGE = '<link rel="stylesheet" href="/assets/v1-atlas.css?v=4">'
CSS_HUB = (
    '<link rel="stylesheet" href="/assets/v1-tools.css?v=6"><link rel="stylesheet" href="/assets/v1-recommendations.css?v=2">'
    '<link rel="stylesheet" href="/assets/reading-catalogue.css?v=15"><link rel="stylesheet" href="/assets/v1-atlas.css?v=4">'
)
HUB_SCRIPT = '<script defer src="/assets/atlas-catalogue.js?v=2"></script>'
LABELS = ("hecho", "tradicion", "atribucion", "ficcion")

COUNTRIES = {
    "AR": "Argentina", "CZ": "República Checa", "EG": "Egipto", "ES": "España", "FR": "Francia",
    "GB": "Reino Unido", "IE": "Irlanda", "PT": "Portugal", "IT": "Italia", "DE": "Alemania",
    "US": "Estados Unidos", "MX": "México", "CO": "Colombia", "CL": "Chile", "PE": "Perú",
    "AT": "Austria", "NL": "Países Bajos", "BE": "Bélgica", "CH": "Suiza", "SE": "Suecia",
    "NO": "Noruega", "DK": "Dinamarca", "PL": "Polonia", "RU": "Rusia", "JP": "Japón",
}
PLACE_TYPES = {
    "bookshop": "Librería", "library": "Biblioteca", "museum": "Museo",
    "writer_house_museum": "Casa de escritor", "booktown": "Pueblo del libro",
    "monument": "Monumento", "literary_plaque": "Placa literaria", "street": "Calle",
    "square": "Plaza", "cafe": "Café o bar", "film_location": "Rodaje",
    "landscape": "Paisaje", "festival": "Fiesta del libro", "other": "Otro lugar",
    "historic_site": "Lugar histórico",
}
RELATION_LABELS = {
    "narrative_explicit": "Aparece en la obra",
    "author_public_history": "Vida del autor",
    "inspiration_documented": "Inspiró la obra",
    "filming_location": "Rodaje de una adaptación",
    "literary_homage": "Homenaje literario",
}
VISIT = {"visit_inside": "Se puede entrar", "reservation": "Con reserva", "outside": "Solo exterior"}
KIND_LABEL = {"destination": "Destino", "place": "Lugar", "route": "Ruta"}


class ValidationError(Exception):
    pass




def norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn")


def slug_id(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", norm(text)).strip("-")


def merge_directory(catalogue: dict, directory: dict, config: dict) -> dict:
    """Añade al catálogo las entradas automáticas de Wikidata como lugares aprobados sin ficha propia."""
    places = directory.get("places") or []
    if not places:
        return catalogue
    cap = int(config.get("max_directory_cards", 400))
    merged = json.loads(json.dumps(catalogue))
    updated = directory["updated"]
    dests = {(norm(d["name"]), d["country_iso2"]): d for d in merged["destinations"]}
    taken_ids = {d["id"] for d in merged["destinations"]} | {p["id"] for p in merged["places"]}
    have_names = {(norm(p["name"]), p["destination_id"]) for p in merged["places"]}
    have_urls = {p.get("official_url") for p in merged["places"] if p.get("official_url")}
    for entry in places[:cap]:
        if entry["official_url"] in have_urls:
            continue
        key = (norm(entry["city"]), entry["country_iso2"])
        dest = dests.get(key)
        if dest is None:
            dest_id = slug_id(entry["city"])
            if dest_id in taken_ids or len(dest_id) < 3 or not dest_id[0].isalpha():
                dest_id = (slug_id(entry["city"]) or "destino") + "-" + entry["country_iso2"].lower()
            if len(dest_id) < 3 or not dest_id[0].isalpha():
                continue
            taken_ids.add(dest_id)
            dest = {"id": dest_id, "status": "approved", "verified_at": updated, "slug": dest_id, "name": entry["city"],
                    "country_iso2": entry["country_iso2"],
                    "summary_original": f"Lugares literarios en {entry['city']}."}
            merged["destinations"].append(dest)
            dests[key] = dest
        if (norm(entry["name"]), dest["id"]) in have_names:
            continue
        pid = "wd-" + entry["qid"].lower()
        sid = "wikidata-" + entry["qid"].lower()
        merged["sources"].append({
            "id": sid, "url": f"https://www.wikidata.org/wiki/{entry['qid']}", "title": f"Wikidata: {entry['name']}",
            "publisher": "Wikidata", "retrieved_at": updated, "source_kind": "wikidata_statement",
            "evidence_summary": "Declaraciones de Wikidata sobre tipo de lugar, web oficial y ubicación.",
            "license_review": "not_required_for_link", "dataset_license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "license_name": "CC0 1.0", "attribution_text": "Datos de Wikidata (CC0 1.0)", "provider_record_id": entry["qid"],
        })
        summary = entry.get("description") or f"{PLACE_TYPES[entry['place_type']]} en {entry['city']}."
        merged["places"].append({
            "id": pid, "status": "approved", "verified_at": updated, "slug": pid, "name": entry["name"],
            "destination_id": dest["id"], "place_type": entry["place_type"], "geo_precision": "building",
            "latitude": entry["latitude"], "longitude": entry["longitude"], "wikidata_qid": entry["qid"],
            "official_url": entry["official_url"], "summary_original": summary[:200], "source_ids": [sid],
        })
        have_names.add((norm(entry["name"]), dest["id"]))
    return merged


class Atlas:
    """Vista de lectura del catálogo y de la capa editorial."""

    def __init__(self, catalogue: dict, editorial: dict) -> None:
        self.cat = catalogue
        self.ed = editorial
        self.dest = {d["id"]: d for d in catalogue["destinations"] if d["status"] == "approved"}
        self.places = {p["id"]: p for p in catalogue["places"] if p["status"] == "approved"}
        self.works = {w["id"]: w for w in catalogue["works"] if w["status"] == "approved"}
        self.authors = {a["id"]: a for a in catalogue["authors"] if a["status"] == "approved"}
        self.routes = {r["id"]: r for r in catalogue["routes"] if r["status"] == "approved"}
        self.sources = {s["id"]: s for s in catalogue["sources"]}
        self.pages = editorial["pages"]
        # Solo las relaciones aprobadas se muestran; las demás son mesa editorial.
        self.rels = [r for r in catalogue["relationships"] if r["status"] == "approved"]
        self.rels_by_place: dict[str, list[dict]] = {}
        for r in self.rels:
            self.rels_by_place.setdefault(r["place_id"], []).append(r)

    def kind(self, slug: str) -> str | None:
        if slug in self.routes:
            return "route"
        if slug in self.places:
            return "place"
        if slug in self.dest:
            return "destination"
        return None

    def country_name(self, iso: str) -> str:
        return COUNTRIES.get(iso, iso)

    def subject_name(self, rel: dict) -> str:
        table = self.works if rel["subject_type"] == "work" else self.authors
        entry = table[rel["subject_id"]]
        return entry.get("title") or entry["name"]

    def place_page_url(self, place: dict) -> str | None:
        return f"/atlas-literario/{place['slug']}/" if place["slug"] in self.pages else None

    def parent_page(self, place: dict) -> str | None:
        """Página interna donde se explica un lugar sin ficha propia."""
        for route in self.routes.values():
            if place["id"] in route["place_ids"] and route["slug"] in self.pages:
                return f"/atlas-literario/{route['slug']}/"
        if place["destination_id"] in self.pages:
            return f"/atlas-literario/{place['destination_id']}/"
        return None


def validate(catalogue: dict, editorial: dict) -> None:
    problems = _contract.problems(catalogue)
    if problems:
        raise ValidationError("contrato del Atlas: " + "; ".join(problems[:5]))
    atlas = Atlas(catalogue, editorial)
    if not set(editorial.get("labels", {})) == set(LABELS):
        raise ValidationError("labels debe definir " + ", ".join(LABELS))
    for slug, page in atlas.pages.items():
        if atlas.kind(slug) is None:
            raise ValidationError(f"{slug}: la ficha editorial no corresponde a ninguna entidad del catálogo")
        for key in ("title", "description", "lead", "sections", "facts", "sources"):
            if not page.get(key):
                raise ValidationError(f"{slug}: falta {key}")
        if len(page["description"]) < 60:
            raise ValidationError(f"{slug}: description demasiado corta")
        for fact in page["facts"]:
            if fact.get("label") not in LABELS or not str(fact.get("text", "")).strip():
                raise ValidationError(f"{slug}: hecho sin etiqueta válida")
        for sid in page["sources"]:
            if sid not in atlas.sources:
                raise ValidationError(f"{slug}: fuente desconocida {sid!r}")
        for rel in page.get("related", []):
            if rel not in atlas.pages or rel == slug:
                raise ValidationError(f"{slug}: related desconocido {rel!r}")
    for place in atlas.places.values():
        if not (place.get("official_url") or atlas.place_page_url(place) or atlas.parent_page(place)):
            raise ValidationError(f"{place['id']}: sin ficha, web oficial ni página de destino o ruta")


# ---------------------------------------------------------------- piezas HTML


def breadcrumb_html(items: list[tuple[str, str | None]]) -> str:
    return _topics.render_breadcrumb(items).replace("cuaderno-topics-breadcrumb", "atlas-breadcrumb")


def hero(eyebrow: str, title: str, lead: str) -> str:
    """Mismo encabezado que el resto de catálogos (libros, autores, editoriales): .catalogue-hero."""
    return (
        '<header class="catalogue-hero">'
        f'<p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(title)}</h1><p>{esc(lead)}</p></header>'
    )


def jsonld(canonical: str, name: str, description: str, modified: str, crumbs: list, extra: list) -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage", "@id": canonical + "#page", "url": canonical, "name": name,
                "description": description, "dateModified": modified, "inLanguage": "es",
                "isPartOf": {"@id": f"{SITE}/#website"}, "author": {"@id": f"{SITE}/#author"},
                "breadcrumb": {"@id": canonical + "#breadcrumb"},
            },
            *extra,
            {**_topics.breadcrumb_jsonld(crumbs), "@id": canonical + "#breadcrumb"},
        ],
    }


def wrap(title: str, description: str, canonical: str, schema: dict, main: str, hub: bool = False) -> str:
    page = _topics.head(title, description, canonical, schema)
    if CSS_OLD not in page:
        raise ValidationError("head de las colecciones cambió: revisa CSS_OLD")
    page = page.replace(CSS_OLD, CSS_HUB if hub else CSS_PAGE)
    footer = _topics.SHELL_FOOTER
    if hub:
        footer = footer.replace("</body>", HUB_SCRIPT + "</body>", 1)
    return page + main + footer


def relation_chips(atlas: Atlas, place_id: str) -> list[tuple[str, str]]:
    return [(RELATION_LABELS[r["relationship_type"]], atlas.subject_name(r)) for r in atlas.rels_by_place.get(place_id, [])
            if r["relationship_type"] in RELATION_LABELS]


def card_attrs(**values: str) -> str:
    return " ".join(f'data-{k}="{esc(v)}"' for k, v in values.items())


def summary_of(entity: dict, page: dict | None) -> str:
    text = (page or {}).get("description") or entity.get("summary_original") or ""
    return text if len(text) <= 200 else text[:197].rsplit(" ", 1)[0] + "…"


def build_cards(atlas: Atlas) -> list[dict]:
    """Una tarjeta por destino con ficha, lugar y ruta, con todos sus valores de filtro."""
    cards: list[dict] = []
    for dest in atlas.dest.values():
        if dest["slug"] not in atlas.pages:
            continue
        page = atlas.pages[dest["slug"]]
        cards.append({
            "kind": "destination", "title": dest["name"], "href": f"/atlas-literario/{dest['slug']}/", "external": False,
            "where": atlas.country_name(dest["country_iso2"]), "summary": summary_of(dest, page),
            "pais": dest["country_iso2"], "destino": dest["id"], "tipo": "destination",
            "vinculo": [], "obra": [], "autor": [], "visita": "", "type_label": "Destino", "chips": [],
        })
    for place in atlas.places.values():
        dest = atlas.dest[place["destination_id"]]
        rels = atlas.rels_by_place.get(place["id"], [])
        href = atlas.place_page_url(place)
        external = False
        cta = "Ver ficha"
        if not href:
            href = atlas.parent_page(place)
            cta = "Ver en " + ("la ruta" if href and "ruta-" in href else dest["name"])
        if not href:
            href, external, cta = place["official_url"], True, "Web oficial"
        cards.append({
            "kind": "place", "title": place["name"], "href": href, "external": external, "cta": cta,
            "official": place.get("official_url", ""),
            "where": f"{dest['name']} · {atlas.country_name(dest['country_iso2'])}",
            "summary": summary_of(place, atlas.pages.get(place["slug"])),
            "pais": dest["country_iso2"], "destino": dest["id"], "tipo": place["place_type"],
            "vinculo": sorted({r["relationship_type"] for r in rels if r["relationship_type"] in RELATION_LABELS}),
            "obra": sorted({r["subject_id"] for r in rels if r["subject_type"] == "work"}),
            "autor": sorted({r["subject_id"] for r in rels if r["subject_type"] == "author"}),
            "visita": place.get("visit_status", ""), "type_label": PLACE_TYPES[place["place_type"]],
            "chips": relation_chips(atlas, place["id"]),
        })
    for route in atlas.routes.values():
        if route["slug"] not in atlas.pages:
            continue
        dest = atlas.dest[route["destination_id"]]
        stops = [atlas.places[p] for p in route["place_ids"]]
        rels = [r for p in stops for r in atlas.rels_by_place.get(p["id"], [])]
        cards.append({
            "kind": "route", "title": route["title"], "href": f"/atlas-literario/{route['slug']}/", "external": False,
            "where": f"{dest['name']} · {atlas.country_name(dest['country_iso2'])}",
            "summary": summary_of(route, atlas.pages.get(route["slug"])),
            "pais": dest["country_iso2"], "destino": dest["id"], "tipo": "route",
            "vinculo": sorted({r["relationship_type"] for r in rels if r["relationship_type"] in RELATION_LABELS}),
            "obra": sorted({r["subject_id"] for r in rels if r["subject_type"] == "work"}),
            "autor": sorted({r["subject_id"] for r in rels if r["subject_type"] == "author"}),
            "visita": "", "type_label": f"Ruta · {len(stops)} paradas", "chips": [],
        })
    order = {"destination": 0, "route": 1, "place": 2}
    cards.sort(key=lambda c: (order[c["kind"]], norm(c["title"])))
    return cards


def facet_group(key: str, title: str, options: list[tuple[str, str]], opened: bool = False) -> str:
    if not options:
        return ""
    boxes = "".join(
        f'<label class="catalogue-check"><input type="checkbox" id="{key}={esc(v)}" name="{key}" value="{esc(v)}" data-facet="{key}">'
        f'<span>{esc(label)}</span><small data-facet-count></small></label>'
        for v, label in options
    )
    return (
        f'<details class="catalogue-facet" data-facet-group="{key}"{" open" if opened else ""}>'
        f'<summary>{esc(title)} <small data-facet-selected></small></summary>'
        f'<div class="catalogue-facet__options">{boxes}</div></details>'
    )


def render_card(card: dict, index: int) -> str:
    attrs = card_attrs(
        kind=card["kind"], pais=card["pais"], destino=card["destino"], tipo=card["tipo"],
        vinculo=" ".join(card["vinculo"]), obra=" ".join(card["obra"]), autor=" ".join(card["autor"]),
        visita=card["visita"], title=card["title"],
        search=" ".join([card["title"], card["where"], card["summary"], card["type_label"]]
                        + [c[1] for c in card["chips"]]),
    )
    chips = "".join(f'<li><span class="atlas-chip__k">{esc(k)}</span> {esc(v)}</li>' for k, v in card["chips"])
    chips_html = f'<ul class="atlas-chips">{chips}</ul>' if chips else ""
    official = ""
    external = bool(card.get("external"))
    if card.get("official") and card["kind"] == "place" and not external and not card["href"].endswith("/" + slug_id(card["title"]) + "/"):
        official = (f'<a class="atlas-card__official" href="{esc(card["official"])}" target="_blank" '
                    f'rel="noopener noreferrer">Web oficial<span class="sr-only"> de {esc(card["title"])} (otra pestaña)</span></a>')
    cta = card.get("cta") or ("Explorar" if card["kind"] != "place" else "Ver ficha")
    tgt = ' target="_blank" rel="noopener noreferrer"' if external else ""
    hidden_ext = f'<span class="sr-only"> (otra pestaña)</span>' if external else ""
    return (
        f'<li class="catalogue-card atlas-card" data-atlas-card {attrs}>'
        f'<p class="atlas-card__meta"><span>{esc(card["type_label"])}</span><span>{esc(card["where"])}</span></p>'
        f'<h3><a href="{esc(card["href"])}"{tgt}>{esc(card["title"])}{hidden_ext}</a></h3>'
        f'<p class="atlas-card__summary">{esc(card["summary"])}</p>{chips_html}'
        f'<p class="atlas-card__actions"><a class="text-action" href="{esc(card["href"])}"{tgt}>{esc(cta)}'
        f'<span class="sr-only">: {esc(card["title"])}{" (otra pestaña)" if external else ""}</span></a>{official}</p></li>'
    )


def render_hub(atlas: Atlas, cards: list[dict]) -> str:
    title = "Atlas literario | David Porto Díaz"
    description = (
        "Bibliotecas, librerías, casas de escritores y rutas para viajar con los libros: filtra por país, "
        "ciudad, tipo de lugar, obra o autor, con fuentes y certeza de cada dato."
    )
    country_opts = sorted({(c["pais"], atlas.country_name(c["pais"])) for c in cards}, key=lambda x: norm(x[1]))
    dest_opts = sorted({(c["destino"], atlas.dest[c["destino"]]["name"]) for c in cards}, key=lambda x: norm(x[1]))
    tipo_used = {c["tipo"] for c in cards}
    tipo_opts = [("destination", "Destino (ciudad)"), ("route", "Ruta")] + sorted(
        [(k, v) for k, v in PLACE_TYPES.items() if k in tipo_used], key=lambda x: norm(x[1]))
    tipo_opts = [o for o in tipo_opts if o[0] in tipo_used]
    vinc_used = {v for c in cards for v in c["vinculo"]}
    vinc_opts = [(k, v) for k, v in RELATION_LABELS.items() if k in vinc_used]
    work_used = {w for c in cards for w in c["obra"]}
    work_opts = sorted([(w, atlas.works[w]["title"]) for w in work_used], key=lambda x: norm(x[1]))
    author_used = {a for c in cards for a in c["autor"]}
    author_opts = sorted([(a, atlas.authors[a]["name"]) for a in author_used], key=lambda x: norm(x[1]))
    visit_used = {c["visita"] for c in cards if c["visita"]}
    visit_opts = [(k, v) for k, v in VISIT.items() if k in visit_used]
    facets = (
        facet_group("pais", "País", country_opts, True) + facet_group("destino", "Ciudad o destino", dest_opts)
        + facet_group("tipo", "Tipo de lugar", tipo_opts, True) + facet_group("vinculo", "Vínculo con los libros", vinc_opts)
        + facet_group("obra", "Obra", work_opts) + facet_group("autor", "Autor", author_opts)
        + facet_group("visita", "Cómo se visita", visit_opts)
    )
    grid = "".join(render_card(c, i) for i, c in enumerate(cards))
    n = len(cards)
    section = (
        '<section class="catalogue-section" id="catalogo" aria-label="Buscar en el Atlas literario">'
        '<div class="catalogue-layout"><aside class="catalogue-sidebar">'
        '<form id="atlas-search-form" class="catalogue-filters" data-atlas-filters><fieldset disabled>'
        '<legend>Explora el Atlas</legend>'
        '<label class="catalogue-search">Buscar por lugar, ciudad, obra o autor'
        '<input type="search" name="q" data-filter="q" maxlength="200" autocomplete="off" placeholder="¿Adónde te lleva un libro?"></label>'
        f'<div class="catalogue-facets">{facets}</div>'
        '<div class="catalogue-filter-actions"><button type="submit">Buscar lugares</button><button type="reset" disabled>Restablecer</button></div>'
        '</fieldset></form></aside>'
        '<div class="catalogue-main"><div class="catalogue-results-head"><h2>El atlas</h2>'
        f'<p role="status" aria-live="polite" data-atlas-count>{n} resultados</p></div>'
        f'<ul class="catalogue-grid atlas-grid">{grid}</ul>'
        '<p class="atlas-empty" data-atlas-empty hidden>No hay lugares con esa combinación. Quita algún filtro.</p>'
        '<p class="atlas-more" data-atlas-more-wrap hidden><button type="button" data-atlas-more>Mostrar más</button></p>'
        '</div></div></section>'
    )
    schema = jsonld(
        ATLAS_URL, title, description, atlas.ed["verified"], [("Inicio", SITE + "/"), ("Atlas literario", None)],
        [{
            "@type": "ItemList", "@id": ATLAS_URL + "#list",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "url": SITE + c["href"], "name": c["title"]}
                for i, c in enumerate(cards, 1) if c["href"]
            ],
        }],
    )
    main = (
        '<main id="contenido" tabindex="-1" class="v1-main reading-catalogue atlas-catalogue" data-family="atlas">'
        + breadcrumb_html([("Inicio", "/"), ("Atlas literario", None)])
        + hero("Lugares reales", "Atlas literario",
               "Bibliotecas, librerías, casas de escritores y rutas que se pueden visitar, con fuentes y la certeza de cada dato.")
        + section
        + f'<section class="atlas-tail"><p>Revisión del Atlas: <time datetime="{esc(atlas.ed["verified"])}">{esc(atlas.ed["verified"])}</time></p>'
        + '<p><a href="/recomendaciones/">Libros recomendados</a></p></section></main>'
    )
    return wrap(title, description, ATLAS_URL, schema, main, hub=True)


def facts_html(atlas: Atlas, page: dict) -> str:
    return "".join(
        f'<li><span class="atlas-tag" data-certainty="{f["label"]}">{esc(atlas.ed["labels"][f["label"]])}</span>{esc(f["text"])}</li>'
        for f in page["facts"]
    )


def place_row(atlas: Atlas, place: dict) -> str:
    href = atlas.place_page_url(place)
    name = f'<a href="{href}">{esc(place["name"])}</a>' if href else f'<strong>{esc(place["name"])}</strong>'
    kind = PLACE_TYPES[place["place_type"]]
    chips = "; ".join(f"{k}: {v}" for k, v in relation_chips(atlas, place["id"]))
    official = (f' <a href="{esc(place["official_url"])}" target="_blank" rel="noopener noreferrer">Web oficial'
                f'<span class="sr-only"> de {esc(place["name"])} (otra pestaña)</span></a>') if place.get("official_url") and not href else ""
    return (f'<li>{name}<small>{esc(kind)}{" · " + esc(chips) if chips else ""}</small>'
            f'{esc(place["summary_original"]) if not href else ""}{official}</li>')


def render_entry(atlas: Atlas, slug: str) -> str:
    page = atlas.pages[slug]
    kind = atlas.kind(slug)
    canonical = f"{ATLAS_URL}{slug}/"
    title = f"{page['title']} | Atlas literario | David Porto Díaz"
    if len(title) > 75:  # límite de scripts/check-seo-meta-quality.py
        title = f"{page['title']} | Atlas literario"
    crumbs = [("Inicio", SITE + "/"), ("Atlas literario", ATLAS_URL), (page["title"], None)]
    extra: list[dict] = []
    aside: list[str] = []
    if kind == "route":
        route = atlas.routes[slug]
        stops_places = [atlas.places[p] for p in route["place_ids"]]
        extra.append({
            "@type": "ItemList", "@id": canonical + "#stops", "itemListOrder": "https://schema.org/ItemListOrderAscending",
            "itemListElement": [{"@type": "ListItem", "position": i, "name": p["name"]} for i, p in enumerate(stops_places, 1)],
        })
        stops = "".join(
            f'<li>{"<a href=" + chr(34) + (atlas.place_page_url(p) or "") + chr(34) + ">" + esc(p["name"]) + "</a>" if atlas.place_page_url(p) else "<strong>" + esc(p["name"]) + "</strong>"}'
            f'<small>{esc(PLACE_TYPES[p["place_type"]])}</small>{esc(p["summary_original"])}'
            + (f' <a href="{esc(p["official_url"])}" target="_blank" rel="noopener noreferrer">Web oficial<span class="sr-only"> de {esc(p["name"])} (otra pestaña)</span></a>' if p.get("official_url") else "")
            + "</li>"
            for p in stops_places
        )
        aside.append(f'<section aria-labelledby="atlas-paradas"><h2 id="atlas-paradas">Paradas</h2><ol class="atlas-stops">{stops}</ol></section>')
    elif kind == "destination":
        dest = atlas.dest[slug]
        here = [p for p in atlas.places.values() if p["destination_id"] == slug]
        routes_here = [r for r in atlas.routes.values() if r["destination_id"] == slug and r["slug"] in atlas.pages]
        if here:
            rows = "".join(place_row(atlas, p) for p in sorted(here, key=lambda p: norm(p["name"])))
            aside.append(f'<section aria-labelledby="atlas-lugares"><h2 id="atlas-lugares">Lugares</h2><ul class="atlas-stops atlas-stops--plain">{rows}</ul></section>')
        if routes_here:
            rows = "".join(f'<li><a href="/atlas-literario/{r["slug"]}/">{esc(r["title"])}</a></li>' for r in routes_here)
            aside.append(f'<section aria-labelledby="atlas-rutas"><h2 id="atlas-rutas">Rutas</h2><ul class="atlas-plain">{rows}</ul></section>')
    elif kind == "place":
        place = atlas.places[slug]
        chips = relation_chips(atlas, slug)
        if chips:
            rows = "".join(f"<li><strong>{esc(k)}</strong> {esc(v)}</li>" for k, v in chips)
            aside.append(f'<section aria-labelledby="atlas-vinculos"><h2 id="atlas-vinculos">Vínculo con los libros</h2><ul class="atlas-plain">{rows}</ul></section>')
        dest = atlas.dest[place["destination_id"]]
        crumbs = [("Inicio", SITE + "/"), ("Atlas literario", ATLAS_URL), (page["title"], None)]
    aside.append(f'<section aria-labelledby="atlas-datos"><h2 id="atlas-datos">Qué sabemos</h2><ul class="atlas-facts">{facts_html(atlas, page)}</ul></section>')
    if page.get("practical"):
        practical = "".join(f"<li>{esc(p)}</li>" for p in page["practical"])
        aside.append(f'<section aria-labelledby="atlas-practico"><h2 id="atlas-practico">Antes de ir</h2><ul class="atlas-plain">{practical}</ul></section>')
    sources = "".join(
        f'<li><a href="{esc(atlas.sources[s]["url"])}" rel="noopener noreferrer">{esc(atlas.sources[s]["title"])}</a></li>'
        for s in page["sources"]
    )
    aside.append(f'<section aria-labelledby="atlas-fuentes"><h2 id="atlas-fuentes">Fuentes</h2><ul class="atlas-plain">{sources}</ul></section>')
    if page.get("related"):
        related = "".join(f'<li><a href="/atlas-literario/{r}/">{esc(atlas.pages[r]["title"])}</a></li>' for r in page["related"])
        aside.append(f'<section aria-labelledby="atlas-relacionado"><h2 id="atlas-relacionado">Sigue por aquí</h2><ul class="atlas-plain">{related}</ul></section>')
    schema = jsonld(canonical, page["title"], page["description"], atlas.ed["verified"], crumbs, extra)
    sections = "".join(f'<h2>{esc(s["h"])}</h2>' + "".join(f"<p>{esc(p)}</p>" for p in s["p"]) for s in page["sections"])
    main = (
        '<main id="contenido" tabindex="-1" class="v1-main" data-family="atlas">'
        + breadcrumb_html([("Inicio", "/"), ("Atlas literario", "/atlas-literario/"), (page["title"], None)])
        + hero(f"{KIND_LABEL[kind]} · {page['country_label']}", page["title"], page["lead"])
        + f'<div class="atlas-article"><div class="atlas-article__main" data-pagefind-filter="atlas_entity:{kind}">{sections}</div>'
        + f'<aside class="atlas-aside" aria-label="Datos de la ficha">{"".join(aside)}</aside></div>'
        + f'<section class="atlas-tail"><p>Datos revisados el <time datetime="{esc(atlas.ed["verified"])}">{esc(atlas.ed["verified"])}</time>. '
        + 'Si ves un error, escríbenos desde la <a href="/metodologia-editorial/">metodología editorial</a>.</p>'
        + '<p><a href="/atlas-literario/">← Todo el Atlas</a></p></section></main>'
    )
    return wrap(title, page["description"], canonical, schema, main)


# ------------------------------------------------------- registro y mapa del sitio


def registry_entries(atlas: Atlas) -> list[dict]:
    out = [{
        "id": "atlas-hub", "url": "/atlas-literario/", "label": "Atlas literario", "shortLabel": "Atlas literario",
        "type": "article", "territory": "recomendaciones", "parentId": "recommendations-hub",
        "hubId": "recommendations-hub", "discoverability": "secondary", "footerEligible": True,
        "audience": ["reader"], "jobs": ["explorar-atlas"], "sourceFile": "atlas-literario/index.html",
    }]
    for slug, page in atlas.pages.items():
        out.append({
            "id": "atlas-" + slug, "url": f"/atlas-literario/{slug}/", "label": page["title"],
            "shortLabel": page["title"].split(":")[0][:40], "type": "article", "territory": "recomendaciones",
            "parentId": "atlas-hub", "hubId": "recommendations-hub", "discoverability": "contextual",
            "audience": ["reader"], "jobs": ["explorar-atlas"], "sourceFile": f"atlas-literario/{slug}/index.html",
        })
    return out


def sync_registry(root: Path, atlas: Atlas, write: bool) -> bool:
    path = root / "data" / "content-registry.json"
    if not path.is_file():
        return True
    registry = json.loads(path.read_text(encoding="utf-8"))
    have = {e.get("id") for e in registry["entries"]}
    missing = [e for e in registry_entries(atlas) if e["id"] not in have]
    if missing and write:
        registry["entries"].extend(missing)
        path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return not missing


MAP_START = "<!-- atlas-map:start -->"
MAP_END = "<!-- atlas-map:end -->"


def render_site_map(document: str, atlas: Atlas) -> str:
    start, end = document.find(MAP_START), document.find(MAP_END)
    if start < 0 or end < start:
        raise ValidationError("mapa-del-sitio/index.html sin marcadores atlas-map")
    items = '<li><a href="/atlas-literario/">Atlas literario</a></li>' + "".join(
        f'<li><a href="/atlas-literario/{slug}/">{esc(page["title"])}</a></li>' for slug, page in atlas.pages.items()
    )
    return document[: start + len(MAP_START)] + items + document[end:]


# --------------------------------------------------------------------- construcción


def build(data_path: Path, root: Path, check_only: bool) -> tuple[int, bool]:
    catalogue = json.loads(data_path.read_text(encoding="utf-8"))
    editorial = json.loads((data_path.parent / "editorial.json").read_text(encoding="utf-8"))
    directory_path = data_path.parent / "directory.json"
    config_path = data_path.parent / "feed-config.json"
    if directory_path.is_file():
        config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.is_file() else {}
        catalogue = merge_directory(catalogue, json.loads(directory_path.read_text(encoding="utf-8")), config)
    validate(catalogue, editorial)
    atlas = Atlas(catalogue, editorial)
    cards = build_cards(atlas)

    outputs = {"atlas-literario/index.html": inject_shell_auto(render_hub(atlas, cards))}
    for slug in atlas.pages:
        outputs[f"atlas-literario/{slug}/index.html"] = inject_shell_auto(render_entry(atlas, slug))
    map_path = root / "mapa-del-sitio" / "index.html"
    if map_path.is_file():
        outputs["mapa-del-sitio/index.html"] = render_site_map(map_path.read_text(encoding="utf-8"), atlas)
    routes = [{"url": "/atlas-literario/", "kind": "hub"}] + [
        {"url": f"/atlas-literario/{slug}/", "kind": atlas.kind(slug)} for slug in atlas.pages
    ]
    outputs["data/atlas-routes-manifest.json"] = json.dumps(
        {"schema_version": 1, "routes": routes}, ensure_ascii=False, indent=2) + "\n"

    drift: list[str] = []
    for rel, content in outputs.items():
        path = root / rel
        if check_only:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                drift.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if not sync_registry(root, atlas, write=not check_only) and check_only:
        drift.append("data/content-registry.json (faltan entradas del Atlas)")
    atlas_dir = root / "atlas-literario"
    if atlas_dir.is_dir():
        for path in atlas_dir.rglob("index.html"):
            rel = path.relative_to(root).as_posix()
            if rel not in outputs:
                drift.append(f"{rel} (sin entrada en el catálogo)")
    if check_only:
        if drift:
            print("FAIL: salida desactualizada: " + ", ".join(drift))
            return len(outputs), False
        print(f"PASS: {len(cards)} entradas en el catálogo, {len(atlas.pages)} fichas y hub, salida al día")
        return len(outputs), True
    print(f"GENERATED: hub con {len(cards)} entradas + {len(atlas.pages)} ficha(s) del Atlas")
    return len(outputs), True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        _, ok = build(args.data, args.root, args.check)
    except (OSError, json.JSONDecodeError, ValidationError, KeyError) as exc:
        print(f"FAIL: {exc!r}", file=sys.stderr)
        return 1
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
