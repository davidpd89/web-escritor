"""Do not publish snapshots generated in the future or long before the claimed lifetime."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/research'))
import gpt_social_publish as pub

NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


class PublisherClockTests(unittest.TestCase):
    def test_generated_at_cannot_be_from_future_or_ancient_past(self):
        source = json.loads((ROOT / 'redes-sociales/social-metrics.json').read_text(encoding='utf-8'))
        for stamp in ('2035-01-01T00:00:00Z', '2020-01-01T00:00:00Z', 'not-a-date'):
            with self.subTest(stamp=stamp):
                item = json.loads(json.dumps(source))
                item['generated_at'] = stamp
                with self.assertRaises(pub.PublishError):
                    pub.validate(json.dumps(item), NOW)


if __name__ == '__main__':
    unittest.main()
