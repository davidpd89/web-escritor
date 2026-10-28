"""Synthetic offline Planeta adapter tests."""
import importlib.util
import sys
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "scripts/reading_planeta_offline_probe.py"
spec = importlib.util.spec_from_file_location("planeta_probe", FILE)
probe = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = probe
spec.loader.exec_module(probe)

LIVE_EXAMPLE = "https://www.planetadelibros.com/libro-cosamala/458658"
# Hand-authored fixture from OFFICIAL VISIBLE Ficha Técnica, not raw HTML QA.
HTML = """<!doctype html><html><body>
<nav><a href="/libro-cosamala/458658">Cosamala</a>
<a href="/libro-otra-novela/123457">Otra</a>
<a href="https://evil.test/libro-extra/333333">Fuera</a></nav>
<h1>Cosamala</h1><h2>Ficha Técnica</h2>
<dl><dt>Publicación</dt><dd>14 octubre 2026</dd>
<dt>Editorial</dt><dd>Seix Barral</dd>
<dt>ISBN</dt><dd>978-84-322-5143-6</dd>
<dt>Páginas</dt><dd>272</dd></dl>
</body></html>"""


class PlanetaOfflineProbeTest(unittest.TestCase):
    def test_listing_only_official_product_links(self):
        self.assertEqual(probe.listing_urls(HTML), [
            "https://www.planetadelibros.com/libro-cosamala/458658",
            "https://www.planetadelibros.com/libro-otra-novela/123457",
        ])

    def test_edition_only_verified_identity_and_date(self):
        row = probe.edition_candidate(HTML, LIVE_EXAMPLE)
        self.assertEqual(row["isbn13"], "9788432251436")
        self.assertEqual(row["fecha_publicacion_edicion"], "2026-10-14")
        self.assertEqual(row["editorial"], "Seix Barral")
        self.assertEqual(row["titulo"], "Cosamala")
        self.assertEqual(row["numero_paginas"], 272)
        self.assertEqual(row["status"], "candidate_review")
        self.assertFalse(row["authors_verified"])

    def test_wrong_host_and_redirect_not_accepted(self):
        self.assertIsNone(probe.product_url("https://other.example/libro-cosamala/458658"))
        self.assertIsNone(probe.product_url(
            "https://www.planetadelibros.com/libro-cosamala/458658?ref=other"
        ))

    def test_invalid_checksum_fails_closed(self):
        wrong = HTML.replace("978-84-322-5143-6", "978-84-322-5143-7")
        self.assertIsNone(probe.edition_candidate(wrong, LIVE_EXAMPLE))

    def test_month_without_exact_day_not_a_release_day(self):
        old = HTML.replace("14 octubre 2026", "octubre 2026")
        self.assertIsNone(probe.edition_candidate(old, LIVE_EXAMPLE))

    def test_no_ficha_tecnica_no_candidate(self):
        self.assertIsNone(probe.edition_candidate("<h1>Cosamala</h1>", LIVE_EXAMPLE))


if __name__ == "__main__":
    unittest.main()
