"""Atlas renderer against the REAL reading catalogue (no network, no site changes)."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import atlas_reading_crosslinks as links  # noqa: E402
import atlas_static_preview as preview  # noqa: E402

sys.path.insert(0, str(ROOT / "tests"))
from test_atlas_static_preview import fixture  # noqa: E402

REAL = json.loads((ROOT / "data/reading-catalogue.json").read_text(encoding="utf-8"))


def snapshot_with_real_book(book_id):
    data = fixture()
    data["schema_version"] = 1
    data["works"][0]["reading_book_id"] = book_id
    return data


class RealCatalogueBridge(unittest.TestCase):
    def published(self):
        return [b for b in REAL["libros"] if b.get("estado") == "publicado"]

    def test_every_published_book_resolves_to_an_existing_page(self):
        self.assertTrue(self.published())
        for book in self.published():
            data = snapshot_with_real_book(book["id"])
            url = links.canonical_links(data, REAL)["wrk-example"]
            self.assertTrue((ROOT / url.lstrip("/") / "index.html").is_file(), url)

    def test_unknown_book_id_fails_closed(self):
        with self.assertRaises(ValueError):
            links.canonical_links(snapshot_with_real_book("lib-9999"), REAL)

    def test_render_links_book_without_affiliate_or_duplicate_pages(self):
        book = self.published()[0]
        data = snapshot_with_real_book(book["id"])
        pages = preview.pages_from(data, links.canonical_links(data, REAL))
        place = pages["/atlas-literario/lugares/biblioteca-de-prueba/"]
        self.assertIn('href="/recomendaciones/libros/' + book["slug"] + '/"', place)
        for forbidden in ("amazon.", "amzn.to", "tag="):
            self.assertNotIn(forbidden, place)
        self.assertFalse(any(u.startswith("/recomendaciones/") for u in pages))

    def test_cli_only_writes_inside_atlas_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            snap = Path(tmp) / "snapshot.json"
            snap.write_text(json.dumps(snapshot_with_real_book(self.published()[0]["id"])), encoding="utf-8")
            bad = subprocess.run([sys.executable, str(ROOT / "scripts/atlas_static_preview.py"), str(snap),
                                  "--out", str(Path(tmp) / "site")], capture_output=True)
            self.assertNotEqual(bad.returncode, 0)
            out = Path(tmp) / "atlas-preview"
            ok = subprocess.run([sys.executable, str(ROOT / "scripts/atlas_static_preview.py"), str(snap),
                                 "--out", str(out), "--reading-catalogue", str(ROOT / "data/reading-catalogue.json")],
                                capture_output=True)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(len(list(out.rglob("index.html"))), 3)


class PublicationGate(unittest.TestCase):
    def test_site_atlas_data_has_no_approved_records_rendered_by_preview(self):
        atlas = json.loads((ROOT / "data/atlas-literario.json").read_text(encoding="utf-8"))
        # Los registros actuales usan otro esquema (guias) y el renderer exige destinations[] aprobados.
        self.assertEqual(preview.pages_from(atlas), {})

    def test_planned_or_unverified_records_generate_nothing(self):
        data = fixture()
        for key in ("destinations", "places"):
            data[key][0]["status"] = "planned"
        self.assertEqual(preview.pages_from(data), {})
        data = fixture()
        data["places"][0].pop("verified_at")
        pages = preview.pages_from(data)
        self.assertNotIn("/atlas-literario/lugares/biblioteca-de-prueba/", pages)


if __name__ == "__main__":
    unittest.main()
