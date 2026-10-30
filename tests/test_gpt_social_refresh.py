from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "research"))
import gpt_metricool_live as live  # noqa: E402
import gpt_metricool_mcp as mcp  # noqa: E402
import gpt_social_refresh as refresh  # noqa: E402

NOW = datetime(2026, 10, 23, 8, 0, tzinfo=timezone.utc)
GOOD_BRAND = {"id": 1, "networksData": {"threadsData": "davidporto.escritor", "instagramData": "davidporto.escritor",
                                         "tiktokData": "davidporto.escritor", "pinterestData": "davidportoescritor"}}


class FakeClient:
    def __init__(self, brands, rows=None):
        self.brands, self.rows = brands, rows

    def call(self, name, args):
        if name == "getBrandSettings":
            return {"data": self.brands}
        return {"rows": self.rows}


class LiveAdapterTests(unittest.TestCase):
    def test_wrong_handle_is_rejected(self):
        bad = {"id": 2, "networksData": {"threadsData": "someone_else"}}
        with self.assertRaises(ValueError):
            live.pick_brand([bad])

    def test_unexpected_analytics_shape_fails(self):
        with self.assertRaises(ValueError):
            live.read(NOW, FakeClient([GOOD_BRAND], rows=None))

    def test_reauth_propagates(self):
        class Dead:
            def call(self, *a):
                raise mcp.ReauthRequired("expired")
        with self.assertRaises(mcp.ReauthRequired):
            live.read(NOW, Dead())


class RefreshRunnerTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        p = mock.patch.dict(os.environ, {"SOCIAL_STATE_DIR": str(self.dir)})
        p.start()
        self.addCleanup(p.stop)

    def test_lock_blocks_second_worker_and_recovers_from_stale_pid(self):
        first = refresh.acquire_lock()
        self.assertIsNotNone(first)
        self.assertIsNone(refresh.acquire_lock())
        first.write_text("99999999")  # dead pid after a crash/reboot
        again = refresh.acquire_lock()
        self.assertIsNotNone(again)
        again.unlink()

    def test_reauth_sets_flag_and_does_not_retry(self):
        with mock.patch.object(refresh, "attempt", return_value=2) as a, mock.patch.object(refresh.time, "sleep"):
            self.assertEqual(refresh.main([]), 2)
        self.assertEqual(a.call_count, 1)
        status = json.loads((self.dir / "status.json").read_text())
        self.assertTrue(status["reauth_required"])
        self.assertIn("last_success", status)  # other sources still collected

    def test_transient_failure_retries_then_succeeds(self):
        with mock.patch.object(refresh, "attempt", side_effect=[1, 0]) as a, mock.patch.object(refresh.time, "sleep"):
            self.assertEqual(refresh.main([]), 0)
        self.assertEqual(a.call_count, 2)
        self.assertIn("last_success", json.loads((self.dir / "status.json").read_text()))

    def test_publish_failure_is_recorded_in_status(self):
        with mock.patch.object(refresh, "attempt", return_value=0), mock.patch.object(refresh, "publish", return_value=4):
            self.assertEqual(refresh.main(["--no-retry", "--publish"]), 4)
        status = json.loads((self.dir / "status.json").read_text())
        self.assertEqual(status["last_exit_code"], 4)
        self.assertFalse(status["last_publish_ok"])
        self.assertIn("last_success", status)  # collection itself worked

    def test_lock_released_after_run(self):
        with mock.patch.object(refresh, "attempt", return_value=0):
            refresh.main(["--no-retry"])
        self.assertFalse((self.dir / "refresh.lock").exists())


class PublicArtifactTests(unittest.TestCase):
    def test_reader_copies_identical(self):
        a = (ROOT / "scripts/research/gpt_social_reader.mjs").read_bytes()
        b = (ROOT / "redes-sociales/gpt_social_reader.mjs").read_bytes()
        self.assertEqual(a, b)

    def test_public_json_has_no_private_ids(self):
        text = (ROOT / "redes-sociales/social-metrics.json").read_text(encoding="utf-8")
        for needle in ("brandId", "access_token", "refresh_token", "client_id", "Bearer"):
            self.assertNotIn(needle, text)


class ReauthKeepsSnapshotTests(unittest.TestCase):
    def test_expired_metricool_login_keeps_last_good_and_exits_2(self):
        import gpt_social_snapshot as snap
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        out = d / "m.json"
        # A live snapshot may have no Threads sample, or have a newer date.
        # Seed the actual contract with a known, unexpired last-good value.
        previous = snap.compose.compose([{
            "id": "threads", "source": "metricool-mcp-export", "status": "ok",
            "followers": 13, "observed_at": "2026-10-22",
        }], now=NOW)
        out.write_text(json.dumps(previous), encoding="utf-8")
        def dead(now):
            raise mcp.ReauthRequired("expired")
        with mock.patch.object(snap.metricool_live, "read", dead):
            rc = snap.main(["--output", str(out), "--metricool-live", "--bluesky-fixture",
                            str(ROOT / "tests/fixtures/social/bluesky_profile.fixture.json"),
                            "--mastodon-fixture", str(ROOT / "tests/fixtures/social/mastodon_search.fixture.json"),
                            "--now", "2026-10-23T18:00:00Z"])
        self.assertEqual(rc, 2)
        kept = {n["id"]: n["status"] for n in json.loads(out.read_text(encoding="utf-8"))["networks"]}
        self.assertEqual(kept["threads"], "ok")  # last-good Metricool value preserved


if __name__ == "__main__":
    unittest.main()
