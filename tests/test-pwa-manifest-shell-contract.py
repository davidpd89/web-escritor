import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class PWAManifestShell(unittest.TestCase):
    def test_manifest_and_precache_consistency(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
        match = re.search(r'const APP_SHELL\s*=\s*\[([^\]]*)\]', worker, re.S)
        self.assertIsNotNone(match, 'service-worker.js: falta APP_SHELL')
        shell = re.findall(r'[\x22\x27](/[^\x22\x27]+)[\x22\x27]', match.group(1))
        self.assertEqual(len(shell), len(set(shell)), 'service-worker.js: APP_SHELL contiene recursos duplicados')
        self.assertIn('/offline.html', shell, 'service-worker.js: offline.html no está precargado')
        self.assertIn('/manifest.json', shell, 'service-worker.js: manifest.json no está precargado')
        self.assertEqual(manifest.get('start_url'), '/', 'manifest.json: start_url inesperada')
        self.assertEqual(manifest.get('scope'), '/', 'manifest.json: scope incompatible con el inicio')
        icons = manifest.get('icons', [])
        self.assertTrue(icons, 'manifest.json: no hay iconos')
        for icon in icons:
            url = icon.get('src', '')
            parsed = urlsplit(url)
            self.assertFalse(parsed.scheme or parsed.netloc, f'manifest.json: icono externo {url}')
            self.assertIn(parsed.path, shell, f'manifest.json: icono {url} ausente de APP_SHELL')
            self.assertTrue((ROOT / parsed.path.lstrip('/')).is_file(), f'manifest.json: no existe {url}')
        for url in shell:
            self.assertTrue((ROOT / url.lstrip('/')).is_file(), f'service-worker.js: recurso precargado inexistente {url}')

if __name__ == '__main__':
    unittest.main()
