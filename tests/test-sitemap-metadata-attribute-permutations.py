import importlib.util
import itertools
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_metadata', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class MetadataPermutationTests(unittest.TestCase):
    def test_canonical_attribute_order(self):
        attrs = ['rel="canonical"', 'href="https://davidportodiaz.com/obra/"', 'id="canonical-test"']
        for permutation in itertools.permutations(attrs):
            with self.subTest(attrs=permutation):
                html = '<link ' + ' '.join(permutation) + '>'
                canonical, _, _ = module.extract_meta(html)
                self.assertEqual(canonical, 'https://davidportodiaz.com/obra/')

    def test_robots_attribute_order(self):
        attrs = ['name="robots"', 'content="noindex,follow"', 'id="robots-test"']
        for permutation in itertools.permutations(attrs):
            with self.subTest(attrs=permutation):
                html = '<meta ' + ' '.join(permutation) + '>'
                _, noindex, _ = module.extract_meta(html)
                self.assertTrue(noindex)

    def test_jsonld_script_attribute_order(self):
        attrs = ['type="application/ld+json"', 'id="structured-data"']
        payload = '{"@type":"Article","dateModified":"2026-10-20"}'
        for permutation in itertools.permutations(attrs):
            html = '<script ' + ' '.join(permutation) + '>' + payload + '</script>'
            with self.subTest(attrs=permutation):
                self.assertEqual(module.extract_date_modified(html), '2026-10-20')

if __name__ == '__main__':
    unittest.main()