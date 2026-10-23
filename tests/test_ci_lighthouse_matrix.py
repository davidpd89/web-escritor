from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'lighthouserc.json').read_text(encoding='utf-8'))['ci']

class LighthouseMatrixTest(unittest.TestCase):
    def test_every_url_has_enforced_contract(self):
        urls = CONFIG['collect']['url']
        matrix = CONFIG['assert']['assertMatrix']
        self.assertTrue(urls)
        for url in urls:
            with self.subTest(url=url):
                matches = [group for group in matrix if re.search(group['matchingUrlPattern'], url)]
                self.assertEqual(len(matches), 1, f'{url}: matriz solapada o sin cobertura')
                rules = matches[0]['assertions']
                for name in ['categories:accessibility', 'cumulative-layout-shift', 'document-title']:
                    if name == 'document-title' and rules.get('categories:seo') != 'off':
                        continue
                    self.assertIn(name, rules, f'{url}: no se verifica {name}')
                    self.assertEqual(rules[name][0], 'error', f'{url}: {name} no bloquea regresiones')
                seo = rules.get('categories:seo')
                if seo == 'off':
                    for name in ['canonical', 'meta-description', 'crawlable-anchors', 'http-status-code']:
                        self.assertEqual(rules.get(name, [None])[0], 'error', f'{url}: falta sustituto SEO {name}')
                else:
                    self.assertEqual(seo[0], 'error', f'{url}: categoría SEO no bloqueante')

if __name__ == '__main__':
    unittest.main()