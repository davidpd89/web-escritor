import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_instant', ROOT / 'scripts/build-sitemap.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class EquivalentInstantTests(unittest.TestCase):
    def test_equivalent_offsets(self):
        cases = [
            (['2026-10-25T00:30:00+02:00', '2026-10-24T22:30:00Z', '2026-10-24T17:30:00-05:00'], '2026-10-24T22:30:00Z'),
            (['2026-01-01T00:15:00+01:00', '2025-12-31T23:15:00Z', '2025-12-31T18:15:00-05:00'], '2025-12-31T23:15:00Z'),
            (['2026-06-10T19:00:00+02:00', '2026-06-10T17:00:00Z', '2026-06-10T12:00:00-05:00'], '2026-06-10T17:00:00Z'),
        ]
        for representations, expected in cases:
            for raw in representations:
                with self.subTest(raw=raw):
                    self.assertEqual(module.normalize_lastmod(raw), expected)

if __name__ == '__main__':
    unittest.main()