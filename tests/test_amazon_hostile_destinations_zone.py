import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('amazon_audit_hostile', ROOT / 'scripts/audit-amazon-links.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

class HostileDestinations(unittest.TestCase):
    def audit(self, url):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            (root / 'index.html').write_text('<a href="' + url.replace('&', '&amp;') + '">Comprar</a>', encoding='utf-8')
            (root / 'data/reading-catalogue.json').write_text(json.dumps({'libros': []}), encoding='utf-8')
            return module.audit(root, 'davidporto-21')

    def test_unsafe_commercial_destinations_are_reported(self):
        urls = [
            'http://www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21',
            'https://www.amazon.es.evil.test/dp/B0GB6LGQFH?tag=davidporto-21',
            'https://user:password@www.amazon.es/dp/B0GB6LGQFH?tag=davidporto-21',
            'https://www.amazon.es:8443/dp/B0GB6LGQFH?tag=davidporto-21',
            'javascript:alert(1)'
        ]
        for url in urls:
            with self.subTest(url=url):
                result = self.audit(url)
                self.assertTrue(result['errors'], 'Destino peligroso ignorado: ' + url)

if __name__ == '__main__':
    unittest.main()
