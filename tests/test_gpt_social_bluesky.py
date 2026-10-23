#!/usr/bin/env python3
"""Offline contract tests for the proposed Bluesky extractor.

Run: python -m unittest discover -s tests -p 'test_gpt_social_bluesky.py' -v
"""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts/research/gpt_social_bluesky.py"
spec = importlib.util.spec_from_file_location("gpt_social_bluesky", MODULE)
bs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs)

VALID = {"handle": bs.ACTOR, "did": "did:plc:verified-demo", "followersCount": 23, "postsCount": 0}


class BlueskyContractTests(unittest.TestCase):
    def test_valid(self):
        got = bs.normalize_profile(VALID, expected_did=VALID["did"], observed_at="2026-10-22T11:00:00Z")
        self.assertEqual((got["followers"], got["posts"], got["status"]), (23, 0, "ok"))
        self.assertIsNone(got["impressions_30d"])
        self.assertIsNone(got["views_30d"])
        self.assertEqual(got["observed_at"], "2026-10-22T11:00:00Z")

    def test_missing_count_is_not_zero(self):
        got = bs.normalize_profile({"handle": bs.ACTOR, "did": "did:plc:x"})
        self.assertIsNone(got["followers"])
        self.assertEqual(got["status"], "partial")

    def test_zero_is_valid(self):
        self.assertEqual(bs.optional_count(0), 0)

    def test_bad_counts_rejected(self):
        for value in (True, -1, 5.2, "99", [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                bs.normalize_profile({**VALID, "followersCount": value})

    def test_identity_drift_rejected(self):
        for changes in ({"handle": "fake.bsky.social"}, {"did": "not-did"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bs.normalize_profile({**VALID, **changes})
        with self.assertRaises(ValueError):
            bs.normalize_profile(VALID, expected_did="did:plc:other")

    def test_nonobject_rejected(self):
        with self.assertRaises(ValueError):
            bs.normalize_profile([])

    def test_single_url_read_and_parse(self):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, n):
                return json.dumps(VALID).encode("utf-8")
        with patch.object(bs, "urlopen", return_value=Response()) as opener:
            self.assertEqual(bs.read_profile(), VALID)
            self.assertEqual(opener.call_count, 1)
            self.assertIn("actor=davidportoescritor.bsky.social", opener.call_args.args[0].full_url)

    def test_oversize_fails(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n): return b"x" * n
        with patch.object(bs, "urlopen", return_value=Response()), self.assertRaises(ValueError):
            bs.read_profile()

    def test_atomic_preserves_old_after_bad_profile(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "latest.json"
            path.write_text('{"last_good": true}', encoding="utf-8")
            with patch.object(bs, "read_profile", return_value={"handle": "wrong", "did": "did:plc:x"}):
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(bs.main(["--expected-did", "did:plc:x", "--output", str(path)]), 1)
            self.assertEqual(json.loads(path.read_text()), {"last_good": True})

    def test_partial_preserves_old_output(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "latest.json"
            path.write_text('{"last_good": true}', encoding="utf-8")
            with patch.object(bs, "read_profile", return_value={"handle": bs.ACTOR, "did": "did:plc:x"}):
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(bs.main(["--expected-did", "did:plc:x", "--output", str(path)]), 1)
            self.assertEqual(json.loads(path.read_text()), {"last_good": True})

    def test_write_requires_verified_did(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            bs.main(["--output", "/tmp/no.json"])

    def test_fixture_is_not_publishable(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "fixture.json"
            file.write_text(json.dumps(VALID), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(bs.main(["--fixture", str(file)]), 0)
            self.assertEqual(json.loads(out.getvalue())["followers"], 23)
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                bs.main(["--fixture", str(file), "--output", str(Path(d) / "never.json")])

    def test_output_write_works_when_live_mock_valid(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "stats.json"
            with patch.object(bs, "read_profile", return_value=VALID):
                self.assertEqual(bs.main(["--expected-did", VALID["did"], "--output", str(target)]), 0)
            self.assertEqual(json.loads(target.read_text())["followers"], 23)


if __name__ == "__main__":
    unittest.main()
