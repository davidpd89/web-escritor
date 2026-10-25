import importlib.util
import itertools
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rss_determinism', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class RssPermutationDeterminism(unittest.TestCase):
    def test_all_discovery_orders_generate_identical_xml(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for slug in ('zeta', 'alfa', 'beta'):
                page = root / (slug + '.html')
                page.write_text('<html><head><title>' + slug + '</title><link rel="canonical" href="https://davidportodiaz.com/cuaderno/' + slug + '/"><meta name="datePublished" content="2026-10-20"></head></html>', encoding='utf-8')
                paths.append(str(page))
            outputs = set()
            for permutation in itertools.permutations(paths):
                with patch.object(mod, 'find_html_files', return_value=iter(permutation)):
                    items, _ = mod.collect_items()
                outputs.add(mod.build_feed_bytes(items))
            self.assertEqual(len(outputs), 1, 'El RSS cambia con el orden del sistema de archivos')

if __name__ == '__main__':
    unittest.main()
