import json
import re
import unittest
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'autor.html', 'cuaderno/index.html', 'recomendaciones/index.html', 'mapa-del-sitio/index.html', 'las-manecillas-del-recuerdo/fragmentos/index.html']


class ExploreParity(unittest.TestCase):
    def test_static_menu_matches_canonical_data_on_every_template(self):
        nav = json.loads((ROOT / 'data/navigation.json').read_text(encoding='utf-8'))
        registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
        by_id = {e['id']: {**registry['defaults'], **e} for e in registry['entries']}
        expected_rows = [(t['id'], by_id[t['id']]['url']) for t in nav['exploreTerritories']]
        for source in PAGES:
            with self.subTest(source=source):
                html = (ROOT / source).read_text(encoding='utf-8')
                blocks = re.findall(r'<nav class="explore-list"[^>]*>(.*?)</nav>', html, re.S)
                self.assertEqual(len(blocks), 1)
                block = blocks[0]
                rows = [(key, unescape(href)) for href, key in re.findall(r'<a class="explore-row" href="([^"]+)" data-preview="([^"]+)"', block)]
                self.assertEqual(rows, expected_rows)
                for territory, _ in expected_rows:
                    pattern = rf'<div class="explore-children" id="explore-children-{re.escape(territory)}"[^>]*>(.*?)</div>'
                    children = re.findall(pattern, block, re.S)
                    self.assertEqual(len(children), 1)
                    actual = [(unescape(href), unescape(re.sub(r'<[^>]+>', '', label)).strip()) for href, label in re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', children[0], re.S)]
                    expected = [(by_id[item['targetId']]['url'], item['label']) for item in nav['menu'][territory]]
                    self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()