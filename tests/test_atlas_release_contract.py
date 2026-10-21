"""Unexecuted offline contract tests using synthetic static HTML only."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_atlas_release_contract.py"
spec = importlib.util.spec_from_file_location("atlas_release", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SITE = "https://davidportodiaz.com"
DESC = "Guía literaria de prueba con información contrastada, fuentes y navegación entre destinos y lugares documentados."


def render(url, title, body="", ld=None, extra="", entity=None):
    canonical = SITE + url
    schema = ('<script type="application/ld+json">' +
              json.dumps({"@context": "https://schema.org", "@graph": ld}) + "</script>") if ld else ""
    facets = f'<span data-pagefind-filter="atlas_entity:{entity}"></span>' if entity else ''
    return (f'<!doctype html><html lang="es"><head><title>{title}</title>'
            f'<meta name="description" content="{DESC} {title}">'
            f'<link rel="canonical" href="{canonical}">'
            f'{schema}{extra}</head><body><main><h1>{title}</h1>{facets}{body}</main></body></html>')


def fixture(root):
    pages = {
        "/atlas-literario/": render(
            "/atlas-literario/", "Atlas literario",
            '<a href="/atlas-literario/destinos/ciudad-ejemplo/">Ciudad ejemplo</a>'
        ),
        "/atlas-literario/destinos/ciudad-ejemplo/": render(
            "/atlas-literario/destinos/ciudad-ejemplo/", "Lugares literarios en ciudad de ejemplo",
            '<a href="/atlas-literario/lugares/biblioteca-ejemplo/">Biblioteca ejemplo</a>',
            [{"@type": "BreadcrumbList", "itemListElement": []},
             {"@type": "CollectionPage", "name": "Ciudad ejemplo"}], entity="destination"
        ),
        "/atlas-literario/lugares/biblioteca-ejemplo/": render(
            "/atlas-literario/lugares/biblioteca-ejemplo/", "Biblioteca ejemplo y sus libros",
            '<a href="/atlas-literario/destinos/ciudad-ejemplo/">Volver</a>',
            [{"@type": "BreadcrumbList", "itemListElement": []},
             {"@type": "Place", "name": "Biblioteca ejemplo"}], entity="place"
        ),
    }
    for url, content in pages.items():
        path = root / url.lstrip("/") / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return {"schema_version": 1, "routes": [
        {"url": "/atlas-literario/", "kind": "hub"},
        {"url": "/atlas-literario/destinos/ciudad-ejemplo/", "kind": "destination"},
        {"url": "/atlas-literario/lugares/biblioteca-ejemplo/", "kind": "place"},
    ]}


class AtlasReleaseContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = fixture(self.root)

    def test_approved_routes_full_graph(self):
        self.assertEqual(mod.audit(self.root, self.manifest), [])

    def test_orphan_card_points_to_missing_html(self):
        path = self.root / "atlas-literario/lugares/biblioteca-ejemplo/index.html"
        path.unlink()
        errors = mod.audit(self.root, self.manifest)
        self.assertTrue(any("inexistente" in e or "404" in e for e in errors))

    def test_pending_or_debug_page_cannot_leak(self):
        f = self.root / "atlas-literario/lugares/biblioteca-ejemplo/index.html"
        f.write_text(f.read_text(encoding="utf-8") + "reviewer_note_private",
                     encoding="utf-8")
        self.assertTrue(any("información de revisión" in e for e in mod.audit(self.root, self.manifest)))
        extra = self.root / "atlas-literario/lugares/no-aprobado/index.html"
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text("noindex", encoding="utf-8")
        self.assertTrue(any("sin manifest" in e for e in mod.audit(self.root, self.manifest)))

    def test_canonical_and_description_collisions(self):
        f = self.root / "atlas-literario/destinos/ciudad-ejemplo/index.html"
        f.write_text(f.read_text(encoding="utf-8").replace(
            SITE + "/atlas-literario/destinos/ciudad-ejemplo/",
            SITE + "/atlas-literario/lugares/biblioteca-ejemplo/"), encoding="utf-8")
        self.assertTrue(any("canonical" in e for e in mod.audit(self.root, self.manifest)))

    def test_heavy_map_is_forbidden_on_initial_destination(self):
        f = self.root / "atlas-literario/destinos/ciudad-ejemplo/index.html"
        f.write_text(f.read_text(encoding="utf-8").replace(
            "</head>", '<script src="/assets/maplibre-gl.js"></script></head>'), encoding="utf-8")
        self.assertTrue(any("carga motor de mapa" in e for e in mod.audit(self.root, self.manifest)))

    def test_schema_has_breadcrumbs_and_valid_jsonld(self):
        f = self.root / "atlas-literario/lugares/biblioteca-ejemplo/index.html"
        f.write_text(f.read_text(encoding="utf-8").replace('"BreadcrumbList"', '"Thing"'),
                     encoding="utf-8")
        self.assertTrue(any("BreadcrumbList" in e for e in mod.audit(self.root, self.manifest)))

    def test_manifest_rejects_duplicate_url(self):
        self.manifest["routes"].append(dict(self.manifest["routes"][0]))
        self.assertTrue(any("duplicada" in e for e in mod.audit(self.root, self.manifest)))

    def test_missing_pagefind_type_filter_is_a_release_failure(self):
        f = self.root / "atlas-literario/lugares/biblioteca-ejemplo/index.html"
        f.write_text(f.read_text(encoding="utf-8").replace(
            '<span data-pagefind-filter="atlas_entity:place"></span>', ''),
            encoding="utf-8")
        self.assertTrue(any("filtro Pagefind" in e for e in mod.audit(self.root, self.manifest)))

    def test_pagefind_partial_body_attribute_cannot_deindex_existing_site(self):
        f = self.root / "atlas-literario/lugares/biblioteca-ejemplo/index.html"
        f.write_text(f.read_text(encoding="utf-8").replace(
            "<main>", "<main data-pagefind-body>"), encoding="utf-8")
        self.assertTrue(any("data-pagefind-body parcial" in e for e in
                            mod.audit(self.root, self.manifest)))


    def test_atlas_to_reading_book_link_needs_real_html(self):
        url = "/atlas-literario/lugares/biblioteca-ejemplo/"
        f = self.root / url.lstrip("/") / "index.html"
        text = f.read_text(encoding="utf-8").replace(
            "</main>", '<a href="/recomendaciones/libros/coraline/">Coraline</a></main>'
        )
        f.write_text(text, encoding="utf-8")
        self.assertTrue(any("libro sin HTML" in e for e in mod.audit(self.root, self.manifest)))
        book = self.root / "recomendaciones/libros/coraline/index.html"
        book.parent.mkdir(parents=True, exist_ok=True)
        book.write_text("<h1>Coraline</h1>", encoding="utf-8")
        self.assertEqual(mod.audit(self.root, self.manifest), [])


if __name__ == "__main__":
    unittest.main()
