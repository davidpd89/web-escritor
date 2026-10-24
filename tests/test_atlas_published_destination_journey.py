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

class PublishedDestinationJourney(unittest.TestCase):
    def test_every_published_card_has_real_destination(self):
        original = json.loads((ROOT / 'data/atlas-literario.json').read_text(encoding='utf-8'))
        for item in original['items'][:3]:
            with self.subTest(slug=item['slug']), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                case = dict(original)
                published = dict(item)
                published['status'] = 'published'
                published['verified_date'] = '2026-08-20'
                published['image'] = {'src': '/assets/fixture.webp', 'alt': 'Imagen de prueba', 'credit': 'QA', 'license': 'CC0', 'source_url': 'https://example.org/image'}
                case['items'] = [published]
                source = base / 'source.json'
                source.write_text(json.dumps(case, ensure_ascii=False), encoding='utf-8')
                loaded, categories = atlas.load(source)
                output = base / 'atlas-literario'
                self.assertEqual(atlas.build(loaded, categories, output), 1)
                html = (output / 'index.html').read_text(encoding='utf-8')
                targets = set(re.findall(r'href="(/atlas-literario/[^"#?]+/)"', html))
                expected = '/atlas-literario/' + published['slug'] + '/'
                self.assertIn(expected, targets)
                for target in targets:
                    relative = target.lstrip('/') + 'index.html'
                    self.assertTrue((base / relative).is_file() or (ROOT / relative).is_file(), 'CTA sin destino público: ' + target)

if __name__ == '__main__':
    unittest.main()