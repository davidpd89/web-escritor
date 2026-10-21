"""Synthetic regression cases for unpublished atlas static HTML preview.

Do not run Actions; data here are invented and no site files are touched.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts/atlas_static_preview.py"
spec = importlib.util.spec_from_file_location("atlas_static_preview", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

DESCRIPTION = "Una descripción editorial original de prueba. " * 5


def fixture():
    return {
        "destinations": [{"id": "dst-example", "slug": "ciudad-ficticia",
                          "name": "Ciudad de prueba", "country_iso2": "ES",
                          "summary_original": DESCRIPTION,
                          "status": "approved", "verified_at": "2026-10-21"}],
        "places": [{"id": "pla-example", "slug": "biblioteca-de-prueba",
                    "name": "Biblioteca de prueba", "destination_id": "dst-example",
                    "summary_original": DESCRIPTION,
                    "geo_precision": "building", "latitude": 40.2, "longitude": -3.5,
                    "source_ids": ["src-example"], "status": "approved",
                    "verified_at": "2026-10-21"}],
        "works": [{"id": "wrk-example", "title": "Novela de prueba", "status": "approved",
                   "verified_at": "2026-10-21"}],
        "authors": [], "adaptations": [],
        "relationships": [{"id": "rel-example", "status": "approved",
                           "verified_at": "2026-10-21", "place_id": "pla-example",
                           "subject_type": "work", "subject_id": "wrk-example",
                           "relationship_type": "narrative_explicit",
                           "evidence_note": "Obra sintética explícita", "source_ids": ["src-example"]}],
        "sources": [{"id": "src-example", "title": "Fuente sintética",
                     "url": "https://example.org/fictional", "retrieved_at": "2026-10-21",
                     "evidence_summary": "Prueba sintética, no fuente real."}],
    }


class StaticAtlasTest(unittest.TestCase):
    def test_approved_fixture_generates_only_three_pages(self):
        pages = mod.pages_from(fixture())
        self.assertEqual(len(pages), 3)
        self.assertIn("/atlas-literario/", pages)
        self.assertIn("/atlas-literario/destinos/ciudad-ficticia/", pages)
        self.assertIn("/atlas-literario/lugares/biblioteca-de-prueba/", pages)
        page = pages["/atlas-literario/lugares/biblioteca-de-prueba/"]
        self.assertIn("Novela de prueba", page)
        self.assertIn('rel="canonical"', page)
        self.assertIn('property="og:url"', page)
        self.assertNotIn("data-pagefind-body", page)  # index global usa body por defecto
        self.assertIn('data-pagefind-filter="atlas_entity:place"', page)
        self.assertIn('data-pagefind-filter="atlas_city:dst-example"', page)
        self.assertIn('data-pagefind-filter="atlas_work:wrk-example"', page)
        self.assertIn('data-pagefind-filter="atlas_relation:narrative_explicit"', page)
        self.assertIn("BreadcrumbList", page)
        self.assertIn("Ver en el mapa", page)

    def test_cannot_publish_unapproved_place_or_destination(self):
        data = fixture()
        data["places"][0]["status"] = "candidate"
        self.assertEqual(mod.pages_from(data), {})
        data = fixture()
        data["destinations"][0]["status"] = "candidate"
        self.assertEqual(mod.pages_from(data), {})

    def test_no_place_without_sources_or_original_editorial_text(self):
        data = fixture()
        data["sources"][0]["retrieved_at"] = ""
        self.assertEqual(mod.pages_from(data), {})
        data = fixture()
        data["places"][0]["summary_original"] = "Corto"
        self.assertEqual(mod.pages_from(data), {})

    def test_json_ld_escapes_script_end_and_html(self):
        data = fixture()
        data["places"][0]["name"] = "Prueba </script><img src=x onerror=alert(1)>"
        page = mod.pages_from(data)["/atlas-literario/lugares/biblioteca-de-prueba/"]
        self.assertEqual(page.count("</script>"), 1)  # only intended closing script
        self.assertNotIn("<img src=x", page)
        self.assertIn("\\u003c/script>", page)

    def test_unlocated_or_area_is_not_precisely_geocoded(self):
        data = fixture()
        data["places"][0]["geo_precision"] = "area"
        page = mod.pages_from(data)["/atlas-literario/lugares/biblioteca-de-prueba/"]
        self.assertNotIn("GeoCoordinates", page)
        self.assertNotIn("Ver en el mapa", page)

    def test_unverified_relation_is_not_displayed(self):
        data = fixture()
        data["relationships"][0]["status"] = "candidate"
        page = mod.pages_from(data)["/atlas-literario/lugares/biblioteca-de-prueba/"]
        self.assertNotIn("Novela de prueba", page)
        data = fixture()
        data["relationships"][0]["source_ids"] = ["missing-source"]
        page = mod.pages_from(data)["/atlas-literario/lugares/biblioteca-de-prueba/"]
        self.assertNotIn("Novela de prueba", page)

    def test_duplicate_place_slug_is_not_silently_overwritten(self):
        data = fixture()
        other = dict(data["places"][0], id="pla-second")
        data["places"].append(other)
        with self.assertRaisesRegex(ValueError, "URL de lugar duplicada"):
            mod.pages_from(data)


    def test_verified_catalogue_link_can_reuse_existing_book_page(self):
        data = fixture()
        html = mod.pages_from(data, {"wrk-example": "/recomendaciones/libros/coraline/"})[
            "/atlas-literario/lugares/biblioteca-de-prueba/"
        ]
        self.assertIn('href="/recomendaciones/libros/coraline/"', html)
        self.assertIn('Novela de prueba</a>', html)

    def test_untrusted_catalogue_link_not_rendered(self):
        data = fixture()
        html = mod.pages_from(data, {"wrk-example": 'javascript:alert(1)'})[
            "/atlas-literario/lugares/biblioteca-de-prueba/"
        ]
        self.assertNotIn("javascript:alert", html)
        self.assertIn("<li>Novela de prueba</li>", html)

    def test_invalid_film_relation_or_missing_evidence_is_hidden(self):
        data = fixture()
        data["relationships"][0]["relationship_type"] = "filming_location"
        html = mod.pages_from(data)["/atlas-literario/lugares/biblioteca-de-prueba/"]
        self.assertNotIn("Novela de prueba", html)
        data = fixture()
        data["relationships"][0]["evidence_note"] = ""
        html = mod.pages_from(data)["/atlas-literario/lugares/biblioteca-de-prueba/"]
        self.assertNotIn("Novela de prueba", html)

    def test_https_source_must_have_real_host(self):
        data = fixture()
        data["sources"][0]["url"] = "https://"
        self.assertEqual(mod.pages_from(data), {})
        data["sources"][0]["url"] = "https://user:pass@example.org/data"
        self.assertEqual(mod.pages_from(data), {})



if __name__ == "__main__":
    unittest.main()
