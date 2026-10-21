"""Contract tests for offline Open Library works dump candidate extraction.

All data fictional; no networking, actual dumps, actions or CI triggered.
"""
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts/atlas_openlibrary_dump_candidates.py"
spec = importlib.util.spec_from_file_location("olatlas", PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def record(kind="/type/work", work="/works/OL123W", title="Novela sintética",
           places=None, authors=None):
    data = {"title": title, "subject_places": ["Ciudad imaginaria"] if places is None else places,
            "authors": [{"author": {"key": "/authors/OL44A"}}] if authors is None else authors}
    return "\t".join([kind, work, "1", "2026-10-01T00:00:00", json.dumps(data)]) + "\n"


class DumpCandidatesTest(unittest.TestCase):
    def test_work_emits_unverified_place_candidate(self):
        row = mod.work_candidate(record())
        self.assertEqual(row["status"], "candidate")
        self.assertEqual(row["work_id"], "OL123W")
        self.assertEqual(row["subject_place_candidates"], ["Ciudad imaginaria"])
        self.assertEqual(row["authors_openlibrary"], ["/authors/OL44A"])
        self.assertEqual(row["relationship_type"], "unverified_subject_place")

    def test_edition_malformed_and_unknown_id_skipped(self):
        self.assertIsNone(mod.work_candidate(record(kind="/type/edition")))
        self.assertIsNone(mod.work_candidate(record(work="/works/FAKE")))
        self.assertIsNone(mod.work_candidate("not\ta\tvalid\n"))

    def test_fuzzy_places_not_inferred(self):
        self.assertIsNone(mod.work_candidate(record(places=[])))
        self.assertIsNone(mod.work_candidate(record(places=["Londres"]), ("tokyo",)))
        self.assertEqual(len(mod.work_candidate(record(places=["Londres", "Londres"]))["subject_place_candidates"]), 1)

    def test_bounded_by_rows_and_candidates(self):
        out, stats = mod.scan(io.StringIO(record() * 5), max_rows=2, max_candidates=10)
        self.assertEqual(len(out), 2)
        self.assertTrue(stats["stopped_by_limit"])
        out, stats = mod.scan(io.StringIO(record() * 5), max_rows=100, max_candidates=1)
        self.assertEqual(len(out), 1)


if __name__ == "__main__":
    unittest.main()
