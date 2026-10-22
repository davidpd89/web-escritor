"""No-network tests for an eight-field Metricool one-day MCP result."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1] / "scripts" / "research"
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("gpt_metricool_followers", HERE / "gpt_metricool_followers.py")
mf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mf)
IDS = list(mf.FIELDS)


def fixture():
    # Deliberately synthetic values, NOT the linked Metricool account.
    return {
        "metrics": IDS[:],
        "from": "2026-10-21",
        "to": "2026-10-21",
        "rows": [[str(1000 + i) + ".0" for i in range(len(IDS))] + ["20261021"]],
    }


class MultiNetworkFollowerTests(unittest.TestCase):
    def test_eight_fields_in_one_real_shape(self):
        result = mf.normalize(fixture())
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(len(result["records"]), 8)
        self.assertEqual([v["id"] for v in result["records"]], list(mf.FIELDS.values()))
        self.assertEqual([v["followers"] for v in result["records"]], list(range(1000, 1008)))
        self.assertTrue(all(v["status"] == "ok" for v in result["records"]))

    def test_reverse_field_order_is_mapped_by_explicit_ids(self):
        raw = fixture()
        raw["metrics"].reverse()
        raw["rows"][0][:-1] = raw["rows"][0][:-1][::-1]
        self.assertEqual({r["id"]: r["followers"] for r in mf.normalize(raw)["records"]},
                         dict(zip(mf.FIELDS.values(), range(1000, 1008))))

    def test_one_field_compatible_with_existing_threads_reader(self):
        raw = {"metrics": ["THEV01"], "from": "2026-10-21", "to": "2026-10-21",
               "rows": [["2001.0", "20261021"]]}
        record = mf.normalize(raw)["records"][0]
        self.assertEqual((record["id"], record["followers"], record["source"]),
                         ("threads", 2001, "metricool-mcp-export"))
        self.assertIsNone(record["views_30d"])

    def test_a_null_does_not_invalidate_seven_good_followers(self):
        raw = fixture()
        raw["rows"][0][3] = None
        records = mf.normalize(raw)["records"]
        self.assertIsNone(records[3]["followers"])
        self.assertEqual(records[3]["status"], "partial")
        self.assertEqual(sum(r["status"] == "ok" for r in records), 7)

    def test_zero_is_real_count(self):
        raw = fixture()
        raw["rows"][0][2] = "0.0"
        record = mf.normalize(raw)["records"][2]
        self.assertEqual(record["followers"], 0)
        self.assertEqual(record["status"], "ok")

    def test_empty_rows_yield_partial_not_fake_zero(self):
        raw = fixture()
        raw["rows"] = []
        records = mf.normalize(raw)["records"]
        self.assertTrue(all(r["followers"] is None for r in records))

    def test_unverified_period_metrics_rejected(self):
        for field in ("THEV06", "IGEV05", "TKEV02", "FBEV49", "THEV05"):
            with self.subTest(field=field):
                raw = fixture()
                raw["metrics"][0] = field
                with self.assertRaises(ValueError):
                    mf.normalize(raw)

    def test_duplicate_field_rejected(self):
        raw = fixture()
        raw["metrics"][1] = raw["metrics"][0]
        with self.assertRaises(ValueError):
            mf.normalize(raw)

    def test_missing_field_list_rejected(self):
        for fields in ([], None, "THEV01", [True]):
            with self.subTest(fields=fields):
                raw = fixture()
                raw["metrics"] = fields
                with self.assertRaises(ValueError):
                    mf.normalize(raw)

    def test_extra_private_metadata_rejected(self):
        raw = fixture()
        raw["brandId"] = "private"
        with self.assertRaises(ValueError):
            mf.normalize(raw)

    def test_bad_row_width_fails_closed(self):
        for rows in ([["1000.0", "20261021"]], [123], ["text"]):
            with self.subTest(rows=rows):
                raw = fixture()
                raw["rows"] = rows
                with self.assertRaises(ValueError):
                    mf.normalize(raw)

    def test_duplicate_day_rejected(self):
        raw = fixture()
        raw["rows"].append(raw["rows"][0][:])
        with self.assertRaises(ValueError):
            mf.normalize(raw)

    def test_mismatched_reporting_day_rejected(self):
        raw = fixture()
        raw["rows"][0][-1] = "20261020"
        with self.assertRaises(ValueError):
            mf.normalize(raw)

    def test_multiday_export_rejected(self):
        raw = fixture()
        raw["from"] = "2026-10-20"
        with self.assertRaises(ValueError):
            mf.normalize(raw)

    def test_invalid_counter_rejected_without_partial_publication(self):
        for bad in (True, -2, "NaN", "3.5", float("inf")):
            with self.subTest(bad=bad):
                raw = fixture()
                raw["rows"][0][4] = bad
                with self.assertRaises(ValueError):
                    mf.normalize(raw)

    def test_only_allowed_fields_appear_in_public_candidates(self):
        raw = fixture()
        raw["rows"][0][0] = "9000.0"
        result = json.dumps(mf.normalize(raw), ensure_ascii=False)
        self.assertNotIn("brandId", result)
        self.assertNotIn("access_token", result)
        self.assertNotIn("THEV06", result)

    def test_cli_real_file_only_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "private.json"
            path.write_text(json.dumps(fixture()), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(mf.main([str(path)]), 0)
            self.assertEqual(len(json.loads(out.getvalue())["records"]), 8)
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ["private.json"])

    def test_cli_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "private.json"
            path.write_text("invalid", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(mf.main([str(path)]), 1)


if __name__ == "__main__":
    unittest.main()
