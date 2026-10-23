import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hub', ROOT / 'scripts/build-tools-hub.py')
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)

class ThreeWaySetEquality(unittest.TestCase):
    def test_cards_noscript_and_schema_match_dataset(self):
        data = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))
        tools, directories = hub.validate(data)
        markup = hub.render(data, tools, directories)
        cards = re.findall(r'<article class="id-card" data-tool\b.*?<h3><a href="([^"]+)"', markup, re.S)
        noscript = re.search(r'<noscript>(.*?)</noscript>', markup, re.S)
        schema_block = re.search(r'<script type="application/ld\+json">(.*?)</script>', markup, re.S)
        self.assertIsNotNone(noscript)
        self.assertIsNotNone(schema_block)
        alternate = re.findall(r'<strong><a href="([^"]+)"', noscript.group(1))
        schema = json.loads(schema_block.group(1))
        entries = schema['mainEntity']['itemListElement']
        structured = [entry['url'].removeprefix('https://davidportodiaz.com') for entry in entries]
        expected = [tool['href'] for tool in tools]
        for name, actual in [('tarjetas', cards), ('sin JavaScript', alternate), ('JSON-LD', structured)]:
            with self.subTest(representation=name):
                self.assertCountEqual(actual, expected)
                self.assertEqual(len(actual), len(set(actual)))
        self.assertEqual([entry['position'] for entry in entries], list(range(1, len(expected) + 1)))
        self.assertEqual(schema['mainEntity']['numberOfItems'], len(expected))

if __name__ == '__main__':
    unittest.main()