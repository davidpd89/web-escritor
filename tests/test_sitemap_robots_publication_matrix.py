import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap', ROOT / 'scripts/build-sitemap.py')
sitemap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sitemap)

class RobotsPublicationMatrix(unittest.TestCase):
    def test_valid_noindex_variants_never_enter_sitemap(self):
        variants = [
            '<meta content="noindex,follow" name="robots">',
            '<META CONTENT="NOINDEX" NAME="ROBOTS">',
            '<meta name="robots" content="index, noindex">',
            '<meta name="robots" content="follow"><meta content="noindex" name="robots">'
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for i, markup in enumerate(variants):
                file = root / f'blocked-{i}.html'
                file.write_text('<!doctype html><html><head>' + markup + f'<link rel="canonical" href="https://davidportodiaz.com/blocked-{i}/"></head><body><h1>No indexar</h1></body></html>', encoding='utf-8')
            public = root / 'public.html'
            public.write_text('<html><head><meta name="robots" content="index,follow"><link rel="canonical" href="https://davidportodiaz.com/public/"></head></html>', encoding='utf-8')
            urls = sitemap.collect_urls(root)
            self.assertIn('https://davidportodiaz.com/public/', urls)
            for i in range(len(variants)):
                with self.subTest(variant=i):
                    self.assertNotIn(f'https://davidportodiaz.com/blocked-{i}/', urls)

if __name__ == '__main__':
    unittest.main()