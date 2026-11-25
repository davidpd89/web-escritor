"""El servidor estático de QA sirve las portadas del almacén y los workflows lo usan."""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import qa_static_server as server  # noqa: E402


class StoreBytes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / 'data').mkdir()
        (self.root / 'data/reading-covers-store.json').write_text(json.dumps({
            'base_url': 'https://example.github.io/portadas', 'archivos': ['isbn-1.webp'],
            'sha256': {'isbn-1.webp': 'a' * 64}}), encoding='utf-8')
        self.served = self.root / 'dist'
        (self.served / 'assets/reading-covers').mkdir(parents=True)
        server.CACHE = self.root / 'cache'
        self.urls = []

    def tearDown(self):
        self.tmp.cleanup()

    def get(self, url):
        self.urls.append(url)
        return b'IMG'

    def test_portada_del_almacen_se_sirve_y_se_cachea(self):
        for _ in range(2):
            self.assertEqual(server.store_bytes('/assets/reading-covers/isbn-1.webp', self.served, self.root, get=self.get), b'IMG')
        self.assertEqual(self.urls, ['https://example.github.io/portadas/isbn-1.webp'])

    def test_disco_y_ajenas_no_pasan_por_el_almacen(self):
        (self.served / 'assets/reading-covers/isbn-1.webp').write_bytes(b'LOCAL')
        self.assertIsNone(server.store_bytes('/assets/reading-covers/isbn-1.webp', self.served, self.root, get=self.get))
        self.assertIsNone(server.store_bytes('/assets/reading-covers/otra.webp', self.served, self.root, get=self.get))
        self.assertIsNone(server.store_bytes('/assets/otra/isbn-1.webp', self.served, self.root, get=self.get))
        self.assertEqual(self.urls, [])


class Workflows(unittest.TestCase):
    def test_ningun_workflow_usa_http_server_plano(self):
        plain = re.compile(r'python3? -m http\.server')
        bad = [p.name for p in (ROOT / '.github/workflows').glob('*.yml') if plain.search(p.read_text(encoding='utf-8'))]
        self.assertEqual(bad, [], 'usar scripts/qa_static_server.py: sin él las portadas del almacén dan 404')


if __name__ == '__main__':
    unittest.main()
