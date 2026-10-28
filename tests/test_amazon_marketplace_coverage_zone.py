import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('amazon_marketplace_audit', ROOT / 'scripts/audit-amazon-links.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

class MarketplaceCoverage(unittest.TestCase):
    def test_foreign_marketplaces_require_review(self):
        for host in ('www.amazon.com', 'www.amazon.co.uk', 'www.amazon.de', 'www.amazon.fr', 'www.amazon.it'):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / 'data').mkdir()
                url = 'https://' + host + '/dp/B0GB6LGQFH?tag=davidporto-21'
                (root / 'index.html').write_text('<a href="' + url + '">Comprar</a>', encoding='utf-8')
                (root / 'data/reading-catalogue.json').write_text(json.dumps({'libros': []}), encoding='utf-8')
                result = module.audit(root, 'davidporto-21')
                self.assertTrue(result['errors'] or result['manual_review'], 'Mercado extranjero omitido: ' + host)

if __name__ == '__main__':
    unittest.main()
