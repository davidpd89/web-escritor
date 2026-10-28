import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/research'))
import gpt_social_publish as publisher


class SocialPublisherProfileIntegrity(unittest.TestCase):
    def test_publisher_rejects_substituted_profile(self):
        path = ROOT / 'redes-sociales/social-metrics.json'
        original = json.loads(path.read_text(encoding='utf-8'))
        now = datetime(2026, 10, 25, 12, tzinfo=timezone.utc)
        self.assertIsInstance(publisher.validate(json.dumps(original), now), dict, f'{path}: snapshot real rechazado')
        altered = json.loads(json.dumps(original))
        altered['networks'][0]['profile_url'] = original['networks'][1]['profile_url']
        with self.assertRaises(publisher.PublishError, msg=f'{path}: se acepta un perfil sustituido'):
            publisher.validate(json.dumps(altered), now)


if __name__ == '__main__':
    unittest.main()
