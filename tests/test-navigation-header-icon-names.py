import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'autor.html', 'cuaderno/index.html', 'recomendaciones/index.html', 'mapa-del-sitio/index.html', 'las-manecillas-del-recuerdo/fragmentos/index.html']
CONTROLS = ('header-search', 'header-home', 'header-sitemap', 'explore-trigger')


class HeaderIconNames(unittest.TestCase):
    def test_navigation_icons_have_meaningful_distinct_names(self):
        for source in PAGES:
            with self.subTest(source=source):
                html = (ROOT / source).read_text(encoding='utf-8')
                header = re.search(r'<header class="site-header"[^>]*>(.*?)</header>', html, re.S)
                self.assertIsNotNone(header)
                names = []
                for control in CONTROLS:
                    pattern = rf'<(?:a|button)\b(?=[^>]*\bclass="[^"]*\b{control}\b)[^>]*>'
                    tags = re.findall(pattern, header.group(1))
                    self.assertEqual(len(tags), 1, f'{source}: {control}')
                    label = re.search(r'\baria-label="([^"]+)"', tags[0])
                    self.assertIsNotNone(label, f'{source}: {control} lacks aria-label')
                    self.assertGreaterEqual(len(label.group(1).strip()), 4)
                    names.append(label.group(1).strip().casefold())
                self.assertEqual(len(names), len(set(names)), f'{source}: duplicated control names')


if __name__ == '__main__':
    unittest.main()