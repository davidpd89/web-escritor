"""Offline contract tests for the single-metric Metricool Threads importer."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

SOURCE = Path(__file__).resolve().parents[1] / "scripts/research/gpt_metricool_threads.py"
spec = importlib.util.spec_from_file_location("gpt_metricool_threads", SOURCE)
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


def fixture():
    return {"metrics": ["THEV01"], "from": "2026-10-21", "to": "2026-10-21",
            "rows": [["123456.0", "20261021"]]}


class MetricoolThreadsContractTests(unittest.TestCase):
    def test_real_mcp_one_day_shape(self):
        result = importer.normalize(fixture())
        self.assertEqual(result["followers"], 123456)
        self.assertEqual(result["observed_at"], "2026-10-21")
        self.assertEqual(result["source"], "metricool-mcp-export")
        self.assertEqual(result["status"], "ok")
        self.assertIsNone(result["views_30d"])

    def test_null_followers_are_not_zero(self):
        data = fixture()
        data["rows"][0][0] = None
        result = importer.normalize(data)
        self.assertIsNone(result["followers"])
        self.assertIsNone(result["observed_at"])
        self.assertEqual(result["status"], "partial")

    def test_no_data_is_partial(self):
        data = fixture()
        data["rows"] = []
        self.assertIsNone(importer.normalize(data)["followers"])

    def test_zero_is_valid(self):
        data = fixture()
        data["rows"][0][0] = "0.0"
        self.assertEqual(importer.normalize(data)["followers"], 0)

    def test_decimal_string_is_exact(self):
        self.assertEqual(importer.count("000123456.000"), 123456)
        self.assertEqual(importer.count(123456), 123456)

    def test_invalid_numeric_values_fail(self):
        for bad in (True, False, -1, "1.5", "NaN", "Infinity", "", "x", 2.3, [], {}, "9"*65):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                importer.count(bad)

    def test_wrong_metric_is_rejected(self):
        data = fixture()
        data["metrics"] = ["THEV06"]
        with self.assertRaises(ValueError):
            importer.normalize(data)

    def test_even_extra_metric_is_rejected(self):
        data = fixture()
        data["metrics"] = ["THEV01", "THEV06"]
        data["rows"][0].insert(1, "15.0")
        with self.assertRaises(ValueError):
            importer.normalize(data)

    def test_extra_private_fields_not_accepted(self):
        data = fixture()
        data["brandId"] = "private-do-not-publish"
        with self.assertRaises(ValueError):
            importer.normalize(data)

    def test_multi_day_input_is_rejected(self):
        data = fixture()
        data["from"] = "2026-10-20"
        with self.assertRaises(ValueError):
            importer.normalize(data)

    def test_duplicate_rows_rejected(self):
        data = fixture()
        data["rows"].append(["234.0", "20261021"])
        with self.assertRaises(ValueError):
            importer.normalize(data)

    def test_wrong_date_in_row_rejected(self):
        data = fixture()
        data["rows"][0][1] = "20261020"
        with self.assertRaises(ValueError):
            importer.normalize(data)

    def test_invalid_calendar_day_rejected(self):
        data = fixture()
        data["from"] = data["to"] = "2026-02-30"
        with self.assertRaises(ValueError):
            importer.normalize(data)

    def test_bad_rows_rejected(self):
        for bad in (None, 20, {}, "rows", [123], [["222.0"]], [["222.0", 20261021]]):
            data = fixture()
            data["rows"] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                importer.normalize(data)

    def test_views_are_always_missing(self):
        data = fixture()
        result = importer.normalize(data)
        self.assertIsNone(result["views_30d"])
        self.assertIsNone(result["impressions_30d"])

    def test_cli_does_not_write_public_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "private.json"
            raw.write_text(json.dumps(fixture()), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(importer.main([str(raw)]), 0)
            result = json.loads(stdout.getvalue())
            self.assertEqual(result["followers"], 123456)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["private.json"])

    def test_cli_rejects_bad_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "private.json"
            raw.write_text("INVALID JSON", encoding="utf-8")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(importer.main([str(raw)]), 1)


if __name__ == "__main__":
    unittest.main()
