#!/usr/bin/env python3
"""Offline gate for future published literary-atlas HTML.

Scope: only indexable atlas routes, not provider ingestion/accuracy. Runs on
a PRE-BUILT, fully assembled static site root after shell/sitemap/Pagefind.
Does not access network, GitHub, Google APIs, or mutate files.

Not wired to CI yet: call manually after future implementation is authorized.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

SITE = "https://davidportodiaz.com"
ATLAS = "/atlas-literario/"
REQUIRED_KINDS = {"hub", "destination", "place", "route"}
PATH_RE = re.compile(r"^/atlas-literario/(?:[a-z0-9-]+/)*$")
FORBIDDEN_PUBLIC_TERMS = (
    "reviewer_note_private", "provider_api_key", "google_sheets_access_token",
    "candidate_jsonl", "source_raw_private",
)


class Inspect(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.in_title = False
        self.h1_count = 0
        self.canonicals: list[str] = []
        self.description: list[str] = []
        self.robots: list[str] = []
        self.hrefs: list[str] = []
        self.script_src: list[str] = []
        self.pagefind_filters: list[str] = []
        self.jsonld_texts: list[str] = []
        self.in_jsonld = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1_count += 1
        if tag == "link" and "canonical" in (attrs.get("rel") or "").split():
            self.canonicals.append(attrs.get("href") or "")
        if tag == "meta" and attrs.get("name", "").lower() == "description":
            self.description.append(attrs.get("content") or "")
        if tag == "meta" and attrs.get("name", "").lower() == "robots":
            self.robots.append(attrs.get("content") or "")
        if attrs.get("data-pagefind-filter"):
            self.pagefind_filters.append(attrs["data-pagefind-filter"])
        if tag == "a":
            self.hrefs.append(attrs.get("href") or "")
        if tag == "script":
            src = attrs.get("src")
            if src:
                self.script_src.append(src)
            if attrs.get("type") == "application/ld+json":
                self.in_jsonld = True
                self.jsonld_texts.append("")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script":
            self.in_jsonld = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_jsonld and self.jsonld_texts:
            self.jsonld_texts[-1] += data


def file_for(root: Path, url: str) -> Path:
    if not PATH_RE.fullmatch(url):
        raise ValueError("Ruta no válida para Atlas: " + repr(url))
    p = (root / url.lstrip("/") / "index.html").resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError("Ruta fuera de root")
    return p


def audit(root: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    records = manifest.get("routes")
    if manifest.get("schema_version") != 1 or not isinstance(records, list) or not records:
        return ["Manifest sin schema_version=1 o rutas"]
    urls = {}
    for entry in records:
        if not isinstance(entry, dict):
            errors.append("Entrada route debe ser objeto")
            continue
        url, kind = entry.get("url"), entry.get("kind")
        if not isinstance(url, str) or kind not in REQUIRED_KINDS:
            errors.append("URL/kind no válido: " + repr(entry))
            continue
        if url in urls:
            errors.append("URL duplicada: " + url)
        urls[url] = kind
    if ATLAS not in urls or urls[ATLAS] != "hub":
        errors.append("Falta hub indexable en manifest")

    title_seen: set[str] = set()
    desc_seen: set[str] = set()
    for url, kind in sorted(urls.items()):
        try:
            path = file_for(root, url)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not path.is_file():
            errors.append(url + " apunta a fichero inexistente")
            continue
        source = path.read_text(encoding="utf-8")
        lower = source.casefold()
        # Pagefind processes one combined corpus: tagging only Atlas body would
        # drop unrelated legacy pages from the global index (Pagefind docs).
        if "data-pagefind-body" in lower:
            errors.append(url + " introduce data-pagefind-body parcial: riesgo global Pagefind")
        for needle in FORBIDDEN_PUBLIC_TERMS:
            if needle in lower:
                errors.append(url + " filtra información de revisión: " + needle)
        page = Inspect()
        page.feed(source)
        if page.h1_count != 1:
            errors.append(url + " necesita exactamente un h1")
        if not page.title.strip() or page.title.strip() in title_seen:
            errors.append(url + " title vacío o duplicado")
        title_seen.add(page.title.strip())
        if len(page.description) != 1 or len(page.description[0].strip()) < 60:
            errors.append(url + " meta description ausente/corta/duplicada")
        else:
            desc = page.description[0].strip()
            if desc in desc_seen:
                errors.append(url + " meta description repetida")
            desc_seen.add(desc)
        if page.canonicals != [SITE + url]:
            errors.append(url + " canonical incorrecto")
        if any("noindex" in value.lower() for value in page.robots):
            errors.append(url + " noindex en página aprobada")
        if kind != "hub":
            if not any(f"atlas_entity:{kind}" in value.split(",") for value in page.pagefind_filters):
                errors.append(url + " sin filtro Pagefind de tipo de entidad")
            if not page.jsonld_texts:
                errors.append(url + " sin JSON-LD")
            else:
                types = []
                for script in page.jsonld_texts:
                    try:
                        raw = json.loads(script)
                    except json.JSONDecodeError:
                        errors.append(url + " JSON-LD inválido")
                        continue
                    graph = raw.get("@graph") if isinstance(raw, dict) else None
                    nodes = graph if isinstance(graph, list) else [raw]
                    types.extend(node.get("@type") for node in nodes if isinstance(node, dict))
                if "BreadcrumbList" not in types:
                    errors.append(url + " sin BreadcrumbList")
        if kind in {"hub", "destination"}:
            heavy = ("maplibre", "leaflet", "supercluster", "google-maps")
            if any(any(tag in src.lower() for tag in heavy) for src in page.script_src):
                errors.append(url + " carga motor de mapa en la primera visita")
        for href in page.hrefs:
            href = html.unescape(href)
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc:
                continue
            if parsed.path.startswith(ATLAS):
                target = parsed.path if parsed.path.endswith("/") else parsed.path + "/"
                if target not in urls:
                    errors.append(url + " enlaza a Atlas no publicado: " + target)
                else:
                    p = file_for(root, target)
                    if not p.is_file():
                        errors.append(url + " enlace interno a 404: " + target)
            elif parsed.path.startswith("/recomendaciones/libros/"):
                # Atlas may link only to the canonical pages of existing books;
                # do not let a known ID turn into a guessed affiliate URL/404.
                if not re.fullmatch(
                    r"/recomendaciones/libros/[a-z0-9]+(?:-[a-z0-9]+)*/", parsed.path
                ):
                    errors.append(url + " enlace a libro con ruta no canónica: " + parsed.path)
                else:
                    book_html = root / parsed.path.lstrip("/") / "index.html"
                    if not book_html.is_file():
                        errors.append(url + " enlaza a libro sin HTML: " + parsed.path)

    # No indexable atlas route may be silently omitted from the approved manifest.
    atlas_dir = root / "atlas-literario"
    if atlas_dir.is_dir():
        for path in atlas_dir.rglob("index.html"):
            actual = "/" + path.relative_to(root).parent.as_posix().rstrip("/") + "/"
            if actual not in urls:
                errors.append("HTML Atlas sin manifest público: " + actual)
    return errors


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", required=True, type=Path, help="Static site build root")
    p.add_argument("--manifest", required=True, type=Path,
                   help="Atlas approved routes manifest JSON (no private data)")
    args = p.parse_args()
    issues = audit(args.root, json.loads(args.manifest.read_text(encoding="utf-8")))
    for issue in issues:
        print("FAIL " + issue)
    print(f"atlas-release-contract: {len(issues)} error(es)")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
