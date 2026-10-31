"""Offline regression suite for three-source public social contract."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1] / "scripts/research/gpt_social_compose.py"
_spec = importlib.util.spec_from_file_location("gpt_social_compose", SRC)
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)
NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


def bsky(**patch):
    return {"id": "bluesky", "profile_url": sc.PROFILES["bluesky"],
            "followers": 11, "source": "bluesky-public-appview", "status": "ok",
            "observed_at": "2026-10-22T11:00:00Z", **patch}


def threads(**patch):
    return {"id": "threads", "followers": 7, "source": "metricool-mcp-export",
            "status": "ok", "observed_at": "2026-10-21", **patch}


def mastodon(**patch):
    return {"id": "mastodon", "profile_url": sc.PROFILES["mastodon"],
            "followers": 0, "source": "mastodon-public-search", "status": "ok",
            "observed_at": "2026-10-22T10:00:00Z", **patch}



def metricool_batch(include_threads=True):
    # Literal shape emitted by #705; numbers intentionally synthetic.
    records = []
    for key in ("bluesky", "threads", "instagram", "facebook", "tiktok",
                "pinterest", "youtube", "twitter"):
        if key == "threads" and not include_threads:
            continue
        records.append({
            "id": key, "followers": 13 if key == "threads" else 100,
            "views_30d": None, "impressions_30d": None,
            "observed_at": "2026-10-21", "source": "metricool-mcp-export",
            "status": "ok",
        })
    return {"kind": "metricool-follower-candidates", "schema_version": 1,
            "requested_day": "2026-10-21", "generated_at": "2026-10-22T11:30:00Z",
            "records": records}


class ComposeTests(unittest.TestCase):
    def test_batch_counts_only_five_verified_metricool_profiles(self):
        public = sc.compose([metricool_batch()], now=NOW)
        self.assertEqual(public["totals"]["coverage"], 5)
        self.assertEqual(public["totals"]["follower_relationships"], 413)
        self.assertEqual(public["networks"][2]["id"], "threads")
        self.assertTrue(all(x["followers"] is None for x in public["networks"][:2]))
        self.assertEqual([r["id"] for r in public["networks"][3:]],
                         ["instagram", "tiktok", "pinterest", "facebook", "x"])
        self.assertIsNone(public["networks"][-1]["followers"])  # Metricool "twitter" is not X

    def test_bundle_and_public_readers_do_not_double_count_bluesky(self):
        public = sc.compose([metricool_batch(), bsky(), mastodon()], now=NOW)
        self.assertEqual(public["totals"]["coverage"], 7)
        self.assertEqual(public["totals"]["follower_relationships"], 424)

    def test_batch_without_threads_does_not_extend_public_account_list(self):
        public = sc.compose([metricool_batch(include_threads=False)], now=NOW)
        self.assertEqual(public["totals"]["coverage"], 4)
        self.assertEqual(public["totals"]["eligible"], 8)

    def test_batch_duplicate_candidate_rejected(self):
        batch = metricool_batch()
        batch["records"].append(batch["records"][1].copy())
        with self.assertRaisesRegex(ValueError, "Duplicate Metricool candidate"):
            sc.compose([batch], now=NOW)

    def test_batch_wrong_provider_rejected_even_when_ignored(self):
        batch = metricool_batch()
        batch["records"][0]["source"] = "other-provider"
        with self.assertRaisesRegex(ValueError, "unexpected provider"):
            sc.compose([batch], now=NOW)

    def test_batch_wrong_day_rejected(self):
        batch = metricool_batch()
        batch["records"][1]["observed_at"] = "2026-10-20"
        with self.assertRaisesRegex(ValueError, "date differs"):
            sc.compose([batch], now=NOW)

    def test_batch_with_unverified_impressions_rejected(self):
        batch = metricool_batch()
        batch["records"][0]["impressions_30d"] = 120
        with self.assertRaisesRegex(ValueError, "Unverified period"):
            sc.compose([batch], now=NOW)

    def test_batch_malformed_schema_rejected(self):
        for key, value in (("schema_version", True),
                           ("requested_day", "2026-02-30"),
                           ("records", "not-an-array")):
            batch = metricool_batch()
            batch[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                sc.compose([batch], now=NOW)

    def test_batch_and_direct_threads_duplication_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate network ID"):
            sc.compose([metricool_batch(), threads()], now=NOW)

    def test_no_publish_when_batch_has_only_unapproved_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "batch.json"
            target = Path(tmp) / "last-good.json"
            batch = metricool_batch(include_threads=False)
            batch["records"] = [r for r in batch["records"]
                                if r["id"] in ("bluesky", "youtube", "twitter")]
            src.write_text(json.dumps(batch), encoding="utf-8")
            target.write_text('{"old": true}', encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(sc.main([str(src), "--output", str(target)]), 1)
            self.assertEqual(json.loads(target.read_text()), {"old": True})

    def test_profiles_aggregate_with_three_sources_and_pending_others(self):
        result = sc.compose([threads(), bsky(), mastodon()], now=NOW)
        self.assertEqual(result["totals"]["follower_relationships"], 18)
        self.assertEqual(result["totals"]["coverage"], 3)
        self.assertEqual(result["totals"]["eligible"], 8)
        self.assertEqual([r["id"] for r in result["networks"]], list(sc.PROFILES))
        self.assertEqual(result["generated_at"], "2026-10-22T12:00:00Z")

    def test_no_sources_no_fake_zero(self):
        result = sc.compose([], now=NOW)
        self.assertIsNone(result["totals"]["follower_relationships"])
        self.assertEqual(result["totals"]["coverage"], 0)
        self.assertTrue(all(x["status"] == "pending" for x in result["networks"]))

    def test_zero_is_fresh_observation(self):
        result = sc.compose([mastodon()], now=NOW)
        self.assertEqual(result["totals"]["follower_relationships"], 0)
        self.assertEqual(result["totals"]["coverage"], 1)

    def test_null_never_converted_to_zero(self):
        source = threads()
        source["followers"] = None
        source["observed_at"] = None
        source["status"] = "partial"
        result = sc.compose([source], now=NOW)
        self.assertEqual(result["networks"][2]["status"], "pending")
        self.assertIsNone(result["totals"]["follower_relationships"])

    def test_date_in_madrid_maps_to_end_of_reporting_day(self):
        instant = sc.observed_utc("2026-10-21")
        self.assertEqual(instant.date().isoformat(), "2026-10-21")
        self.assertEqual(instant.hour, 21)  # Madrid UTC+2 (October 21)

    def test_madrid_daylight_saving_transition(self):
        self.assertEqual(sc.observed_utc("2026-10-25").hour, 22)  # UTC+1 after transition

    def test_48_hour_boundary_is_inclusive(self):
        cutoff = (NOW - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
        src = bsky()
        src["observed_at"] = cutoff
        self.assertEqual(sc.compose([src], now=NOW)["totals"]["coverage"], 1)

    def test_stale_is_not_in_total_or_public_number(self):
        src = bsky()
        src["observed_at"] = "2026-10-18T10:00:00Z"
        result = sc.compose([src, threads()], now=NOW)
        self.assertEqual(result["totals"]["follower_relationships"], 7)
        self.assertEqual(result["totals"]["coverage"], 1)
        self.assertEqual(result["networks"][0]["status"], "stale")
        self.assertIsNone(result["networks"][0]["followers"])

    def test_reject_current_madrid_unfinished_day(self):
        src = threads()
        src["observed_at"] = "2026-10-22"
        with self.assertRaisesRegex(ValueError, "future-dated"):
            sc.compose([src], now=NOW)

    def test_reject_ambiguous_timezone(self):
        src = bsky()
        src["observed_at"] = "2026-10-22T11:00:00"
        with self.assertRaisesRegex(ValueError, "explicit timezone"):
            sc.compose([src], now=NOW)

    def test_reject_bad_timestamp(self):
        src = bsky()
        src["observed_at"] = "yesterday"
        with self.assertRaises(ValueError):
            sc.compose([src], now=NOW)

    def test_reject_unknown_network(self):
        src = bsky()
        src["id"] = "unknown"
        with self.assertRaises(ValueError):
            sc.compose([src], now=NOW)

    def test_reject_url_impersonation(self):
        src = bsky()
        src["profile_url"] = "https://evil.example/"
        with self.assertRaises(ValueError):
            sc.compose([src], now=NOW)

    def test_reject_duplicate_accounts(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            sc.compose([bsky(), bsky()], now=NOW)

    def test_reject_bool_negative_float(self):
        for value in (True, False, -1, 1.25, "9"):
            src = bsky()
            src["followers"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                sc.compose([src], now=NOW)

    def test_reject_unverified_views(self):
        for key in sc.UNVERIFIED_PERIOD_FIELDS:
            src = bsky()
            src[key] = 100
            with self.subTest(metric=key), self.assertRaises(ValueError):
                sc.compose([src], now=NOW)

    def test_reject_missing_source(self):
        src = bsky()
        src.pop("source")
        with self.assertRaises(ValueError):
            sc.compose([src], now=NOW)

    def test_reject_wrong_provider_for_network(self):
        src = bsky()
        src["source"] = "metricool-mcp-export"
        with self.assertRaisesRegex(ValueError, "wrong provider"):
            sc.compose([src], now=NOW)

    def test_reject_invalid_status(self):
        src = bsky()
        src["status"] = "ok-nope"
        with self.assertRaises(ValueError):
            sc.compose([src], now=NOW)

    def test_reject_number_without_date(self):
        src = bsky()
        src["observed_at"] = None
        with self.assertRaises(ValueError):
            sc.compose([src], now=NOW)

    def test_output_omits_private_id_fields(self):
        src = bsky()
        src["did"] = "did:plc:not-published"
        src["account_id"] = "private"
        src["access_token"] = "secret"
        result = json.dumps(sc.compose([src], now=NOW))
        self.assertNotIn("secret", result)
        self.assertNotIn("did:plc", result)
        self.assertNotIn("private", result)

    def test_preserve_last_good_on_source_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "public.json"
            old.write_text('{"old":true}', encoding="utf-8")
            incoming = Path(tmp) / "invalid.json"
            src = bsky()
            src["followers"] = -1
            incoming.write_text(json.dumps(src), encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(sc.main([str(incoming), "--output", str(old)]), 1)
            self.assertEqual(json.loads(old.read_text()), {"old": True})

    def test_no_sources_never_overwrite_previous_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "public.json"
            old.write_text('{"old":true}', encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(sc.main(["--output", str(old)]), 1)
            self.assertEqual(json.loads(old.read_text()), {"old": True})

    def test_publication_cannot_overwrite_input_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp) / "source.json"
            old.write_text(json.dumps(bsky()), encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(sc.main([str(old), "--output", str(old)]), 1)
            self.assertEqual(json.loads(old.read_text())["id"], "bluesky")

    def test_atomic_write_good_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "json" / "metrics.json"
            sc.atomic_write(file, sc.compose([threads()], now=NOW))
            payload = json.loads(file.read_text(encoding="utf-8"))
            self.assertEqual(payload["totals"]["follower_relationships"], 7)

    def test_cli_no_sources_safe_stdout(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(sc.main([]), 0)
        output = json.loads(buf.getvalue())
        self.assertEqual(output["totals"]["coverage"], 0)

    def test_source_output_from_real_child_shapes(self):
        src1 = {"id": "bluesky", "profile_url": sc.PROFILES["bluesky"], "handle": "h", "did": "did:plc:test",
                "followers": 9, "posts": 20, "views_30d": None, "impressions_30d": None,
                "interactions_30d": None, "observed_at": "2026-10-22T11:00:00Z",
                "source": "bluesky-public-appview", "status": "ok"}
        src2 = {"id": "threads", "followers": 6, "views_30d": None, "impressions_30d": None,
                "observed_at": "2026-10-21", "source": "metricool-mcp-export", "status": "ok"}
        result = sc.compose([src1, src2], now=NOW)
        self.assertEqual(result["totals"]["follower_relationships"], 15)
        self.assertEqual(result["totals"]["coverage"], 2)


if __name__ == "__main__":
    unittest.main()
