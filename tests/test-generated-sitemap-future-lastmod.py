import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_future_lastmod', ROOT / 'scripts/build-sitemap.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class SitemapFutureLastmod(unittest.TestCase):
    def test_future_modified_date_is_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {'@context': 'https://schema.org', '@type': 'WebPage', 'dateModified': '2099-01-01'}
            (root / 'index.html').write_text('<link rel="canonical" href="https://davidportodiaz.com/"><script type="application/ld+json">' + json.dumps(payload) + '</script>', encoding='utf-8')
            urls = mod.collect_urls(root)
            self.assertIn('https://davidportodiaz.com/', urls)
            self.assertIsNone(urls['https://davidportodiaz.com/'], 'Una fecha futura no debe publicarse como lastmod')

if __name__ == '__main__':
    unittest.main()
