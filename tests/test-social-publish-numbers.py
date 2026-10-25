"""The publisher must reject numeric values that JavaScript cannot safely display."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/research'))
import gpt_social_publish as pub
import gpt_social_compose as compose

NOW = datetime(2026, 10, 23, 12, tzinfo=timezone.utc)


def payload():
    stamp = NOW.isoformat().replace('+00:00', 'Z')
    expiry = (NOW + timedelta(hours=24)).isoformat().replace('+00:00', 'Z')
    return {'schema_version': 1, 'generated_at': stamp,
            'networks': [{'id': name, 'followers': 2, 'status': 'ok',
                          'source': compose.EXPECTED_SOURCES[name],
                          'profile_url': compose.PROFILES[name],
                          'observed_at': stamp, 'valid_until': expiry}
                         for name in sorted(pub.NETWORKS)],
            'totals': {'follower_relationships': 12, 'valid_until': expiry}}


class NumberContractTests(unittest.TestCase):
    def test_bools_floats_and_unsafe_integers_fail_closed(self):
        for value in (True, False, 1.0, 1.5, -1, 2**53, 10**30):
            with self.subTest(value=value):
                sample = payload()
                sample['networks'][0]['followers'] = value
                with self.assertRaises(pub.PublishError):
                    pub.validate(json.dumps(sample), NOW)


if __name__ == '__main__':
    unittest.main()
