#!/usr/bin/env python3
'''Hubs de colecciones temáticas del Cuaderno.

Genera `/cuaderno/temas/` y `/cuaderno/temas/{slug}/` para las colecciones
con status "ready". Los artículos conservan sus URLs; esta capa solo crea
índices editoriales que explican por qué las piezas forman un conjunto.

Uso:
  python scripts/build-topic-collections.py --data data/topic-collections.json --root .
  python scripts/build-topic-collections.py --data data/topic-collections.json --root . --check
'''
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from site_shell import inject_shell_auto  # noqa: E402

SITE = "https://davidportodiaz.com"
INDEX_URL = f"{SITE}/cuaderno/temas/"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
INTERNAL_URL_RE = re.compile(r"^/[a-z0-9\-/]+/$")
ALLOWED_STATUS = {"draft", "ready"}
ALLOWED_MODE = {"collection", "series"}
ALLOWED_ITEM_TYPE = {"articulo", "proceso", "recomendacion", "recurso"}

SHARE_IMAGE = f"{SITE}/assets/david-porto-imagen-compartir.jpg"
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
        raise ValidationError(
            f"{coll_slug}.items[{index}]: URL debe ser interna y limpia "
            f"(sin dominio, query ni hash): {url!r}"
        )
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
                f"{slug}: status=ready exige al menos 3 piezas; tiene {len(items)}. "
                "Déjala en draft hasta que exista una tercera pieza real."
            )

    return collections


def check_repo(root: Path, ready_collections: list[dict]) -> None:
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


SHELL_HEADER = '''  <a href="#contenido" class="skip-link">Saltar al contenido</a>

  <header class="site-header" data-header>
    <div class="site-header__inner">
      <a class="brand" href="/" aria-label="David Porto Díaz — inicio">
        <span class="brand__name">David Porto Díaz</span>
        <span class="brand__role">Escritor</span>
      </a>
      <nav class="primary-nav" aria-label="Navegación principal">
        <a href="/libros/">Obra</a>
        <a href="/cuaderno/" aria-current="page">Cuaderno</a>
        <a href="/herramientas/">Herramientas</a>
      </nav>
      <button class="explore-trigger" type="button" aria-haspopup="dialog" aria-controls="explore-dialog" aria-expanded="false" data-explore-open>
        Explorar
      </button>
    </div>
  </header>

  <dialog class="explore-dialog" id="explore-dialog" aria-labelledby="explore-title" data-explore-dialog>
    <div class="explore-dialog__shell">
      <div class="explore-dialog__head">
        <div>
          <p class="eyebrow">Índice general</p>
          <h2 id="explore-title">Explorar</h2>
        </div>
        <button class="icon-button" type="button" aria-label="Cerrar Explorar" data-explore-close>
          <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20"><path d="M5 5l14 14M19 5L5 19"/></svg>
        </button>
      </div>

      <div class="explore-dialog__grid">
        <nav class="explore-list" aria-label="Destinos de la web">
          <a class="explore-row" href="/las-manecillas-del-recuerdo/" data-preview="manecillas">
            <span class="explore-row__index">01</span>
            <span class="explore-row__body"><strong>Las manecillas del recuerdo</strong><small>La obra actual.</small></span>
          </a>
          <a class="explore-row" href="/autor.html" data-preview="autor">
            <span class="explore-row__index">02</span>
            <span class="explore-row__body"><strong>Autor</strong><small>Biografía, obra y trayectoria.</small></span>
          </a>
          <a class="explore-row" href="/libros/samuel-entre-mundos/" data-preview="samuel">
            <span class="explore-row__index">03</span>
            <span class="explore-row__body"><strong>Samuel entre mundos</strong><small>Primera novela publicada.</small></span>
          </a>
          <a class="explore-row" href="/cuaderno/" data-preview="cuaderno">
            <span class="explore-row__index">04</span>
            <span class="explore-row__body"><strong>Cuaderno</strong><small>Artículos y piezas editoriales.</small></span>
          </a>
          <a class="explore-row" href="/herramientas/" data-preview="herramientas">
            <span class="explore-row__index">05</span>
            <span class="explore-row__body"><strong>Herramientas</strong><small>Utilidades gratuitas para escritores.</small></span>
          </a>
          <a class="explore-row" href="/prensa.html" data-preview="prensa">
            <span class="explore-row__index">06</span>
            <span class="explore-row__body"><strong>Prensa y eventos</strong><small>Apariciones, materiales y agenda.</small></span>
          </a>
        </nav>

        <aside class="explore-preview" aria-live="polite" aria-atomic="true" data-explore-preview>
          <div class="explore-preview__media" aria-hidden="true" data-preview-media></div>
          <p class="explore-preview__label" data-preview-label>Cuaderno</p>
          <p class="explore-preview__copy" data-preview-copy>Artículos, crónicas y piezas editoriales.</p>
        </aside>
      </div>
    </div>
  </dialog>
'''

