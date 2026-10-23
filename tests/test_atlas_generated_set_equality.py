import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('atlas', ROOT / 'scripts/build-atlas-literario.py')
atlas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(atlas)

class AtlasSetEquality(unittest.TestCase):
    def test_published_sets_are_bijective(self):
        original = json.loads((ROOT / 'data/atlas-literario.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as directory:
            data = dict(original)
            entries = []
            for i, item in enumerate(original['items'][:4]):
                current = dict(item)
                if i < 3:
                    current['status'] = 'published'
                    current['verified_date'] = '2026-08-20'
                    current['image'] = {'src': '/assets/test.webp', 'alt': 'Prueba', 'credit': 'QA', 'license': 'CC0', 'source_url': 'https://example.org/image'}
                entries.append(current)
            data['items'] = entries
            source = Path(directory) / 'source.json'
            source.write_text(json.dumps(data), encoding='utf-8')
            loaded, categories = atlas.load(source)
            output = Path(directory) / 'out'
            atlas.build(loaded, categories, output)
            html = (output / 'index.html').read_text(encoding='utf-8')
            public = json.loads((output / 'atlas-literario-public.json').read_text(encoding='utf-8'))
            cards = re.findall(r'<article\b[^>]*data-atlas-card\b[^>]*>(.*?)</article>', html, re.S)
            slugs = []
            for card in cards:
                match = re.search(r'<h2><a href="/atlas-literario/([^/]+)/"', card)
                self.assertIsNotNone(match, card[:100])
                slugs.append(match.group(1))
            expected = [item['slug'] for item in entries if item['status'] == 'published']
            actual_json = [item['slug'] for item in public['items']]
            self.assertEqual(len(slugs), len(set(slugs)))
            self.assertEqual(len(actual_json), len(set(actual_json)))
            self.assertEqual(set(slugs), set(expected))
            self.assertEqual(set(actual_json), set(expected))
            self.assertEqual(len(cards), len(expected))

if __name__ == '__main__':
    unittest.main()