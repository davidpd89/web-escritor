"""Synthetic Atlas -> existing reading catalogue bridge tests. Not executed."""
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/atlas_reading_crosslinks.py"
spec = importlib.util.spec_from_file_location("reading_crosslinks", SCRIPT)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def snapshots():
    atlas = {"schema_version": 1, "works": [
        {"id": "wrk-a", "status": "approved", "reading_book_id": "lib-0001"},
        {"id": "wrk-external", "status": "approved"}
    ]}
    reading = {"schema_version": 1, "libros": [
        {"id": "lib-0001", "slug": "coraline", "estado": "publicado"},
        {"id": "lib-0002", "slug": "un-libro", "estado": "borrador"}
    ]}
    return atlas, reading


class AtlasReadingLinks(unittest.TestCase):
    def test_exact_id_maps_only_to_published_canonical_url(self):
        atlas, reading = snapshots()
        self.assertEqual(mod.canonical_links(atlas, reading),
                         {"wrk-a": "/recomendaciones/libros/coraline/"})

    def test_missing_book_fails_instead_of_creating_dead_link(self):
        atlas, reading = snapshots()
        atlas["works"][0]["reading_book_id"] = "isbn-inexistente"
        with self.assertRaisesRegex(ValueError, "no existe"):
            mod.canonical_links(atlas, reading)

    def test_draft_book_is_never_linked(self):
        atlas, reading = snapshots()
        atlas["works"][0]["reading_book_id"] = "lib-0002"
        with self.assertRaisesRegex(ValueError, "sin publicación"):
            mod.canonical_links(atlas, reading)

    def test_url_path_cannot_escape_known_catalogue_prefix(self):
        atlas, reading = snapshots()
        reading["libros"][0]["slug"] = "../unsafe"
        with self.assertRaisesRegex(ValueError, "Slug"):
            mod.canonical_links(atlas, reading)

    def test_duplicate_work_mapping_rejected(self):
        atlas, reading = snapshots()
        atlas["works"].append({"id": "wrk-duplicate", "status": "approved",
                               "reading_book_id": "lib-0001"})
        with self.assertRaisesRegex(ValueError, "comparten"):
            mod.canonical_links(atlas, reading)

    def test_unapproved_work_cannot_acquire_public_link(self):
        atlas, reading = snapshots()
        atlas["works"][0]["status"] = "candidate"
        self.assertEqual(mod.canonical_links(atlas, reading), {})


if __name__ == "__main__":
    unittest.main()
