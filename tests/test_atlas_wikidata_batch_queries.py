"""Offline query-builder checks: never contacts Wikidata or any endpoint."""
import importlib.util
import sys
import unittest
from pathlib import Path

F = Path(__file__).resolve().parents[1] / "scripts/atlas_wikidata_batch_queries.py"
spec = importlib.util.spec_from_file_location("wd_atlas", F)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class WikidataBatchTests(unittest.TestCase):
    def test_narrative_predicate_is_p840(self):
        q = mod.make_query("narrative", ["Q123"])
        self.assertIn("?subject wdt:P840 ?place", q)
        self.assertIn("wd:Q123", q)
        self.assertNotIn("SERVICE wikibase:label", q)

    def test_filming_uses_p915_not_p840(self):
        q = mod.make_query("filming", ["Q456"])
        self.assertIn("wdt:P915", q)
        self.assertNotIn("wdt:P840", q)

    def test_author_residence_uses_p551_not_birthplace(self):
        q = mod.make_query("author_residence", ["Q789"])
        self.assertIn("wdt:P551", q)
        self.assertNotIn("wdt:P19", q)

    def test_dedup_and_split_into_bounded_batches(self):
        result = mod.plan("narrative", ["Q1", "Q1", "Q2", "Q3"], batch_size=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["qids"], ["Q1", "Q2"])
        self.assertEqual(result[1]["qids"], ["Q3"])
        self.assertEqual(len(result[0]["query_sha256"]), 64)

    def test_sparql_injection_cannot_pass_qid_validation(self):
        with self.assertRaisesRegex(ValueError, "QIDs inválidos"):
            mod.make_query("filming", ["Q1 } SERVICE <https://evil.test> {"])
        with self.assertRaises(ValueError):
            mod.plan("narrative", ["Q0"])

    def test_unknown_predicate_and_batch_oversize_rejected(self):
        with self.assertRaises(ValueError):
            mod.make_query("unknown", ["Q1"])
        with self.assertRaises(ValueError):
            mod.make_query("narrative", [f"Q{i}" for i in range(1, 52)])
        with self.assertRaises(ValueError):
            mod.chunks(["Q1"], batch_size=51)

    def test_nothing_is_labelled_published(self):
        for row in mod.plan("filming", ["Q123"]):
            self.assertEqual(row["status"], "UNEXECUTED_CANDIDATE_QUERY")
            self.assertEqual(row["endpoint_policy"], "configure_separately")
            self.assertEqual(row["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
