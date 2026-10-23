import json
import re
import unittest
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MastheadParity(unittest.TestCase):
    def test_every_static_territory_has_exact_menu(self):
        nav = json.loads((ROOT / 'data/navigation.json').read_text(encoding='utf-8'))
        registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
        by_id = {entry['id']: {**registry['defaults'], **entry} for entry in registry['entries']}
        html = (ROOT / 'index.html').read_text(encoding='utf-8')
        region = html.split('<nav class="masthead-nav"', 1)[1].split('</nav>', 1)[0]
        static_ids = re.findall(r'data-territory="([^"]+)"', region)
        expected_ids = [item['id'] for item in nav['exploreTerritories']]
        self.assertEqual(static_ids, expected_ids)
        for territory in expected_ids:
            with self.subTest(territory=territory):
                pattern = rf'<div class="masthead-nav__submenu" id="masthead-submenu-{re.escape(territory)}"[^>]*>(.*?)</div>'
                blocks = re.findall(pattern, region, re.S)
                self.assertEqual(len(blocks), 1)
                actual = [(unescape(href), unescape(re.sub(r'<[^>]+>', '', label)).strip()) for href, label in re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', blocks[0], re.S)]
                expected = [(by_id[item['targetId']]['url'], item['label']) for item in nav['menu'][territory]]
                self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()