"""Cross-PR adapter-to-compositor test; no network and no real user metrics.

Run after combining draft #704 with the unmerged source files from #705/#706/#707:
python -m unittest discover -s tests -p 'test_gpt_social_pipeline.py' -v

In isolated PR #704 these tests SKIP, because the three reader source files are
intentionally confined to other branches. Never copy the readers to this PR.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1] / "scripts" / "research"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load(filename):
    path = ROOT / filename
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("joint_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


compose = load("gpt_social_compose.py")
bluesky = load("gpt_social_bluesky.py")
mastodon = load("gpt_social_mastodon.py")
threads = load("gpt_metricool_threads.py")
metricool_batch_reader = load("gpt_metricool_followers.py")
ALL_PRESENT = all(x is not None for x in (compose, bluesky, mastodon, threads))
TEST_TIME = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def collect():
    assert ALL_PRESENT
    b = bluesky.normalize_profile(
        {"handle": bluesky.ACTOR, "did": "did:plc:synthetic-sample",
         "followersCount": 17, "postsCount": 8},
        expected_did="did:plc:synthetic-sample",
        observed_at="2026-10-22T11:00:00Z")
    m = mastodon.normalize_search(
        {"accounts": [{"id": "synthetic-123", "username": mastodon.USERNAME,
                       "acct": mastodon.USERNAME, "url": mastodon.PROFILE_URL,
                       "followers_count": 23, "statuses_count": 10}]},
        expected_id="synthetic-123",
        observed_at="2026-10-22T10:00:00Z")
    t = threads.normalize(
        {"metrics": ["THEV01"], "from": "2026-10-21", "to": "2026-10-21",
         "rows": [["13.0", "20261021"]]})
    return b, m, t


@unittest.skipUnless(ALL_PRESENT, "Needs PR #705/#706/#707 source modules beside PR #704")
class PipelineTests(unittest.TestCase):
    def test_three_current_sources_sum(self):
        public = compose.compose(collect(), now=TEST_TIME)
        self.assertEqual(public["totals"]["follower_relationships"], 53)
        self.assertEqual(public["totals"]["coverage"], 3)
        self.assertEqual([x["status"] for x in public["networks"]],
                         ["ok", "ok", "ok"] + ["pending"] * 5)
        self.assertEqual(public["totals"]["eligible"], 8)

    def test_real_source_contracts_do_not_leak_private_identifiers(self):
        body = json.dumps(compose.compose(collect(), now=TEST_TIME))
        self.assertNotIn("did:plc:synthetic", body)
        self.assertNotIn("synthetic-123", body)
        self.assertNotIn("postsCount", body)
        self.assertNotIn("views_not_published_reason", body)

    def test_old_metricool_snapshot_kept_out(self):
        b, m, t = collect()
        t["observed_at"] = "2026-10-18"
        public = compose.compose([b, m, t], now=TEST_TIME)
        self.assertEqual(public["totals"]["follower_relationships"], 40)
        self.assertEqual(public["totals"]["coverage"], 2)
        self.assertIsNone(public["networks"][2]["followers"])

    def test_three_sources_through_real_file_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = []
            for number, record in enumerate(collect()):
                path = root / f"source-{number}.json"
                path.write_text(json.dumps(record), encoding="utf-8")
                paths.append(str(path))
            output = root / "public.json"
            # Keep the CLI test on the same clock as its fixed input samples.
            real_compose = compose.compose
            with mock.patch.object(compose, "compose", side_effect=lambda sources: real_compose(sources, now=TEST_TIME)):
                self.assertEqual(compose.main([*paths, "--output", str(output)]), 0)
            public = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(public["totals"]["coverage"], 3)
            self.assertEqual(public["totals"]["follower_relationships"], 53)

    def test_no_unverified_views_can_be_published(self):
        b, m, t = collect()
        t["views_30d"] = 200
        with self.assertRaises(ValueError):
            compose.compose([b, m, t], now=TEST_TIME)

    def test_provider_rejects_wrong_identity_before_aggregation(self):
        with self.assertRaises(ValueError):
            bluesky.normalize_profile(
                {"handle": "another.bsky.social", "did": "did:plc:other"})
        with self.assertRaises(ValueError):
            mastodon.normalize_search({"accounts": [{
                "id": "synthetic-123", "username": mastodon.USERNAME,
                "acct": mastodon.USERNAME,
                "url": "https://another.instance/@davidportodiaz",
                "followers_count": 999}]})



@unittest.skipUnless(ALL_PRESENT and metricool_batch_reader is not None,
                     "Needs the multi-network follower reader from #705")
class MultiMetricoolPipelineTests(unittest.TestCase):
    def test_actual_705_batch_into_actual_704_compositor(self):
        fields = list(metricool_batch_reader.FIELDS)
        synthetic = {
            "metrics": fields, "from": "2026-10-21", "to": "2026-10-21",
            "rows": [[str(100 + i) + ".0" for i in range(len(fields))] + ["20261021"]],
        }
        batch = metricool_batch_reader.normalize(synthetic)
        public = compose.compose([batch], now=TEST_TIME)
        # Facebook is verified by page id since v4, so the batch now counts five networks.
        self.assertEqual(public["totals"]["follower_relationships"], 515)
        self.assertEqual(public["totals"]["coverage"], 5)
        self.assertEqual(public["totals"]["eligible"], 8)
        self.assertEqual(public["networks"][2]["source"], "metricool-mcp-export")
        self.assertIsNone(public["networks"][0]["followers"])
        self.assertIn("instagram", [r["id"] for r in public["networks"]])
        self.assertIn("facebook", [r["id"] for r in public["networks"]])
        self.assertNotIn("youtube", [r["id"] for r in public["networks"]])
        self.assertNotIn("twitter", [r["id"] for r in public["networks"]])

    def test_actual_705_batch_with_public_bluesky_and_mastodon(self):
        fields = list(metricool_batch_reader.FIELDS)
        synthetic = {
            "metrics": fields, "from": "2026-10-21", "to": "2026-10-21",
            "rows": [[str(100 + i) + ".0" for i in range(len(fields))] + ["20261021"]],
        }
        batch = metricool_batch_reader.normalize(synthetic)
        b, m, _ = collect()
        public = compose.compose([batch, b, m], now=TEST_TIME)
        self.assertEqual(public["totals"]["follower_relationships"], 17 + 23 + 515)
        self.assertEqual(public["totals"]["coverage"], 7)
        self.assertEqual(len(public["networks"]), 8)

if __name__ == "__main__":
    unittest.main()
