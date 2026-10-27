#!/usr/bin/env python3
'''Atlas literario: hub, destinos, lugares y rutas.

Genera `/atlas-literario/` y `/atlas-literario/{slug}/` desde
`data/atlas-pages.json`. Cada hecho lleva una etiqueta que separa lo documentado
de la tradición, la atribución sin documentar y la ficción.

Uso:
  python scripts/build-atlas-pages.py --data data/atlas-pages.json --root .
  python scripts/build-atlas-pages.py --data data/atlas-pages.json --root . --check
'''
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from site_shell import inject_shell_auto  # noqa: E402

_spec = importlib.util.spec_from_file_location("build_topic_collections", HERE / "build-topic-collections.py")
_topics = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _topics
_spec.loader.exec_module(_topics)
esc = _topics.esc
SITE = _topics.SITE

ATLAS_URL = f"{SITE}/atlas-literario/"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KINDS = {
    "destination": ("Destinos", "Ciudades y barrios donde la literatura se puede recorrer.", "Destino"),
    "place": ("Lugares", "Bibliotecas y librerías concretas, con su historia verificada.", "Lugar"),
    "route": ("Rutas", "Recorridos con paradas, para planificar una visita.", "Ruta"),
}
LABELS = ("hecho", "tradicion", "atribucion", "ficcion")
CSS_OLD = '<link rel="stylesheet" href="/assets/v1-cuaderno-topics.css?v=1"><link rel="stylesheet" href="/assets/cuaderno-index.css?v=1">'
CSS_NEW = '<link rel="stylesheet" href="/assets/v1-atlas.css?v=1">'


class ValidationError(Exception):
    pass


def valid_https(url: object) -> bool:
    if not isinstance(url, str) or not url.startswith("https://"):
        return False
    parts = urlsplit(url)
    return bool(parts.hostname) and not parts.username and not parts.password and not any(
        ord(c) <= 32 or c in '<>\\"' for c in url
    )


def validate(data: dict) -> list[dict]:
    labels = data.get("labels")
    if not isinstance(labels, dict) or set(labels) != set(LABELS):
        raise ValidationError("labels debe definir " + ", ".join(LABELS))
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValidationError("entries vacío")
    for key in ("updated", "verified"):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(data.get(key, ""))):
            raise ValidationError(f"{key} debe ser AAAA-MM-DD")
    seen: set[str] = set()
    for e in entries:
        slug = e.get("slug", "")
        if not SLUG_RE.fullmatch(slug) or slug in seen:
            raise ValidationError(f"slug inválido o repetido: {slug!r}")
        seen.add(slug)
        if e.get("kind") not in KINDS:
            raise ValidationError(f"{slug}: kind inválido")
        for key in ("title", "description", "country", "lead"):
            if not isinstance(e.get(key), str) or not e[key].strip():
                raise ValidationError(f"{slug}: falta {key}")
        if len(e["description"]) < 60:
            raise ValidationError(f"{slug}: description demasiado corta")
        if not e.get("sections") or not e.get("facts"):
            raise ValidationError(f"{slug}: requiere sections y facts")
        for fact in e["facts"]:
            if fact.get("label") not in LABELS or not str(fact.get("text", "")).strip():
                raise ValidationError(f"{slug}: hecho sin etiqueta válida")
        sources = e.get("sources") or []
        if not sources or any(not valid_https(s.get("url")) or not s.get("label") for s in sources):
            raise ValidationError(f"{slug}: requiere fuentes HTTPS válidas")
        if e["kind"] == "route" and not e.get("route_stops"):
            raise ValidationError(f"{slug}: la ruta requiere route_stops")
    for e in entries:
        for rel in e.get("related", []):
            if rel not in seen or rel == e["slug"]:
                raise ValidationError(f"{e['slug']}: related desconocido {rel!r}")
    return entries


def jsonld(canonical: str, name: str, description: str, modified: str, crumbs: list, extra: list) -> dict:
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": canonical + "#page",
                "url": canonical,
                "name": name,
                "description": description,
                "dateModified": modified,
                "inLanguage": "es",
                "isPartOf": {"@id": f"{SITE}/#website"},
                "author": {"@id": f"{SITE}/#author"},
                "breadcrumb": {"@id": canonical + "#breadcrumb"},
            },
            *extra,
            {**_topics.breadcrumb_jsonld(crumbs), "@id": canonical + "#breadcrumb"},
        ],
    }


def breadcrumb_html(items: list[tuple[str, str | None]]) -> str:
    return _topics.render_breadcrumb(items).replace("cuaderno-topics-breadcrumb", "atlas-breadcrumb")


