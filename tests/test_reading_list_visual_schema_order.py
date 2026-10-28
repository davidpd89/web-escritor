import importlib.util
import json
import re
import unittest
from pathlib import Path
from html import unescape

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_list', ROOT / 'scripts/build-reading-list.py')
reading = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reading)

class ReadingOrderParity(unittest.TestCase):
    def test_schema_positions_match_visible_order(self):
        cases = [
            ('Antigua terminada', 'finished', '2026-01-01'),
            ('Actual leyendo', 'reading', None),
            ('Nueva terminada', 'finished', '2026-02-01'),
            ('Lectura pausada', 'paused', None)
        ]
        items = []
        for i, (title, status, finished) in enumerate(cases):
            items.append({'id': f'obra-{i}', 'title': title, 'author': 'Autora', 'note': 'Nota editorial de prueba ' * 5, 'status': status, 'started_on': '2025-12-01', 'finished_on': finished, 'link_kind': 'none'})
        html = reading.render(items, '', '2026-02-10')
        visible = [unescape(x) for x in re.findall(r'<h3>(.*?)</h3>', html, re.S)]
        block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
        self.assertIsNotNone(block)
        schema = json.loads(block.group(1))
        elements = schema['mainEntity']['itemListElement']
        self.assertEqual([x['position'] for x in elements], list(range(1, len(items) + 1)))
        self.assertEqual([x['name'] for x in elements], visible)
        self.assertEqual(len(visible), len(items))

if __name__ == '__main__':
    unittest.main()