SHELL_FOOTER = '''  <footer class="site-footer">
    <div class="site-footer__grid">
      <div>
        <strong class="brand__name">David Porto Díaz</strong>
        <p>Autor de Las manecillas del recuerdo y Samuel entre mundos.</p>
        <div class="social-row">
        <a class="social-icon" href="https://www.instagram.com/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="Instagram" title="Instagram"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="3.8"/><circle cx="17.3" cy="6.7" r="0.6" fill="currentColor" stroke="none"/></svg></a>
        <a class="social-icon" href="https://www.facebook.com/profile.php?id=61590793667301" target="_blank" rel="noopener noreferrer me" aria-label="Facebook" title="Facebook"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M16.7 3H7.3A4.3 4.3 0 0 0 3 7.3v9.4A4.3 4.3 0 0 0 7.3 21h4.2v-6.6H9.4v-2.6h2.1V9.8c0-2.1 1.3-3.3 3.2-3.3.9 0 1.7.1 1.9.1v2.2h-1.3c-1 0-1.2.5-1.2 1.2v1.7h2.4l-.3 2.6h-2.1V21h2.6a4.3 4.3 0 0 0 4.3-4.3V7.3A4.3 4.3 0 0 0 16.7 3z"/></svg></a>
        <a class="social-icon" href="https://www.tiktok.com/@davidportoescritor" target="_blank" rel="noopener noreferrer me" aria-label="TikTok" title="TikTok"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M14 3c.4 2.2 2 3.8 4.2 4.1v2.7c-1.5 0-2.9-.4-4.1-1.2v6.1a4.9 4.9 0 1 1-4.2-4.9v2.7a2.2 2.2 0 1 0 1.6 2.1V3h2.5z"/></svg></a>
        <a class="social-icon" href="https://www.threads.net/@davidportodiaz" target="_blank" rel="noopener noreferrer me" aria-label="Threads" title="Threads"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true" focusable="false"><path d="M12 21c4.4 0 7-2.8 7-7.5C19 8 16.5 4 12 4 8 4 5.5 6.8 5.5 11c0 3 1.8 4.8 4.3 4.8 2 0 3.4-1.2 3.4-3 0-1.4-.9-2.3-2.1-2.3-.9 0-1.5.5-1.7 1.2"/></svg></a>
        <a class="social-icon" href="https://bsky.app/profile/davidportoescritor.bsky.social" target="_blank" rel="noopener noreferrer me" aria-label="Bluesky" title="Bluesky"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M12 7c-1.6-2.3-4.6-3.6-6.7-3.2-.3 2.3.4 5.4 2 7.1-1.6.1-2.8.8-3 1.7.7.9 2.3 1.3 3.8 1-.9 1.1-1.1 2.6-.5 3.8 1.6.1 3.7-1.1 4.6-2.8.4 1 .9 1.9 1.5 2.6.6-.7 1.1-1.6 1.5-2.6.9 1.7 3 2.9 4.6 2.8.6-1.2.4-2.7-.5-3.8 1.5.3 3.1-.1 3.8-1-.2-.9-1.4-1.6-3-1.7 1.6-1.7 2.3-4.8 2-7.1-2.1-.4-5.1.9-6.7 3.2-.2.3-.4.6-.5 1-.1-.4-.3-.7-.5-1z"/></svg></a>
        <a class="social-icon" href="https://www.pinterest.com/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="Pinterest" title="Pinterest"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M12 2C6.5 2 3 5.6 3 10c0 3.2 1.8 5.1 3 5.7.2.1.4 0 .4-.3l.4-1.5c0-.2 0-.3-.1-.5-.4-.5-.7-1.4-.7-2.3 0-3 2.2-5.7 5.8-5.7 3.1 0 4.9 1.9 4.9 4.5 0 3.4-1.5 5.6-3.5 5.6-1.1 0-2-.9-1.7-2.1.3-1.3.9-2.7.9-3.7 0-.8-.5-1.5-1.4-1.5-1.1 0-2 1.2-2 2.7 0 1 .3 1.7.3 1.7s-1.2 4.9-1.4 5.8c-.4 1.6-.1 3.6 0 3.8.1.1.2.1.3 0 .1-.2 1.5-1.9 2-3.5.1-.4.6-2.3.6-2.3.3.6 1.2 1.1 2.2 1.1 2.9 0 5-2.7 5-6.4C20 5.7 16.5 2 12 2z"/></svg></a>
        <a class="social-icon" href="https://www.linkedin.com/in/davidportodiaz/" target="_blank" rel="noopener noreferrer me" aria-label="LinkedIn" title="LinkedIn"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><path d="M5 3a2 2 0 1 0 0 4 2 2 0 0 0 0-4zM3.5 9h3v12h-3V9zm6.5 0h2.9v1.6c.5-.9 1.7-1.9 3.4-1.9 3.6 0 4.6 2.3 4.6 5.4V21h-3v-6.1c0-1.5-.5-2.5-1.9-2.5-1.4 0-2 1-2 2.4V21h-3V9z"/></svg></a>
        <a class="text-action" href="https://www.goodreads.com/author/show/66843136.David_Porto_D_az" target="_blank" rel="noopener noreferrer">Goodreads</a>
        </div>
      </div>
      <nav aria-label="Obra"><h2>Obra</h2><a href="/las-manecillas-del-recuerdo/">Las manecillas del recuerdo</a><a href="/libros/samuel-entre-mundos/">Samuel entre mundos</a><a href="/fragmento/">Fragmento gratis</a></nav>
      <nav aria-label="Leer y recursos"><h2>Leer</h2><a href="/cuaderno/">Cuaderno</a><a href="/herramientas/">Herramientas</a><a href="/mapa-del-sitio/">Mapa del sitio</a></nav>
      <nav aria-label="Información"><h2>Información</h2><a href="/autor.html">Autor</a><a href="/prensa.html">Prensa</a><a href="/eventos.html">Eventos</a><a href="/privacidad.html">Privacidad</a><a href="/aviso-legal.html">Aviso legal</a><a href="/ai/">Para IA</a></nav>
    </div>
  </footer>

  <script defer src="/assets/v1-shell.js"></script>
</body>
</html>
'''