def hero(eyebrow: str, title: str, lead: str, count: int | None, count_label: str) -> str:
    folio = (
        f'<aside class="atlas-hero__folio" aria-label="{esc(count_label)}"><strong>{count:02d}</strong><span>{esc(count_label)}</span></aside>'
        if count is not None
        else ""
    )
    return (
        '<header class="atlas-hero"><div class="atlas-hero__copy">'
        f'<p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(title)}</h1>'
        f'<p class="atlas-hero__lead">{esc(lead)}</p></div>{folio}</header>'
    )


def wrap(title: str, description: str, canonical: str, schema: dict, main: str) -> str:
    page = _topics.head(title, description, canonical, schema)
    if CSS_OLD not in page:
        raise ValidationError("head de las colecciones cambió: revisa CSS_OLD")
    return page.replace(CSS_OLD, CSS_NEW) + main + _topics.SHELL_FOOTER


def render_hub(data: dict, entries: list[dict]) -> str:
    title = "Atlas literario | David Porto Díaz"
    description = (
        "Bibliotecas, librerías, ciudades y rutas para lectores, con una regla: separar lo documentado "
        "de la tradición, la atribución sin documentar y la ficción."
    )
    groups = []
    n = 0
    for kind, (name, blurb, _label) in KINDS.items():
        items = [e for e in entries if e["kind"] == kind]
        if not items:
            continue
        rows = []
        for e in items:
            n += 1
            rows.append(
                '<li class="atlas-entry">'
                f'<span class="atlas-entry__index" aria-hidden="true">{n:02d}</span>'
                '<div class="atlas-entry__body">'
                f'<p class="atlas-entry__meta">{esc(KINDS[kind][2])} · {esc(e["country"])}</p>'
                f'<h3><a href="/atlas-literario/{e["slug"]}/">{esc(e["title"])}</a></h3>'
                f'<p>{esc(e["description"])}</p></div></li>'
            )
        groups.append(
            f'<section class="atlas-group" aria-labelledby="atlas-{kind}"><h2 id="atlas-{kind}">{esc(name)}</h2>'
            f'<p>{esc(blurb)}</p><ul class="atlas-list">{"".join(rows)}</ul></section>'
        )
    legend = " · ".join(f'<strong>{esc(data["labels"][k])}</strong>' for k in LABELS)
    rule = (
        '<p class="atlas-rule">Cada dato del Atlas lleva una etiqueta: '
        f"{legend}. Lo que no se puede documentar no se presenta como hecho. "
        'Cómo trabajamos está en la <a href="/metodologia-editorial/">metodología editorial</a>.</p>'
    )
    schema = jsonld(
        ATLAS_URL, title, description, data["updated"],
        [("Inicio", SITE + "/"), ("Atlas literario", None)],
        [{
            "@type": "ItemList",
            "@id": ATLAS_URL + "#list",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "url": f"{SITE}/atlas-literario/{e['slug']}/", "name": e["title"]}
                for i, e in enumerate(entries, 1)
            ],
        }],
    )
    main = (
        '<main id="contenido" tabindex="-1" class="v1-main" data-family="atlas">'
        + breadcrumb_html([("Inicio", "/"), ("Atlas literario", None)])
        + hero(
            "Atlas literario",
            "El mundo de los libros también existe fuera de las páginas",
            "Lugares reales donde la literatura se puede visitar, investigados con fuentes y sin mezclar el dato con el mito.",
            len(entries),
            "fichas publicadas",
        )
        + rule
        + "".join(groups)
        + f'<section class="atlas-tail"><p>Revisión del Atlas: <time datetime="{esc(data["verified"])}">{esc(data["verified"])}</time></p>'
        + '<p><a href="/recomendaciones/">Libros recomendados</a></p></section></main>'
    )
    return wrap(title, description, ATLAS_URL, schema, main)


