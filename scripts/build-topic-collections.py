#!/usr/bin/env python3
"""Hubs de colecciones tematicas del Cuaderno (doc 55).

Genera `/cuaderno/temas/` (indice) y `/cuaderno/temas/{slug}/` (un hub por
cada coleccion con status "ready"). Los articulos siguen en sus URLs
actuales; esto solo añade una capa de navegacion que explica por que varias
piezas forman un conjunto.

El gate de 3 piezas para "ready" (doc 55, seccion 5) NO es una regla SEO: es
una barrera editorial para no publicar hubs de una o dos tarjetas. Una
coleccion con menos piezas debe quedarse en "draft" — el builder simplemente
no genera pagina para ella, no falla el build (fallar obligaria a completar
la coleccion o borrarla del JSON solo para poder desplegar el resto).

Uso:
  # generar
  python scripts/build-topic-collections.py --data data/topic-collections.json --root .

  # solo validar, sin escribir nada
  python scripts/build-topic-collections.py --data data/topic-collections.json --root . --check
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

SITE = "https://davidportodiaz.com"
INDEX_URL = f"{SITE}/cuaderno/temas/"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INTERNAL_URL_RE = re.compile(r"^/[a-z0-9\-/]+/$")
ALLOWED_STATUS = {"draft", "ready"}
ALLOWED_MODE = {"collection", "series"}
ALLOWED_ITEM_TYPE = {"articulo", "proceso", "recomendacion", "recurso"}

SHARE_IMAGE = f"{SITE}/assets/david-porto-imagen-compartir.webp"
SHARE_IMAGE_WIDTH = 1731
SHARE_IMAGE_HEIGHT = 909


class ValidationError(Exception):
    pass


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def validate_item(item: dict, coll_slug: str, index: int, seen_urls: set[str]) -> None:
    for key in ("url", "title", "description", "type"):
        if not isinstance(item.get(key), str) or not item[key].strip():
            raise ValidationError(f"{coll_slug}.items[{index}]: falta {key}")
    url = item["url"]
    if not INTERNAL_URL_RE.fullmatch(url):
        raise ValidationError(f"{coll_slug}.items[{index}]: URL debe ser interna y limpia (sin dominio, query ni hash): {url!r}")
    if "://" in url:
        raise ValidationError(f"{coll_slug}.items[{index}]: URL externa no permitida: {url!r}")
    if url in seen_urls:
        raise ValidationError(f"{coll_slug}.items[{index}]: URL duplicada dentro de la colección: {url!r}")
    seen_urls.add(url)
    if item["type"] not in ALLOWED_ITEM_TYPE:
        raise ValidationError(f"{coll_slug}.items[{index}]: type desconocido {item['type']!r}")


def validate(data: dict) -> list[dict]:
    if data.get("schema_version") != 1:
        raise ValidationError("schema_version debe ser 1")
    collections = data.get("collections")
    if not isinstance(collections, list) or not collections:
        raise ValidationError("collections debe ser una lista no vacía")

    seen_slugs: set[str] = set()
    for coll in collections:
        for key in ("slug", "status", "mode", "title", "description", "intro", "updated"):
            if not isinstance(coll.get(key), str) or not coll[key].strip():
                raise ValidationError(f"colección {coll.get('slug', '?')}: falta {key}")
        slug = coll["slug"]
        if not SLUG_RE.fullmatch(slug):
            raise ValidationError(f"slug inválido: {slug!r}")
        if slug in seen_slugs:
            raise ValidationError(f"slug duplicado: {slug}")
        seen_slugs.add(slug)
        if coll["status"] not in ALLOWED_STATUS:
            raise ValidationError(f"{slug}: status desconocido {coll['status']!r}")
        if coll["mode"] not in ALLOWED_MODE:
            raise ValidationError(f"{slug}: mode desconocido {coll['mode']!r}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", coll["updated"]):
            raise ValidationError(f"{slug}: updated debe ser AAAA-MM-DD")

        items = coll.get("items")
        if not isinstance(items, list) or not items:
            raise ValidationError(f"{slug}: items debe ser una lista no vacía")
        seen_urls: set[str] = set()
        for i, item in enumerate(items):
            validate_item(item, slug, i, seen_urls)

        if coll["status"] == "ready" and len(items) < 3:
            raise ValidationError(
                f"{slug}: status=ready exige al menos 3 piezas (gate editorial, doc 55 §5); tiene {len(items)}. "
                "Déjala en draft hasta que exista una tercera pieza real."
            )

    return collections


def check_repo(root: Path, ready_collections: list[dict]) -> None:
    """--root: confirma que cada pieza de cada colección ready es una página
    real, indexable, con el canonical esperado — el mismo contrato que ya usa
    scripts/build-surprise-content.py, para que una colección no siga
    ofreciendo un artículo que pasó a noindex o se movió."""
    problems: list[str] = []
    for coll in ready_collections:
        for item in coll["items"]:
            rel = item["url"].strip("/")
            path = root / rel / "index.html"
            if not path.exists():
                problems.append(f"{coll['slug']}: página ausente {item['url']}")
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', text, re.I):
                problems.append(f"{coll['slug']}: {item['url']} está en noindex")
            expected = SITE + item["url"]
            if expected not in text:
                problems.append(f"{coll['slug']}: canonical no confirmado en {item['url']}")
    if problems:
        raise ValidationError("; ".join(problems))


def head(title: str, description: str, canonical: str, jsonld: dict) -> str:
    schema = json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; connect-src \'none\'; '
        "img-src 'self'; style-src 'self'; font-src 'self'; script-src 'self'; object-src 'none'; "
        "base-uri 'self'; form-action 'none'; frame-src 'none'\">"
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        f"<title>{esc(title)}</title>"
        f'<meta name="description" content="{esc(description)}">'
        f'<meta property="og:title" content="{esc(title)}">'
        f'<meta property="og:description" content="{esc(description)}">'
        '<meta property="og:type" content="website">'
        f'<meta property="og:url" content="{esc(canonical)}">'
        f'<meta property="og:image" content="{SHARE_IMAGE}">'
        f'<meta property="og:image:width" content="{SHARE_IMAGE_WIDTH}">'
        f'<meta property="og:image:height" content="{SHARE_IMAGE_HEIGHT}">'
        f'<meta property="og:image:alt" content="{esc(title)}">'
        '<meta property="og:locale" content="es_ES">'
        '<meta property="og:site_name" content="David Porto Díaz">'
        '<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{esc(title)}">'
        f'<meta name="twitter:description" content="{esc(description)}">'
        f'<meta name="twitter:image" content="{SHARE_IMAGE}">'
        f'<meta name="twitter:image:alt" content="{esc(title)}">'
        f'<link rel="canonical" href="{esc(canonical)}">'
        '<meta name="robots" content="index,follow,max-image-preview:large">'
        '<link rel="stylesheet" href="/styles.css?v=202609-launch-1">'
        '<link rel="stylesheet" href="/assets/topic-collection.css">'
        f'<script type="application/ld+json">{schema}</script></head><body>'
    )


def breadcrumb_jsonld(items: list[tuple[str, str | None]]) -> dict:
    elements = []
    for i, (name, url) in enumerate(items, 1):
        entry = {"@type": "ListItem", "position": i, "name": name}
        if url:
            entry["item"] = url
        elements.append(entry)
    return {"@type": "BreadcrumbList", "itemListElement": elements}


def render_breadcrumb(items: list[tuple[str, str | None]]) -> str:
    parts = [f'<a href="{esc(url)}">{esc(name)}</a>' if url else f"<span>{esc(name)}</span>" for name, url in items]
    return '<nav class="breadcrumb" aria-label="Ruta de navegación">' + "<span aria-hidden=\"true\">›</span>".join(parts) + "</nav>"


def render_index(ready: list[dict]) -> str:
    title = "Colecciones del Cuaderno | David Porto Díaz"
    description = "Hubs temáticos que agrupan varios artículos del Cuaderno alrededor de una misma pregunta o proceso, con una introducción que explica por qué encajan juntos."
    cards = "".join(
        f'<article class="topic-card"><h2><a href="{esc(SITE + "/cuaderno/temas/" + c["slug"] + "/")}">{esc(c["title"])}</a></h2>'
        f'<p>{esc(c["description"])}</p>'
        f'<p class="topic-card__meta">{"Colección" if c["mode"] == "collection" else "Serie"} · {len(c["items"])} piezas</p></article>'
        for c in ready
    )
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": INDEX_URL + "#page",
                "url": INDEX_URL,
                "name": title,
                "description": description,
                "inLanguage": "es",
                "isPartOf": {"@id": f"{SITE}/#website"},
                "author": {"@id": f"{SITE}/#author"},
                "breadcrumb": {"@id": INDEX_URL + "#breadcrumb"},
            },
            {**breadcrumb_jsonld([("Inicio", SITE + "/"), ("Cuaderno", SITE + "/cuaderno/"), ("Temas", None)]), "@id": INDEX_URL + "#breadcrumb"},
        ],
    }
    main = (
        '<a href="#main-content" class="skip-link">Saltar al contenido</a>'
        '<main id="main-content" tabindex="-1" class="topic-page">'
        + render_breadcrumb([("Inicio", "/"), ("Cuaderno", "/cuaderno/"), ("Temas", None)])
        + '<header class="topic-hero"><p class="eyebrow">Cuaderno del autor</p>'
        f"<h1>Colecciones del Cuaderno</h1><p class=\"lead\">{esc(description)}</p></header>"
        f'<section class="topic-grid" aria-label="Colecciones publicadas">{cards}</section>'
        '<p class="topic-back"><a href="/cuaderno/">← Volver al Cuaderno</a></p>'
        "</main>"
    )
    return head(title, description, INDEX_URL, jsonld) + main + "</body></html>\n"


def render_hub(coll: dict) -> str:
    canonical = f"{SITE}/cuaderno/temas/{coll['slug']}/"
    title = f"{coll['title']} | Cuaderno | David Porto Díaz"
    is_series = coll["mode"] == "series"
    items_html = []
    for i, item in enumerate(coll["items"], 1):
        number = f'<span class="topic-item__number" aria-hidden="true">{i}</span>' if is_series else ""
        items_html.append(
            f'<li class="topic-item">{number}<h2><a href="{esc(item["url"])}">{esc(item["title"])}</a></h2>'
            f'<p>{esc(item["description"])}</p></li>'
        )
    list_tag = "ol" if is_series else "ul"
    jsonld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": canonical + "#page",
                "url": canonical,
                "name": coll["title"],
                "description": coll["description"],
                "dateModified": coll["updated"],
                "inLanguage": "es",
                "isPartOf": {"@id": f"{SITE}/#website"},
                "author": {"@id": f"{SITE}/#author"},
                "breadcrumb": {"@id": canonical + "#breadcrumb"},
                "mainEntity": {"@id": canonical + "#list"},
            },
            {
                "@type": "ItemList",
                "@id": canonical + "#list",
                "itemListOrder": "https://schema.org/ItemListOrderAscending" if is_series else "https://schema.org/ItemListUnordered",
                "itemListElement": [
                    {"@type": "ListItem", "position": i, "url": SITE + item["url"], "name": item["title"]}
                    for i, item in enumerate(coll["items"], 1)
                ],
            },
            {**breadcrumb_jsonld([("Inicio", SITE + "/"), ("Cuaderno", SITE + "/cuaderno/"), ("Temas", SITE + "/cuaderno/temas/"), (coll["title"], None)]), "@id": canonical + "#breadcrumb"},
        ],
    }
    series_note = (
        '<p class="topic-hero__note">Esta serie tiene un orden de lectura recomendado: cada entrega da por hecha la anterior.</p>'
        if is_series
        else ""
    )
    main = (
        '<a href="#main-content" class="skip-link">Saltar al contenido</a>'
        '<main id="main-content" tabindex="-1" class="topic-page">'
        + render_breadcrumb([("Inicio", "/"), ("Cuaderno", "/cuaderno/"), ("Temas", "/cuaderno/temas/"), (coll["title"], None)])
        + f'<header class="topic-hero"><p class="eyebrow">{"Serie del Cuaderno" if is_series else "Colección del Cuaderno"}</p>'
        f"<h1>{esc(coll['title'])}</h1><p class=\"lead\">{esc(coll['intro'])}</p>{series_note}</header>"
        f'<{list_tag} class="topic-list">{"".join(items_html)}</{list_tag}>'
        f'<p class="topic-updated">Revisión de esta colección: <time datetime="{esc(coll["updated"])}">{esc(coll["updated"])}</time></p>'
        '<p class="topic-back"><a href="/cuaderno/temas/">← Todas las colecciones</a> · <a href="/cuaderno/">Volver al Cuaderno</a></p>'
        "</main>"
    )
    return head(title, coll["description"], canonical, jsonld) + main + "</body></html>\n"


def build(data_path: Path, root: Path, check_only: bool) -> tuple[int, int]:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    collections = validate(data)
    ready = [c for c in collections if c["status"] == "ready"]
    check_repo(root, ready)

    index_target = root / "cuaderno" / "temas" / "index.html"
    index_html = render_index(ready)
    hub_html = {c["slug"]: render_hub(c) for c in ready}

    if check_only:
        drift = []
        if not index_target.exists() or index_target.read_text(encoding="utf-8") != index_html:
            drift.append("cuaderno/temas/index.html")
        for slug, html_out in hub_html.items():
            p = root / "cuaderno" / "temas" / slug / "index.html"
            if not p.exists() or p.read_text(encoding="utf-8") != html_out:
                drift.append(f"cuaderno/temas/{slug}/index.html")
        if drift:
            print("FAIL: salida desactualizada: " + ", ".join(drift))
            return len(collections), -1
        print(f"PASS: {len(collections)} colección(es), {len(ready)} publicada(s), salida al día")
        return len(collections), len(ready)

    index_target.parent.mkdir(parents=True, exist_ok=True)
    index_target.write_text(index_html, encoding="utf-8")
    for slug, html_out in hub_html.items():
        p = root / "cuaderno" / "temas" / slug / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html_out, encoding="utf-8")
    print(f"GENERATED: {len(collections)} colección(es) validadas, {len(ready)} hub(s) publicado(s)")
    return len(collections), len(ready)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--root", type=Path, required=True, help="raíz del repo (para generar/verificar y para --root de check_repo)")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        _, ready_count = build(args.data, args.root, args.check)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 1 if (args.check and ready_count == -1) else 0


if __name__ == "__main__":
    raise SystemExit(main())
