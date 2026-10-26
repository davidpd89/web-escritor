import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_editorial_dates', ROOT / 'scripts/build-sitemap.py')
sitemap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sitemap)

class SitemapEditorialDateTests(unittest.TestCase):
    def test_cuaderno_dates_match_generated_sitemap(self):
        urls = sitemap.collect_urls(ROOT)
        checked = 0
        for page in sorted((ROOT / 'cuaderno').rglob('index.html')):
            if sitemap.should_skip_file(page, ROOT):
                continue
            canonical, noindex, raw_date = sitemap.extract_meta(sitemap.read_text(page))
            if noindex or not raw_date:
                continue
            loc = sitemap.normalize_canonical(canonical, ROOT, page)
            if not loc or loc not in urls:
                continue
            expected = sitemap.normalize_lastmod(raw_date)
            if expected is None:
                continue
            with self.subTest(page=str(page.relative_to(ROOT))):
                actual = urls[loc]
                self.assertIsNotNone(actual, f'{page}: sitemap sin lastmod para {loc}')
                self.assertGreaterEqual(actual, expected, f'{page}: sitemap lastmod {actual!r} anterior al JSON-LD {expected!r}')
            checked += 1
        self.assertGreater(checked, 0, 'cuaderno/: ninguna página real con fecha JSON-LD verificable')

if __name__ == '__main__':
    unittest.main()