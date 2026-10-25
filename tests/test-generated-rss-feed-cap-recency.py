import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rss_cap', ROOT / 'scripts/build-feed.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class RssFeedCapRecency(unittest.TestCase):
    def test_sixty_articles_publish_only_fifty_newest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for index in range(60):
                day = (date(2026, 1, 1) + timedelta(days=index)).isoformat()
                url = f'https://davidportodiaz.com/cuaderno/articulo-{index:02d}/'
                page = root / f'articulo-{index:02d}.html'
                page.write_text(f'<title>Artículo {index}</title><link rel="canonical" href="{url}"><meta name="datePublished" content="{day}">', encoding='utf-8')
                paths.append(str(page))
            with patch.object(mod, 'find_html_files', return_value=iter(reversed(paths))):
                items, skipped = mod.collect_items()
            self.assertEqual(skipped, 0)
            self.assertEqual(len(items), 50)
            self.assertTrue(items[0]['url'].endswith('articulo-59/'))
            self.assertTrue(items[-1]['url'].endswith('articulo-10/'))
            xml = ET.fromstring(mod.build_feed_bytes(items))
            self.assertEqual(len(xml.findall('./channel/item')), 50)

if __name__ == '__main__':
    unittest.main()
