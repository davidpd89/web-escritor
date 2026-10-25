import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / 'redes-sociales/social-metrics.json'
IDS = {'bluesky', 'mastodon', 'threads', 'instagram', 'tiktok', 'pinterest'}

class SocialPublicContract(unittest.TestCase):
    def test_published_snapshot_contract(self):
        data = json.loads(FILE.read_text(encoding='utf-8'))
        self.assertEqual(data['schema_version'], 1, str(FILE))
        networks = data['networks']
        ids = [n['id'] for n in networks]
        self.assertEqual(set(ids), IDS, f'{FILE}: perfiles {ids}')
        self.assertEqual(len(ids), len(IDS), f'{FILE}: identificadores duplicados')
        available = []
        for n in networks:
            url = urlsplit(n['profile_url'])
            self.assertEqual(url.scheme, 'https', f'{FILE}: {n["id"]} URL {n["profile_url"]}')
            self.assertTrue(url.hostname, f'{FILE}: {n["id"]} sin dominio')
            if n['status'] == 'ok':
                self.assertIs(type(n['followers']), int, f'{FILE}: {n["id"]} followers')
                self.assertGreaterEqual(n['followers'], 0, f'{FILE}: {n["id"]} followers')
                available.append(n)
        totals = data['totals']
        self.assertEqual(totals['coverage'], len(available), f'{FILE}: coverage')
        self.assertEqual(totals['eligible'], len(IDS), f'{FILE}: eligible')
        self.assertEqual(totals['follower_relationships'], sum(n['followers'] for n in available), f'{FILE}: follower_relationships')
        self.assertIn('no personas únicas', totals['label'], f'{FILE}: interpretación del total')

if __name__ == '__main__':
    unittest.main()
