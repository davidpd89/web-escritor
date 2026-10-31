import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "research"))
import gpt_social_snapshot as snap  # noqa: E402

FX = ROOT / "tests" / "fixtures" / "social"
NOW = "2026-10-22T08:00:00Z"


class SnapshotPipelineTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.out = self.dir / "out" / "social-metrics.json"

    def args(self, now=NOW, **skip):
        a = ["--output", str(self.out), "--now", now]
        for flag, name in (("--bluesky-fixture", "bluesky_profile"), ("--mastodon-fixture", "mastodon_search"),
                           ("--metricool-export", "metricool_followers")):
            if flag not in skip:
                a += [flag, str(FX / f"{name}.fixture.json")]
        return a

    def read(self):
        return json.loads(self.out.read_text(encoding="utf-8"))

    def test_full_offline_run_covers_six_networks_without_private_ids(self):
        self.assertEqual(snap.main(self.args()), 0)
        data = self.read()
        by_id = {n["id"]: n for n in data["networks"]}
        self.assertEqual(list(by_id), ["bluesky", "mastodon", "threads", "instagram", "tiktok", "pinterest"])
        self.assertEqual(by_id["bluesky"]["followers"], 23)  # public AppView wins over Metricool's 900
        self.assertEqual(data["totals"]["follower_relationships"], 23 + 23 + 101 + 102 + 104 + 105)
        text = self.out.read_text(encoding="utf-8")
        for private in ("did:", "fixture-local", "facebook", "youtube", "twitter"):
            self.assertNotIn(private, text)

    def test_rerun_is_idempotent_and_ignores_generated_at(self):
        snap.main(self.args())
        os.utime(self.out, (1, 1))
        self.assertEqual(snap.main(self.args()), 0)
        self.assertEqual(self.out.stat().st_mtime, 1)

    def test_same_values_within_refresh_window_do_not_rewrite(self):
        snap.main(self.args())
        os.utime(self.out, (1, 1))
        snap.main(self.args(now="2026-10-22T09:00:00Z"))  # only observed_at moved, 1 h
        self.assertEqual(self.out.stat().st_mtime, 1)

    def test_same_values_after_refresh_window_rewrite_to_extend_freshness(self):
        snap.main(self.args())
        os.utime(self.out, (1, 1))
        snap.main(self.args(now="2026-10-22T15:00:00Z"))  # 7 h: must renew observed_at
        self.assertNotEqual(self.out.stat().st_mtime, 1)

    def test_failed_source_keeps_unexpired_last_good_value(self):
        snap.main(self.args())
        bad = self.dir / "bad.json"
        bad.write_text('{"accounts": []}', encoding="utf-8")
        a = self.args(now="2026-10-22T20:00:00Z", **{"--mastodon-fixture": 1}) + ["--mastodon-fixture", str(bad)]
        self.assertEqual(snap.main(a), 0)
        m = {n["id"]: n for n in self.read()["networks"]}["mastodon"]
        self.assertEqual((m["followers"], m["observed_at"]), (23, "2026-10-22T08:00:00Z"))

    def test_expired_last_good_is_not_resurrected(self):
        snap.main(self.args())
        bad = self.dir / "bad.json"
        bad.write_text('{"accounts": []}', encoding="utf-8")
        a = self.args(now="2026-10-25T08:00:00Z", **{"--mastodon-fixture": 1, "--metricool-export": 1}) \
            + ["--mastodon-fixture", str(bad)]
        self.assertEqual(snap.main(a), 0)  # bluesky refreshed; expired mastodon must not survive carry-over
        m = {n["id"]: n for n in self.read()["networks"]}
        self.assertIsNone(m["mastodon"]["followers"])

    def test_zero_after_positive_count_keeps_last_good_value(self):
        snap.main(self.args())
        raw = json.loads((FX / "metricool_followers.fixture.json").read_text())
        raw["rows"][0][4] = "0.0"  # TikTok: Metricool's unconsolidated day
        zero = self.dir / "zero.json"
        zero.write_text(json.dumps(raw), encoding="utf-8")
        a = self.args(now="2026-10-22T20:00:00Z", **{"--metricool-export": 1}) + ["--metricool-export", str(zero)]
        self.assertEqual(snap.main(a), 0)
        m = {n["id"]: n for n in self.read()["networks"]}
        self.assertEqual(m["tiktok"]["followers"], 104)
        self.assertEqual(m["instagram"]["followers"], 102)

    def test_zero_without_positive_history_is_published(self):
        raw = json.loads((FX / "metricool_followers.fixture.json").read_text())
        raw["rows"][0][5] = "0.0"  # Pinterest legitimately starting at 0
        zero = self.dir / "zero.json"
        zero.write_text(json.dumps(raw), encoding="utf-8")
        self.assertEqual(snap.main(self.args(**{"--metricool-export": 1}) + ["--metricool-export", str(zero)]), 0)
        m = {n["id"]: n for n in self.read()["networks"]}
        self.assertEqual(m["pinterest"]["followers"], 0)

    def test_all_sources_failing_preserves_output(self):
        snap.main(self.args())
        before = self.out.read_bytes()
        bad = self.dir / "bad.json"
        bad.write_text("{}", encoding="utf-8")
        a = ["--output", str(self.out), "--now", "2026-10-30T00:00:00Z",
             "--bluesky-fixture", str(bad), "--mastodon-fixture", str(bad)]
        self.assertEqual(snap.main(a), 1)
        self.assertEqual(self.out.read_bytes(), before)

    def test_wrong_bluesky_identity_is_rejected_others_still_publish(self):
        wrong = self.dir / "wrong.json"
        wrong.write_text('{"handle": "someone.else.social", "did": "did:plc:x", "followersCount": 9999}', encoding="utf-8")
        a = self.args(**{"--bluesky-fixture": 1}) + ["--bluesky-fixture", str(wrong)]
        self.assertEqual(snap.main(a), 0)
        m = {n["id"]: n for n in self.read()["networks"]}
        self.assertIsNone(m["bluesky"]["followers"])
        self.assertEqual(m["mastodon"]["followers"], 23)

    def test_metricool_period_mismatch_rejected(self):
        raw = json.loads((FX / "metricool_followers.fixture.json").read_text())
        raw["to"] = "2026-10-20"  # rows are dated 2026-10-21
        bad = self.dir / "m.json"
        bad.write_text(json.dumps(raw), encoding="utf-8")
        a = self.args(**{"--metricool-export": 1}) + ["--metricool-export", str(bad)]
        self.assertEqual(snap.main(a), 0)
        m = {n["id"]: n for n in self.read()["networks"]}
        self.assertIsNone(m["threads"]["followers"])
        self.assertEqual(m["bluesky"]["followers"], 23)

    @unittest.skipUnless(shutil.which("node"), "node required")
    def test_python_output_is_accepted_by_javascript_reader(self):
        snap.main(self.args())
        script = ("import {visibleSocialMetrics as v} from %s;import fs from 'node:fs';"
                  "const d=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));"
                  "const r=v(d,Date.parse('2026-10-22T12:00:00Z'));"
                  "const e=v(d,Date.parse('2026-10-26T00:00:00Z'));"
                  "console.log(JSON.stringify([r.totals.follower_relationships,e.totals.follower_relationships]))"
                  % json.dumps((ROOT / "scripts/research/gpt_social_reader.mjs").as_uri()))
        js = self.dir / "check.mjs"
        js.write_text(script,
                      encoding="utf-8")
        out = subprocess.run(["node", str(js), str(self.out)], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(out.stdout), [458, None])


if __name__ == "__main__":
    unittest.main()
