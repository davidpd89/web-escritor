"""Unit and integration-contract tests for Google Books intake: ZERO network requests."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "reading_intake_fetch", ROOT / "scripts/reading_intake_fetch.py")
intake = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = intake
spec.loader.exec_module(intake)

CONFIG = intake.read_json(ROOT / "data/reading-intake-sources.example.json")
FIXTURES = intake.read_json(ROOT / "tests/fixtures/reading-google-books-2026.json")


class ReadingIntakeFetchTests(unittest.TestCase):
    def test_fixture_deduplicates_published_books(self):
        self.assertIn("9788498382372", intake.existing_isbns(
            ROOT / "data/reading-catalogue.json"))
        state = {"schema_version": 1, "items": {}}
        args = dict(config=CONFIG, fixture=FIXTURES, api_key="",
                    max_requests=10,
                    existing={"9788498382372"}, state=state,
                    today="2026-10-20")
        stats = intake.discover(**args)
        self.assertEqual(stats["requests"], 2)
        self.assertEqual(stats["seen"], 5)
        self.assertEqual(stats["already_published"], 1)
        self.assertEqual(stats["ignored"], 2)
        self.assertEqual(stats["new"], 2)
        self.assertEqual(len(state["items"]), 2)
        self.assertIn("isbn13:9791300000005", state["items"])
        self.assertEqual(state["items"]["isbn13:9791300000005"]["precision_fecha"], "dia")
        self.assertNotIn("isbn13:9788498382372", state["items"])
        before = json.dumps(state, sort_keys=True)
        stats2 = intake.discover(**args)
        self.assertEqual(stats2["new"], 0)
        self.assertEqual(stats2["unchanged"], 2)
        self.assertEqual(before, json.dumps(state, sort_keys=True))

    def test_single_bad_publisher_does_not_stop_next(self):
        modified = json.loads(json.dumps(FIXTURES))
        modified["pages"]["salamandra"] = [{"items": "invalid"}]
        state = {"schema_version": 1, "items": {}}
        stats = intake.discover(CONFIG, fixture=modified, api_key="",
                                max_requests=10, existing=set(),
                                state=state, today="2026-10-20")
        self.assertEqual(len(stats["errors"]), 1)
        self.assertEqual(stats["errors"][0]["publisher"], "salamandra")
        self.assertEqual(stats["new"], 1)

    def test_atomic_write_does_not_modify_if_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            doc = {"schema_version": 1, "items": {}}
            self.assertTrue(intake.write_if_changed(path, doc))
            before = path.stat().st_mtime_ns
            self.assertFalse(intake.write_if_changed(path, doc))
            self.assertEqual(before, path.stat().st_mtime_ns)

    def test_no_network_without_explicit_live(self):
        def forbidden(*_args, **_kwargs):
            raise AssertionError("Unexpected network call")
        state = {"schema_version": 1, "items": {}}
        data = intake.discover(CONFIG, fixture=FIXTURES, api_key="",
                               max_requests=10, existing=set(), state=state,
                               today="2026-10-20", fetch_fn=forbidden)
        self.assertGreater(data["new"], 0)

    def test_request_budget(self):
        state = {"schema_version": 1, "items": {}}
        stats = intake.discover(CONFIG, fixture=FIXTURES, api_key="",
                                max_requests=1, existing=set(),
                                state=state, today="2026-10-20")
        self.assertEqual(stats["requests"], 1)
        with self.assertRaises(ValueError):
            intake.discover(CONFIG, fixture=FIXTURES, api_key="",
                            max_requests=0, existing=set(),
                            state=state, today="2026-10-20")


if __name__ == "__main__":
    unittest.main()