def head(title: str, description: str, canonical: str, jsonld: dict) -> str:
    schema = json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))
    return (
        '<!doctype html><html lang="es" class="v1"><head><meta charset="utf-8">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; connect-src \'none\'; '
        "img-src 'self'; style-src 'self'; font-src 'self'; script-src 'self'; object-src 'none'; "
        "base-uri 'self'; form-action 'none'; frame-src 'none'\">"
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<meta name="robots" content="index,follow,max-image-preview:large">'
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
        '<meta name="theme-color" content="#ffffff">'
        f'<link rel="canonical" href="{esc(canonical)}">'
        '<link rel="icon" type="image/png" href="/assets/david-porto-favicon.png">'
        '<link rel="apple-touch-icon" href="/assets/david-porto-favicon.png">'
        '<link rel="manifest" href="/manifest.json">'
        '<link rel="stylesheet" href="/assets/v1-fonts.css">'
        '<link rel="stylesheet" href="/assets/v1-tokens.css">'
        '<link rel="stylesheet" href="/assets/v1-base.css">'
        '<!-- v1-shell-preload:start (generated by scripts/add_v1_shell_preloads.py -- do not edit by hand) -->'
        '<link rel="preload" as="style" href="/assets/v1-shell-base.css">'
        '<link rel="preload" as="style" href="/assets/v1-shell-lrb-v2.css">'
        '<link rel="preload" as="style" href="/assets/v1-lrb-material-v2.css">'
        '<link rel="preload" as="style" href="/assets/v1-home-editorial-v3.css">'
        '<link rel="preload" as="style" href="/assets/v1-editorial-interior-v4.css">'
        '<link rel="preload" as="style" href="/assets/v1-editorial-placeholders-v4.css">'
        '<link rel="preload" as="style" href="/assets/v1-editorial-interactions-v4.css">'
        '<link rel="preload" as="style" href="/assets/v1-banner-art-direction-v5.css">'
        '<link rel="preload" as="style" href="/assets/v1-site-cohesion-v6.css">'
        '<link rel="preload" as="style" href="/assets/v1-reflow-hardening-v7.css">'
        '<!-- v1-shell-preload:end -->'
        '<link rel="stylesheet" href="/assets/v1-shell.css">'
        '<link rel="stylesheet" href="/assets/v1-components.css">'
        '<link rel="stylesheet" href="/assets/v1-families.css">'
        '<link rel="stylesheet" href="/assets/v1-cuaderno-topics.css">'
        '<link rel="stylesheet" href="/assets/cuaderno-index.css">'
        f'<script type="application/ld+json">{schema}</script></head><body>'
        + SHELL_HEADER
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
    parts = [
        f'<li><a href="{esc(url)}">{esc(name)}</a></li>'
        if url
        else f'<li aria-current="page">{esc(name)}</li>'
        for name, url in items
    ]
    return (
        '<nav class="cuaderno-topics-breadcrumb" aria-label="Ruta de navegación"><ol>'
        + "".join(parts)
        + "</ol></nav>"
    )


def hero(eyebrow: str, title: str, lead: str, count: int, count_label: str) -> str:
    return (
        '<header class="cuaderno-topics-hero">'
        '<div class="cuaderno-topics-hero__copy">'
        f'<p class="eyebrow">{esc(eyebrow)}</p>'
        f"<h1>{esc(title)}</h1>"
        f'<p class="cuaderno-topics-hero__lead">{esc(lead)}</p>'
        "</div>"
        f'<aside class="cuaderno-topics-hero__folio" aria-label="{esc(count_label)}">'
        f"<strong>{count:02d}</strong><span>{esc(count_label)}</span></aside>"
        "</header>"
    )


def render_index(ready: list[dict]) -> str:
    title = "Colecciones del Cuaderno | David Porto Díaz"
    description = (
        "Hubs temáticos que agrupan varios artículos del Cuaderno alrededor de una misma pregunta "
        "o proceso, con una introducción que explica por qué encajan juntos."
    )
    rows = "".join(
        (
            '<li class="cuaderno-topics-entry">'
            f'<span class="cuaderno-topics-entry__index" aria-hidden="true">{i:02d}</span>'
            '<div class="cuaderno-topics-entry__body">'
            f'<p class="cuaderno-topics-entry__meta">{"Colección" if c["mode"] == "collection" else "Serie"} · {len(c["items"])} piezas</p>'
            f'<h2><a href="{esc(SITE + "/cuaderno/temas/" + c["slug"] + "/")}">{esc(c["title"])}</a></h2>'
            f'<p>{esc(c["description"])}</p>'
            "</div></li>"
        )
        for i, c in enumerate(ready, 1)
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
            {
                **breadcrumb_jsonld(
                    [("Inicio", SITE + "/"), ("Cuaderno", SITE + "/cuaderno/"), ("Temas", None)]
                ),
                "@id": INDEX_URL + "#breadcrumb",
            },
        ],
    }
    count_label = "colección publicada" if len(ready) == 1 else "colecciones publicadas"
    main = (
        '<main id="contenido" tabindex="-1" class="v1-main" data-family="cuaderno-topics">'
        + render_breadcrumb([("Inicio", "/"), ("Cuaderno", "/cuaderno/"), ("Temas", None)])
        + hero("Cuaderno del autor", "Colecciones del Cuaderno", description, len(ready), count_label)
        + f'<section class="cuaderno-topics-index" aria-label="Colecciones publicadas"><ol class="cuaderno-topics-ledger">{rows}</ol></section>'
        + '<section class="cuaderno-topics-tail"><p><a class="cuaderno-topics-link" href="/cuaderno/">← Volver al Cuaderno</a></p></section>'
        + "</main>"
    )
    return head(title, description, INDEX_URL, jsonld) + main + SHELL_FOOTER


