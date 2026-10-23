import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('amazon_audit_adversarial', ROOT / 'scripts/audit-amazon-links.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
ASIN = 'B0GB6LGQFH'


class AmazonAdversarialURLs(unittest.TestCase):
    def audit_links(self, links):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            (base / 'data').mkdir()
            (base / 'data/reading-catalogue.json').write_text(json.dumps({'libros': []}), encoding='utf-8')
            (base / 'index.html').write_text(''.join(f'<a href="{url}">Comprar</a>' for url in links), encoding='utf-8')
            return module.audit(base, 'davidporto-21')

    def test_duplicate_tags_are_rejected(self):
        urls = [
            f'https://www.amazon.es/dp/{ASIN}?tag=davidporto-21&tag=otro-21',
            f'https://www.amazon.es/dp/{ASIN}?tag=davidporto-21&tag=davidporto-21',
        ]
        report = self.audit_links(urls)
        errors = [e for e in report['errors'] if e['type'] == 'missing_or_wrong_tag']
        self.assertEqual(len(errors), 2)

    def test_lookalike_host_is_not_counted_as_amazon(self):
        url = f'https://www.amazon.es.example.invalid/dp/{ASIN}?tag=davidporto-21'
        report = self.audit_links([url])
        self.assertEqual(report['counts'].get('product', 0), 0)
        self.assertEqual(report['counts'].get('other_tagged_amazon', 0), 0)


if __name__ == '__main__':
    unittest.main()