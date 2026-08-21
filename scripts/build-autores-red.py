#!/usr/bin/env python3
"""Genera /autores/ y perfiles estáticos desde un JSON revisado manualmente.

Uso:
  python scripts/build-autores-red.py --data content/autores-red.json --root .
  python scripts/build-autores-red.py --data content/autores-red.json --root . --check

No publica registros draft. No obtiene contenido de terceros.
"""
from __future__ import annotations
import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BASE_URL = "https://davidportodiaz.com"

def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)

def valid_https(url: str) -> bool:
    if not url:
        return True
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and bool(parsed.netloc)
    except Exception:
        return False

def load_data(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("authors"), list):
        raise ValueError("authors debe ser una lista")
    seen = set()
    for a in data["authors"]:
        slug = a.get("slug", "")
        if not SLUG_RE.fullmatch(slug):
            raise ValueError(f"slug inválido: {slug!r}")
        if slug in seen:
            raise ValueError(f"slug duplicado: {slug}")
        seen.add(slug)
        if a.get("status") not in {"draft", "published"}:
            raise ValueError(f"{slug}: status debe ser draft o published")
        if not a.get("name") or not a.get("description"):
            raise ValueError(f"{slug}: faltan name/description")
        answers = a.get("answers") or []
        if a.get("status") == "published" and len(answers) < 4:
            raise ValueError(f"{slug}: un perfil publicado necesita al menos 4 respuestas originales")
        for item in answers:
            if len((item.get("answer") or "").strip()) < 40:
                raise ValueError(f"{slug}: respuesta demasiado corta")
        for url in [a.get("website",""), a.get("image",""), *(a.get("same_as") or [])]:
            if url and not valid_https(url):
                raise ValueError(f"{slug}: URL debe ser https: {url}")
        for b in a.get("books") or []:
            if b.get("url") and not valid_https(b["url"]):
                raise ValueError(f"{slug}: URL de libro debe ser https")
    return data

def layout(title: str, description: str, body: str, canonical: str, jsonld: dict | None = None) -> str:
    ld = ""
    if jsonld:
        ld = '<script type="application/ld+json">\n' + json.dumps(jsonld, ensure_ascii=False, indent=2) + "\n</script>"
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<link rel="stylesheet" href="/styles.css?v=202609-launch-1">
<link rel="stylesheet" href="/assets/autores-red.css?v=20260817-1">
{ld}
</head>
<body>
<a class="skip-link" href="#contenido">Saltar al contenido</a>
<div class="site-shell">
<header class="site-header">
<a class="brand" href="/">David Porto Díaz</a>
<nav class="site-nav" aria-label="Navegación principal">
<a href="/libros/">Libros</a>
<a href="/cuaderno/">Cuaderno</a>
<a href="/autores/" aria-current="page">Autores</a>
<a href="/autor.html">Autor</a>
</nav>
</header>
<main id="contenido" tabindex="-1">
{body}
</main>
<footer class="autores-footer">
<p><a href="/">David Porto Díaz</a> · literatura, lectura y escritura.</p>
</footer>
</div>
</body>
</html>
"""

def author_jsonld(a: dict) -> dict:
    url = f"{BASE_URL}/autores/{a['slug']}/"
    person = {
        "@type": "Person",
        "@id": url + "#person",
        "name": a["name"],
        "description": a["description"],
        "url": url,
    }
    if a.get("image"):
        person["image"] = a["image"]
    if a.get("same_as"):
        person["sameAs"] = a["same_as"]
    if a.get("website"):
        person["sameAs"] = list(dict.fromkeys([*(person.get("sameAs") or []), a["website"]]))
    return {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "@id": url + "#profile",
        "url": url,
        "dateCreated": a.get("date_created"),
        "dateModified": a.get("date_modified"),
        "mainEntity": person,
    }

def render_author(a: dict) -> str:
    genres = " · ".join(esc(x) for x in (a.get("genres") or []))
    books = "".join(
        f'<li><a href="{esc(b.get("url"))}" rel="noopener noreferrer">{esc(b.get("title"))}</a></li>'
        if b.get("url") else f"<li>{esc(b.get('title'))}</li>"
        for b in (a.get("books") or [])
    )
    qas = "".join(
        f'<section class="autor-qa"><h2>{esc(x["question"])}</h2><p>{esc(x["answer"])}</p></section>'
        for x in a["answers"]
    )
    official = ""
    if a.get("website"):
        official = f'<p><a class="button secondary" href="{esc(a["website"])}" rel="noopener noreferrer">Web oficial</a></p>'
    return f"""