def render_hub(coll: dict) -> str:
    canonical = f"{SITE}/cuaderno/temas/{coll['slug']}/"
    title = f"{coll['title']} | Cuaderno | David Porto Díaz"
    is_series = coll["mode"] == "series"
    total = len(coll["items"])

    items_html = []
    for i, item in enumerate(coll["items"], 1):
        items_html.append(
            '<li class="cuaderno-topic-step">'
            f'<span class="cuaderno-topic-step__index" aria-hidden="true">{i:02d}</span>'
            '<div class="cuaderno-topic-step__body">'
            f'<h2><a href="{esc(item["url"])}">{esc(item["title"])}</a></h2>'
            f'<p>{esc(item["description"])}</p>'
            "</div></li>"
        )

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
                "itemListOrder": (
                    "https://schema.org/ItemListOrderAscending"
                    if is_series
                    else "https://schema.org/ItemListUnordered"
                ),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i,
                        "url": SITE + item["url"],
                        "name": item["title"],
                    }
                    for i, item in enumerate(coll["items"], 1)
                ],
            },
            {
                **breadcrumb_jsonld(
                    [
                        ("Inicio", SITE + "/"),
                        ("Cuaderno", SITE + "/cuaderno/"),
                        ("Temas", SITE + "/cuaderno/temas/"),
                        (coll["title"], None),
                    ]
                ),
                "@id": canonical + "#breadcrumb",
            },
        ],
    }

    series_note = (
        '<p class="cuaderno-topic-note">Esta serie tiene un orden de lectura recomendado: cada entrega da por hecha la anterior.</p>'
        if is_series
        else ""
    )
    main = (
        '<main id="contenido" tabindex="-1" class="v1-main" data-family="cuaderno-topics">'
        + render_breadcrumb(
            [
                ("Inicio", "/"),
                ("Cuaderno", "/cuaderno/"),
                ("Temas", "/cuaderno/temas/"),
                (coll["title"], None),
            ]
        )
        + hero(
            "Serie del Cuaderno" if is_series else "Colección del Cuaderno",
            coll["title"],
            coll["intro"],
            total,
            "piezas en la colección",
        )
        + series_note
        # <ol> cuando es serie, <ul> cuando no. El JSON-LD ya distingue
        # ItemListOrderedAscending de ItemListUnordered mas arriba, y la pagina
        # dice por escrito que la serie tiene un orden de lectura recomendado:
        # el marcado tiene que decir lo mismo. Un lector de pantalla anuncia
        # "lista de 4 elementos" en un <ul> y "lista ordenada" en un <ol>, que
        # es justo la diferencia que importa aqui.
        + f'<section class="cuaderno-topic-itinerary" aria-label="Piezas de la colección"><{"ol" if is_series else "ul"} class="cuaderno-topic-steps">{"".join(items_html)}</{"ol" if is_series else "ul"}></section>'
        + f'<section class="cuaderno-topics-tail"><p class="cuaderno-topic-revision">Revisión de esta colección: <time datetime="{esc(coll["updated"])}">{esc(coll["updated"])}</time></p>'
        + '<nav class="cuaderno-topics-tail__links" aria-label="Continuar en el Cuaderno"><a class="cuaderno-topics-link" href="/cuaderno/temas/">← Todas las colecciones</a><span aria-hidden="true">·</span><a class="cuaderno-topics-link" href="/cuaderno/">Volver al Cuaderno</a></nav></section>'
        + "</main>"
    )
    return head(title, coll["description"], canonical, jsonld) + main + SHELL_FOOTER


