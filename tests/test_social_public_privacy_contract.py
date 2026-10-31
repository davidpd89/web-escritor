import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'redes-sociales/social-metrics.json'


class PublicSocialPrivacyContract(unittest.TestCase):
    def test_public_json_has_only_approved_fields(self):
        data = json.loads(PUBLIC.read_text(encoding='utf-8'))
        self.assertEqual(set(data), {'schema_version', 'generated_at', 'networks', 'totals'}, str(PUBLIC))
        allowed_network = {'id', 'profile_url', 'followers', 'observed_at', 'valid_until', 'source', 'status'}
        allowed_totals = {'follower_relationships', 'valid_until', 'coverage', 'eligible', 'label'}
        self.assertEqual(set(data['totals']), allowed_totals, f'{PUBLIC}: campos agregados no autorizados')
        self.assertEqual(len(data['networks']), 8, f'{PUBLIC}: número de redes inesperado')
        for network in data['networks']:
            self.assertEqual(set(network), allowed_network, f'{PUBLIC}: campos no públicos en {network.get("id")}')
            self.assertIsInstance(network['profile_url'], str)
            self.assertTrue(network['profile_url'].startswith('https://'), f'{PUBLIC}: perfil inseguro en {network["id"]}')


if __name__ == '__main__':
    unittest.main()
