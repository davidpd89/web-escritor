"""Offline tests for the same-day public profile reader and its merge into the snapshot."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "research"))
import gpt_social_compose as compose  # noqa: E402
import gpt_social_public as public  # noqa: E402
import gpt_social_snapshot as snap  # noqa: E402

NOW = datetime(2026, 10, 31, 9, 0, tzinfo=timezone.utc)


def live(network, followers):
    return {"id": network, "source": public.source_name(network), "status": "ok",
            "followers": followers, "observed_at": "2026-10-31T09:00:00Z"}


def batch(**followers):
    return {"kind": compose.METRICOOL_BATCH_KIND, "schema_version": 1, "requested_day": "2026-10-29",
            "generated_at": "2026-10-31T08:59:00Z",
            "records": [{"id": k, "followers": v, "source": "metricool-mcp-export", "status": "ok",
                         "observed_at": "2026-10-29"} for k, v in followers.items()]}


class ExactCountTests(unittest.TestCase):
    def test_spanish_separators(self):
        for text, expected in (("2.069 seguidores", 2069), ("2,069 seguidores", 2069),
                               ("1 192 seguidores", 1192), ("351 seguidores · 12 seguidos", 351),
                               ("12.345.678 seguidores", 12345678)):
            with self.subTest(text=text):
                self.assertEqual(public.exact_count(text), expected)

    def test_abbreviated_counts_are_not_exact(self):
        for text in ("2,1 mil seguidores", "1,2 M seguidores", "seguidores: muchos", ""):
            with self.subTest(text=text):
                self.assertIsNone(public.exact_count(text))

    def test_number_is_not_cut_from_a_longer_figure(self):
        self.assertIsNone(public.exact_count("2,5 mil seguidores"))


class ReaderTests(unittest.TestCase):
    def test_tiktok_requires_official_account(self):
        page = '{"uniqueId":"davidportoescritor","followerCount":1192},{"followerCount":9}'
        with mock.patch.object(public, "fetch", return_value=page):
            self.assertEqual(public.read_embedded("tiktok"), 1192)
        with mock.patch.object(public, "fetch", return_value='{"uniqueId":"other","followerCount":5}'):
            with self.assertRaisesRegex(ValueError, "official account"):
                public.read_embedded("tiktok")

    def test_pinterest_rejects_ambiguous_counts(self):
        with mock.patch.object(public, "fetch", return_value='"follower_count":8 "follower_count":8'):
            self.assertEqual(public.read_embedded("pinterest"), 8)
        with mock.patch.object(public, "fetch", return_value='"follower_count":8 "follower_count":90'):
            with self.assertRaisesRegex(ValueError, "ambiguous"):
                public.read_embedded("pinterest")

    def test_x_mirror_must_return_the_official_handle(self):
        ok = json.dumps({"user": {"screen_name": "DavidPortoDiaz", "followers": 137}})
        with mock.patch.object(public, "fetch", return_value=ok):
            self.assertEqual(public.read_x(), 137)
        for body in ({"user": {"screen_name": "someone", "followers": 137}},
                     {"user": {"screen_name": "davidportodiaz", "followers": "137"}}, {"code": 404}):
            with self.subTest(body=body), mock.patch.object(public, "fetch", return_value=json.dumps(body)):
                with self.assertRaises(ValueError):
                    public.read_x()

    def test_read_isolates_failures_per_network(self):
        def fake_fetch(url):
            if "tiktok" in url:
                raise OSError("timeout")
            if "fxtwitter" in url:
                return json.dumps({"user": {"screen_name": "davidportodiaz", "followers": 137}})
            return '"follower_count":8'
        errors = []
        with mock.patch.object(public, "fetch", side_effect=fake_fetch), \
                mock.patch.object(public, "read_rendered", return_value={"instagram": 2069}):
            records = public.read(NOW, errors)
        self.assertEqual({r["id"]: r["followers"] for r in records}, {"pinterest": 8, "x": 137, "instagram": 2069})
        self.assertTrue(all(r["source"] == f"{r['id']}-public-profile" for r in records))
        self.assertTrue(all(r["observed_at"] == "2026-10-31T09:00:00Z" for r in records))
        self.assertEqual(len(errors), 1)
        self.assertIn("tiktok", errors[0])

    def test_records_are_accepted_by_the_compositor(self):
        payload = compose.compose([live(n, 10) for n in compose.PROFILES if n not in ("bluesky", "mastodon")], now=NOW)
        self.assertEqual(payload["totals"]["coverage"], 6)
        self.assertNotIn("brandId", json.dumps(payload))


class PreferLiveTests(unittest.TestCase):
    def test_live_replaces_lagging_metricool_record(self):
        errors = []
        merged = snap.prefer_live(None, [batch(instagram=1993, tiktok=1186)], [live("instagram", 2069)], errors)
        self.assertEqual(errors, [])
        payload = compose.compose(merged, now=NOW)
        rows = {r["id"]: r for r in payload["networks"]}
        self.assertEqual(rows["instagram"]["followers"], 2069)
        self.assertEqual(rows["instagram"]["source"], "instagram-public-profile")
        self.assertEqual(rows["tiktok"]["source"], "metricool-mcp-export")

    def test_implausible_live_value_keeps_metricool(self):
        errors = []
        merged = snap.prefer_live(None, [batch(instagram=1993)], [live("instagram", 20)], errors)
        self.assertEqual(compose.compose(merged, now=NOW)["networks"][3]["followers"], 1993)
        self.assertIn("implausible", errors[0])

    def test_previous_snapshot_is_reference_when_metricool_is_missing(self):
        previous = {"networks": [{"id": "x", "followers": 137}]}
        errors = []
        self.assertEqual(snap.prefer_live(previous, [], [live("x", 9000)], errors), [])
        self.assertEqual(len(errors), 1)
        self.assertEqual(snap.prefer_live(previous, [], [live("x", 140)], []), [live("x", 140)])

    def test_batch_emptied_by_live_records_is_dropped(self):
        merged = snap.prefer_live(None, [batch(pinterest=8)], [live("pinterest", 8)], [])
        self.assertEqual(merged, [live("pinterest", 8)])


if __name__ == "__main__":
    unittest.main()