def build(data_path: Path, root: Path, check_only: bool) -> tuple[int, int]:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    collections = validate(data)
    ready = [c for c in collections if c["status"] == "ready"]
    check_repo(root, ready)

    index_target = root / "cuaderno" / "temas" / "index.html"
    # El shell lo genera scripts/build-site-shell.py desde data/navigation.json.
    # La plantilla de este fichero ya no lo escribe: ver scripts/site_shell.py.
    index_html = inject_shell_auto(render_index(ready))
    hub_html = {c["slug"]: inject_shell_auto(render_hub(c)) for c in ready}

    if check_only:
        drift = []
        if not index_target.exists() or index_target.read_text(encoding="utf-8") != index_html:
            drift.append("cuaderno/temas/index.html")
        for slug, html_out in hub_html.items():
            path = root / "cuaderno" / "temas" / slug / "index.html"
            if not path.exists() or path.read_text(encoding="utf-8") != html_out:
                drift.append(f"cuaderno/temas/{slug}/index.html")
        if drift:
            print("FAIL: salida desactualizada: " + ", ".join(drift))
            return len(collections), -1
        print(f"PASS: {len(collections)} colección(es), {len(ready)} publicada(s), salida al día")
        return len(collections), len(ready)

    index_target.parent.mkdir(parents=True, exist_ok=True)
    index_target.write_text(index_html, encoding="utf-8")
    for slug, html_out in hub_html.items():
        path = root / "cuaderno" / "temas" / slug / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html_out, encoding="utf-8")
    print(f"GENERATED: {len(collections)} colección(es) validadas, {len(ready)} hub(s) publicado(s)")
    return len(collections), len(ready)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        _, ready_count = build(args.data, args.root, args.check)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 1 if (args.check and ready_count == -1) else 0


if __name__ == "__main__":
    raise SystemExit(main())