def render_entry(data: dict, e: dict, by_slug: dict[str, dict]) -> str:
    canonical = f"{ATLAS_URL}{e['slug']}/"
    title = f"{e['title']} | Atlas literario | David Porto Díaz"
    if len(title) > 75:  # límite de scripts/check-seo-meta-quality.py
        title = f"{e['title']} | Atlas literario"
    crumbs = [("Inicio", SITE + "/"), ("Atlas literario", ATLAS_URL), (e["title"], None)]
    extra: list[dict] = []
    if e["kind"] == "route":
        extra.append({
            "@type": "ItemList",
            "@id": canonical + "#stops",
            "itemListOrder": "https://schema.org/ItemListOrderAscending",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "name": s["name"]}
                for i, s in enumerate(e["route_stops"], 1)
            ],
        })
    schema = jsonld(canonical, e["title"], e["description"], data["verified"], crumbs, extra)

    sections = "".join(
        f'<h2>{esc(s["h"])}</h2>' + "".join(f"<p>{esc(p)}</p>" for p in s["p"]) for s in e["sections"]
    )
    facts = "".join(
        f'<li><span class="atlas-tag" data-certainty="{f["label"]}">{esc(data["labels"][f["label"]])}</span>{esc(f["text"])}</li>'
        for f in e["facts"]
    )
    aside = []
    if e["kind"] == "route":
        stops = "".join(
            f'<li><strong>{esc(s["name"])}</strong><small>{esc(s["address"])}</small>{esc(s["note"])}</li>'
            for s in e["route_stops"]
        )
        aside.append(f'<section aria-labelledby="atlas-paradas"><h2 id="atlas-paradas">Paradas</h2><ol class="atlas-stops">{stops}</ol></section>')
    aside.append(f'<section aria-labelledby="atlas-datos"><h2 id="atlas-datos">Qué sabemos</h2><ul class="atlas-facts">{facts}</ul></section>')
    if e.get("practical"):
        practical = "".join(f"<li>{esc(p)}</li>" for p in e["practical"])
        aside.append(f'<section aria-labelledby="atlas-practico"><h2 id="atlas-practico">Antes de ir</h2><ul class="atlas-plain">{practical}</ul></section>')
    sources = "".join(
        f'<li><a href="{esc(s["url"])}" rel="noopener noreferrer">{esc(s["label"])}</a></li>' for s in e["sources"]
    )
    aside.append(f'<section aria-labelledby="atlas-fuentes"><h2 id="atlas-fuentes">Fuentes</h2><ul class="atlas-plain">{sources}</ul></section>')
    if e.get("related"):
        related = "".join(
            f'<li><a href="/atlas-literario/{r}/">{esc(by_slug[r]["title"])}</a></li>' for r in e["related"]
        )
        aside.append(f'<section aria-labelledby="atlas-relacionado"><h2 id="atlas-relacionado">Sigue por aquí</h2><ul class="atlas-plain">{related}</ul></section>')

    main = (
        '<main id="contenido" tabindex="-1" class="v1-main" data-family="atlas">'
        + breadcrumb_html([("Inicio", "/"), ("Atlas literario", "/atlas-literario/"), (e["title"], None)])
        + hero(f"{KINDS[e['kind']][2]} · {e['country']}", e["title"], e["lead"], None, "")
        + f'<div class="atlas-article"><div class="atlas-article__main" data-pagefind-filter="atlas_entity:{e["kind"]}">{sections}</div>'
        + f'<aside class="atlas-aside" aria-label="Datos de la ficha">{"".join(aside)}</aside></div>'
        + f'<section class="atlas-tail"><p>Datos revisados el <time datetime="{esc(data["verified"])}">{esc(data["verified"])}</time>. '
        + 'Si ves un error, escríbenos desde la <a href="/metodologia-editorial/">metodología editorial</a>.</p>'
        + '<p><a href="/atlas-literario/">← Todo el Atlas</a></p></section></main>'
    )
    return wrap(title, e["description"], canonical, schema, main)


def build(data_path: Path, root: Path, check_only: bool) -> tuple[int, bool]:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    entries = validate(data)
    by_slug = {e["slug"]: e for e in entries}
    outputs = {"atlas-literario/index.html": inject_shell_auto(render_hub(data, entries))}
    for e in entries:
        outputs[f"atlas-literario/{e['slug']}/index.html"] = inject_shell_auto(render_entry(data, e, by_slug))

    manifest = {
        "schema_version": 1,
        "routes": [{"url": "/atlas-literario/", "kind": "hub"}]
        + [{"url": f"/atlas-literario/{e['slug']}/", "kind": e["kind"]} for e in entries],
    }
    manifest_rel = "data/atlas-routes-manifest.json"
    outputs[manifest_rel] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"

    drift = []
    for rel, content in outputs.items():
        path = root / rel
        if check_only:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                drift.append(rel)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    atlas_dir = root / "atlas-literario"
    if atlas_dir.is_dir():
        for path in atlas_dir.rglob("index.html"):
            rel = path.relative_to(root).as_posix()
            if rel not in outputs:
                drift.append(f"{rel} (sin entrada en el dataset)")
    if check_only:
        if drift:
            print("FAIL: salida desactualizada: " + ", ".join(drift))
            return len(outputs), False
        print(f"PASS: {len(entries)} ficha(s) y hub, salida al día")
        return len(outputs), True
    print(f"GENERATED: hub + {len(entries)} ficha(s) del Atlas")
    return len(outputs), True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        _, ok = build(args.data, args.root, args.check)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
