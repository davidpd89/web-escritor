"""Regression contract: a rating-only change must be eligible for daily PR+deploy."""
import ast
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RatingWorkflowContract(unittest.TestCase):
    def test_market_json_is_allowed_by_generated_only_publisher(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("reading_publisher_rating_contract",
            ROOT / "scripts/publish-reading-refresh.py")
        # importing this module needs gh internals but no network.
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(module.allowed_path("assets/reading-market.json"))
        self.assertFalse(module.allowed_path("assets/other-secrets.json"))

    def test_rating_refresh_is_before_no_new_books_exit(self):
        src = (ROOT / "scripts/refresh-reading-catalogue.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        self.assertIn("refresh_ratings(", src)
        self.assertIn("or changed_ratings", src)
        self.assertIn("assets/reading-market.json", src)
        self.assertLess(src.find("refresh_ratings("), src.find("or changed_ratings"))
        self.assertNotIn("if not publish or not (report['new_books']", src)

    def test_publish_stages_only_existing_paths(self):
        # Sync 41755229440: sin libros en cuarentena no hay data/reading-quarantine.json y git add abortaba la carga.
        src = (ROOT / "scripts/refresh-reading-catalogue.py").read_text(encoding="utf-8")
        self.assertIn("command('git', 'add', '--', *[p for p in staged if (ROOT / p).exists()])", src)
        self.assertNotIn("command('git', 'add', '--', 'assets/page-order.generated.js'", src)

    def test_daily_sync_has_optional_credentials_and_no_extra_workflow(self):
        yaml = (ROOT / ".github/workflows/reading-catalogue-sync.yml").read_text(encoding="utf-8")
        # Una sola carga nocturna (06/11: los 8 cron diarios ocupaban Actions de día); se encadena hasta las 06.
        self.assertIn("cron: '17 0 * * *'", yaml)
        self.assertIn("schedule:'17 0 * * *':*", yaml)
        self.assertEqual(yaml.count("- cron:"), 1)
        self.assertIn("TZ=Europe/Madrid", yaml)
        # GitHub drops crons: a night batch that published books dispatches the next one.
        self.assertIn("name: Chain the next night batch", yaml)
        self.assertIn("gh workflow run reading-catalogue-sync.yml", yaml)
        self.assertIn('[ "$hour" -lt 6 ] && [ "$accepted" -gt 0 ]', yaml)
        # refresh-reading-catalogue.py writes the ingest report: the count lives under "stats".
        self.assertIn(".get('stats',{}).get('accepted',0)", yaml)
        self.assertIn("!inputs.dry_run", yaml)
        self.assertIn("secrets.GOOGLE_BOOKS_API_KEY", yaml)
        self.assertIn("secrets.HARDCOVER_API_KEY", yaml)
        config = json.loads((ROOT / "data/reading-intake-config.json").read_text(encoding="utf-8"))
        self.assertTrue(config["ratings_refresh"]["enabled"])
        self.assertLessEqual(config["ratings_refresh"]["google_books_requests_per_day"], 100)
        self.assertLessEqual(config["ratings_refresh"]["hardcover_requests_per_day"], 100)
        self.assertEqual(config["amazon_partner_tag"], "davidporto-21")


if __name__ == "__main__":
    unittest.main()
