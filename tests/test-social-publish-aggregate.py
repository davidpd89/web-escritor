"""A forged aggregate must not be pushed even when six row IDs are present."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/research'))
import gpt_social_publish as pub

NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


class AggregateContractTests(unittest.TestCase):
    def test_total_coverage_and_deadline_derive_from_rows(self):
        sample = json.loads((ROOT / 'redes-sociales/social-metrics.json').read_text(encoding='utf-8'))
        for field, value in [('follower_relationships', 999999), ('coverage', 99),
                             ('eligible', 99), ('valid_until', '2099-01-01T00:00:00Z')]:
            with self.subTest(field=field):
                forged = json.loads(json.dumps(sample))
                forged['totals'][field] = value
                with self.assertRaises(pub.PublishError):
                    pub.validate(json.dumps(forged), NOW)


if __name__ == '__main__':
    unittest.main()
