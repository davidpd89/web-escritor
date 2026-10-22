"""Run offline: python -m unittest discover -s tests -p test_gpt_metricool_threads.py -v"""
import importlib.util
import io
from datetime import date, timedelta
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

SOURCE = Path(__file__).resolve().parents[1] / "scripts/research/gpt_metricool_threads.py"
spec = importlib.util.spec_from_file_location("gpt_metricool_threads", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
START = date(2026, 9, 22)
END = START + timedelta(days=29)


def fixture():
    return {"metrics": ["THEV01", "THEV06"], "from": START.isoformat(), "to": END.isoformat(),
            "rows": [[str(100+i)+".0", str(i)+".0", (START+timedelta(days=i)).strftime("%Y%m%d")]
                     for i in range(30)][::-1]}


class MetricoolTests(unittest.TestCase):
    def test_unsorted_rows_last_and_suppressed_views(self):
        got=module.normalize(fixture())
        self.assertEqual(got["followers"],129)
        self.assertIsNone(got["views_30d"])
        self.assertEqual(got["coverage"]["days_with_post_views"],30)
        self.assertIn("not verified as views generated",got["views_not_published_reason"])
        self.assertEqual(got["status"],"ok")
        self.assertEqual(got["observed_at"],END.isoformat())

    def test_complete_view_rows_still_not_reported_as_30d(self):
        got=module.normalize(fixture())
        self.assertEqual(got["status"],"ok")
        self.assertIsNone(got["views_30d"])

    def test_zero_and_string(self):
        self.assertEqual(module.count("0.0"),0)
        self.assertEqual(module.count(0),0)

    def test_null(self):
        self.assertIsNone(module.count(None))

    def test_numeric_rejections(self):
        for value in (True, False, 1.2, "1.5", "NaN", "Infinity", "-1", "oops", [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError): module.count(value)

    def test_missing_day_incomplete(self):
        raw=fixture();raw["rows"].pop(4)
        got=module.normalize(raw)
        self.assertIsNone(got["views_30d"])
        self.assertEqual(got["coverage"]["days_with_post_views"],29)

    def test_null_views_incomplete(self):
        raw=fixture();raw["rows"][5][1]=None
        self.assertIsNone(module.normalize(raw)["views_30d"])

    def test_no_last_followers(self):
        raw=fixture();raw["rows"][0][0]=None
        self.assertIsNone(module.normalize(raw)["followers"])

    def test_bad_metric_order(self):
        raw=fixture();raw["metrics"].reverse()
        with self.assertRaises(ValueError):module.normalize(raw)

    def test_bad_window(self):
        raw=fixture();raw["to"]=(END+timedelta(days=1)).isoformat()
        with self.assertRaises(ValueError):module.normalize(raw)

    def test_duplicate_dates(self):
        raw=fixture();raw["rows"].append(raw["rows"][0])
        with self.assertRaises(ValueError):module.normalize(raw)

    def test_bad_date(self):
        raw=fixture();raw["rows"][0][-1]="2026-10-21"
        with self.assertRaises(ValueError):module.normalize(raw)

    def test_bad_row_shape(self):
        raw=fixture();raw["rows"][1]=["1", "20261021"]
        with self.assertRaises(ValueError):module.normalize(raw)

    def test_bad_wrapper(self):
        raw=fixture();raw["blogId"]="private"
        with self.assertRaises(ValueError):module.normalize(raw)

    def test_cli_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"raw.json"
            file.write_text(json.dumps(fixture()),encoding="utf-8")
            stdout=io.StringIO()
            with redirect_stdout(stdout): self.assertEqual(module.main([str(file)]),0)
            self.assertEqual(json.loads(stdout.getvalue())["followers"],129)

    def test_cli_bad_no_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"raw.json"
            file.write_text("BAD JSON",encoding="utf-8")
            with redirect_stderr(io.StringIO()): self.assertEqual(module.main([str(file)]),1)


if __name__ == "__main__":
    unittest.main()
