import json
import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/research'))
import gpt_social_compose as compose


class SocialProfileOrigins(unittest.TestCase):
    def test_published_profiles_match_verified_https_destinations(self):
        path = ROOT / 'redes-sociales/social-metrics.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        profiles = data['networks']
        self.assertEqual({n['id'] for n in profiles}, set(compose.PROFILES), f'{path}: identidades incompletas')
        for network in profiles:
            identity = network['id']
            url = network['profile_url']
            with self.subTest(network=identity):
                self.assertEqual(url, compose.PROFILES[identity], f'{path}: destino incorrecto de {identity}: {url}')
                parsed = urlsplit(url)
                self.assertEqual(parsed.scheme, 'https', f'{path}: esquema inseguro de {identity}')
                self.assertIsNotNone(parsed.hostname, f'{path}: autoridad ausente en {identity}')
                self.assertIsNone(parsed.username, f'{path}: usuario incrustado en {identity}')
                self.assertIsNone(parsed.password, f'{path}: contraseña incrustada en {identity}')
                # Facebook pages without a vanity name are addressed only by their numeric id.
                allowed_query = r'id=\d+' if identity == 'facebook' else ''
                self.assertRegex(parsed.query, f'^{allowed_query}$', f'{path}: parámetros inesperados en {identity}')
                self.assertFalse(parsed.fragment, f'{path}: fragmento inesperado en {identity}')


if __name__ == '__main__':
    unittest.main()
