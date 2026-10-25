import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sitemap_dates_real', ROOT / 'scripts/build-sitemap.py')
sitemap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sitemap)

class SitemapEditorialDates(unittest.TestCase):
    def test_real_public_pages_keep_valid_editorial_dates(self):
        urls = sitemap.collect_urls(ROOT)
        now = datetime.now(timezone.utc)
        for url, value in urls.items():
            if not value:
                continue
            normalized = sitemap.normalize_lastmod(value)
            self.assertIsNotNone(normalized, f'sitemap.xml: lastmod inválido para {url}: {value!r}')
            parsed = datetime.fromisoformat(normalized.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
                self.assertLessEqual(parsed.date(), now.date(), f'sitemap.xml: fecha editorial futura para {url}: {value!r}')
            else:
                self.assertLessEqual(parsed, now, f'sitemap.xml: fecha editorial futura para {url}: {value!r}')

if __name__ == '__main__':
    unittest.main()