<article class="autor-profile">
<header class="autor-profile__hero">
<p class="eyebrow">Autores en primera persona</p>
<h1>{esc(a["name"])}</h1>
{f'<p class="autor-genres">{genres}</p>' if genres else ''}
<p class="autor-profile__intro">{esc(a["description"])}</p>
{official}
</header>
<div class="autor-profile__grid">
<div>{qas}</div>
<aside class="autor-profile__aside" aria-label="Ficha del autor">
<h2>Libros citados</h2>
<ul>{books or "<li>Sin libros añadidos todavía.</li>"}</ul>
<p class="autor-profile__note">Las respuestas de esta página han sido proporcionadas por el autor invitado y revisadas editorialmente antes de publicarse.</p>
</aside>
</div>
<p class="autor-back"><a href="/autores/">← Volver a todos los autores</a></p>
</article>
"""

def render_index(data: dict, authors: list[dict]) -> str:
    cards = "".join(
        f"""<article class="autor-card">
<p class="autor-card__genres">{esc(" · ".join(a.get("genres") or []))}</p>
<h2><a href="/autores/{esc(a["slug"])}/">{esc(a["name"])}</a></h2>
<p>{esc(a["description"])}</p>
<a class="text-link" href="/autores/{esc(a["slug"])}/">Leer conversación →</a>
</article>"""
        for a in authors
    )
    if not cards:
        cards = '<p class="autor-empty">La sección se publicará cuando exista un grupo inicial de autores revisados.</p>'
    items = [
        {"@type": "ListItem", "position": i+1, "url": f"{BASE_URL}/autores/{a['slug']}/", "name": a["name"]}
        for i, a in enumerate(authors)
    ]
    ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": f"{BASE_URL}/autores/#collection",
        "url": f"{BASE_URL}/autores/",
        "name": data.get("section_name", "Autores en primera persona"),
        "description": data.get("section_description", ""),
        "mainEntity": {"@type": "ItemList", "itemListElement": items},
    }
    body = f"""
<section class="autores-hero">
<p class="eyebrow">Comunidad editorial</p>
<h1>{esc(data.get("section_name", "Autores en primera persona"))}</h1>
<p>{esc(data.get("section_description", ""))}</p>
<p class="autores-policy">Perfiles gratuitos y revisados manualmente. No se exige ningún enlace de vuelta para aparecer.</p>
</section>
<section class="autores-grid" aria-label="Autores publicados">{cards}</section>
<section class="autores-join">
<h2>¿Escribes y quieres participar?</h2>
<p>La página debe incluir respuestas originales en primera persona. No se publican biografías copiadas ni fichas automáticas.</p>
<a class="button secondary" href="/#contacto">Proponer un perfil</a>
</section>
"""
    return layout(
        data.get("section_name", "Autores en primera persona") + " | David Porto Díaz",
        data.get("section_description", ""),
        body,
        f"{BASE_URL}/autores/",
        ld,
    )

def expected_outputs(data: dict) -> dict[Path, str]:
    published = sorted((a for a in data["authors"] if a["status"] == "published"), key=lambda a: a["name"].casefold())
    outputs = {Path("autores/index.html"): render_index(data, published)}
    for a in published:
        outputs[Path(f"autores/{a['slug']}/index.html")] = layout(
            f"{a['name']} — Autores en primera persona | David Porto Díaz",
            a["description"],
            render_author(a),
            f"{BASE_URL}/autores/{a['slug']}/",
            author_jsonld(a),
        )
    return outputs

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    data = load_data(Path(args.data))
    outputs = expected_outputs(data)

    if args.check:
        mismatches = []
        for rel, content in outputs.items():
            p = root / rel
            if not p.exists() or p.read_text(encoding="utf-8") != content:
                mismatches.append(str(rel))
        if mismatches:
            print("Desactualizados:", *mismatches, sep="\n- ")
            return 1
        print(f"OK: {len(outputs)} archivos de autores reproducibles")
        return 0

    for rel, content in outputs.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        print("write", rel)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
