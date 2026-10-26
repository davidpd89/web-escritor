import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'assets/reading-catalogue.js'


class CatalogueAsyncRefreshReview(unittest.TestCase):
    def test_market_refresh_preserves_filter_state(self):
        source = PATH.read_text(encoding='utf-8')
        self.assertIn("fetch('/assets/reading-market.json'", source, f'{PATH}: falta carga del mercado real')
        self.assertIn('p?.schema_version === 1', source)
        self.assertIn('Array.isArray(p.offers)', source)
        self.assertIn('Array.isArray(p.ratings)', source)
        self.assertRegex(source, r'market\s*=\s*\{\s*offers:\s*p\.offers\.filter\(')
        self.assertRegex(source, r'ratings:\s*p\.ratings\.filter\(')
        self.assertRegex(source, r'renderMarket\(\);\s*restore\(\);')
        self.assertRegex(source, r'const\s+refresh\s*=\s*\(\)\s*=>\s*\{\s*renderNovelty\(\);\s*renderMarket\(\);\s*apply\(false\);')
        self.assertRegex(source, r'addEventListener\([\'\"]pageshow[\'\"],\s*refresh\)')
        self.assertRegex(source, r'addEventListener\([\'\"]visibilitychange[\'\"],')
        self.assertIn('const offersFor = id =>', source)
        self.assertIn('const ratingFor = id =>', source)
        self.assertIn('fresh(o, 24)', source)
        self.assertIn('fresh(r, 168)', source)


if __name__ == '__main__':
    unittest.main()