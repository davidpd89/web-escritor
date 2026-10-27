"""An HTTPS URL is not sufficient proof of ownership of a social profile."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/research'))
import gpt_social_compose as compose
import gpt_social_publish as pub

NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)


class IdentityTests(unittest.TestCase):
    def test_every_network_url_is_canonical(self):
        source = json.loads((ROOT / 'redes-sociales/social-metrics.json').read_text(encoding='utf-8'))
        for entry in source['networks']:
            with self.subTest(network=entry['id']):
                forged = json.loads(json.dumps(source))
                bad = next(x for x in forged['networks'] if x['id'] == entry['id'])
                bad['profile_url'] = 'https://other.example/verified-looking'
                with self.assertRaises(pub.PublishError):
                    pub.validate(json.dumps(forged), NOW)
        self.assertEqual({x['id']: x['profile_url'] for x in source['networks']}, compose.PROFILES)


if __name__ == '__main__':
    unittest.main()
