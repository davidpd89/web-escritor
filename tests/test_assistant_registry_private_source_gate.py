import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build-assistant-source-registry.mjs'

class AssistantPrivateSourceGate(unittest.TestCase):
    def run_case(self, url):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / 'scripts').mkdir()
            (base / 'data').mkdir()
            (base / 'assets').mkdir()
            shutil.copyfile(SCRIPT, base / 'scripts/build-assistant-source-registry.mjs')
            registry = {'schema_version': 1, 'policy': 'deny-by-default', 'sources': [{'id': 'fixture', 'visibility': 'public', 'url': url, 'title': 'Recurso de prueba'}]}
            (base / 'data/assistant-source-registry.json').write_text(json.dumps(registry), encoding='utf-8')
            return subprocess.run(['node', str(base / 'scripts/build-assistant-source-registry.mjs')], cwd=base, capture_output=True, text=True)

    def test_public_reference(self):
        result = self.run_case('/libros/')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_operational_sources_are_denied(self):
        for url in ['/data/private.json', '/scripts/check-secrets.py', '/tests/fixture.html', '/.github/workflows/internal.yml', '/migrations/secret.sql']:
            with self.subTest(url=url):
                result = self.run_case(url)
                self.assertNotEqual(result.returncode, 0, 'Fuente operativa aceptada: ' + url)

if __name__ == '__main__':
    unittest.main()