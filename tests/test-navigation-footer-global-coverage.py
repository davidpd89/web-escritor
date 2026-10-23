import json
import re
import unittest
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'autor.html', 'cuaderno/index.html', 'recomendaciones/index.html', 'mapa-del-sitio/index.html', 'las-manecillas-del-recuerdo/fragmentos/index.html']


class FooterCoverage(unittest.TestCase):
    def test_all_shared_footers_retain_registry_destinations(self):
        nav = json.loads((ROOT / 'data/navigation.json').read_text(encoding='utf-8'))
        registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
        entries = {item['id']: {**registry['defaults'], **item} for item in registry['entries']}
        required = {entries[item_id]['url'] for ids in nav['footer'].values() for item_id in ids}
        self.assertGreaterEqual(len(required), 15)
        for source in PAGES:
            with self.subTest(source=source):
                html = (ROOT / source).read_text(encoding='utf-8')
                footers = re.findall(r'<footer class="site-footer"[^>]*>(.*?)</footer>', html, re.S)
                self.assertEqual(len(footers), 1)
                hrefs = [unescape(x) for x in re.findall(r'<a\b[^>]*\bhref="([^"]+)"', footers[0])]
                self.assertGreaterEqual(len(hrefs), len(required))
                self.assertEqual(required - set(hrefs), set(), f'Missing from {source}')
                for href in required:
                    self.assertEqual(hrefs.count(href), 1, f'{source}: repeated or absent footer destination {href}')


if __name__ == '__main__':
    unittest.main()