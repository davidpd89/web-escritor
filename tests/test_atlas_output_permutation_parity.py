import importlib.util
import itertools
import json
import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'build-atlas-literario.py'
spec = importlib.util.spec_from_file_location('atlas_builder_permutation_test', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AtlasOutputPermutationParity(unittest.TestCase):
    def item(self, slug, status):
        return {
            'slug': slug,
            'title': 'Título ' + slug,
            'summary': 'Descripción ' + slug,
            'category': 'rutas',
            'relationship': 'writer-route',
            'source_urls': ['https://example.org/' + slug],
            'status': status,
            'verified_date': '2026-10-25',
            'image': {
                'src': '/assets/atlas-literario-placeholder.webp',
                'alt': 'Lugar',
                'credit': 'Autor',
                'license': 'CC BY 4.0',
                'source_url': 'https://example.org/image'
            }
        }

    def test_published_identity_is_permutation_invariant(self):
        items = [
            self.item('ruta-uno', 'published'),
            self.item('ruta-dos', 'published'),
            self.item('ruta-tres', 'draft'),
            self.item('ruta-cuatro', 'published')
        ]
        expected = {'ruta-uno', 'ruta-dos', 'ruta-cuatro'}
        for permutation in itertools.permutations(items):
            with self.subTest(order=[item['slug'] for item in permutation]):
                data = {
                    'updated': '2026-10-25',
                    'categories': [{'slug': 'rutas', 'name': 'Rutas literarias'}],
                    'items': list(permutation)
                }
                with tempfile.TemporaryDirectory() as directory:
                    out = Path(directory) / 'output'
                    count = module.build(data, {'rutas': 'Rutas literarias'}, out)
                    document = (out / 'index.html').read_text(encoding='utf-8')
                    public = json.loads((out / 'atlas-literario-public.json').read_text(encoding='utf-8'))
                    html_slugs = re.findall(r'<h2><a href="/atlas-literario/([a-z0-9-]+)/">', document)
                    json_slugs = [item['slug'] for item in public['items']]
                    self.assertEqual(count, len(expected))
                    self.assertEqual(set(html_slugs), expected)
                    self.assertEqual(set(json_slugs), expected)
                    self.assertEqual(len(html_slugs), len(expected))
                    self.assertEqual(len(json_slugs), len(expected))
                    self.assertEqual(set(html_slugs), set(json_slugs))
                    self.assertNotIn('ruta-tres', document)


if __name__ == '__main__':
    unittest.main()
