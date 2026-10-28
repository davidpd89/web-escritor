import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('atlas_publication_boundary', ROOT / 'scripts/build-atlas-literario.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AtlasPublicationCopyBoundary(unittest.TestCase):
    def test_public_output_contains_only_published_real_items(self):
        data, categories = MODULE.load(ROOT / 'data/atlas-literario.json')
        published = [item for item in data['items'] if item.get('status') == 'published']
        planned = [item for item in data['items'] if item.get('status') == 'planned']
        self.assertTrue(planned, 'data/atlas-literario.json: no se encuentran los proyectos editoriales previstos')
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'atlas-literario'
            count = MODULE.build(data, categories, out)
            public = json.loads((out / 'atlas-literario-public.json').read_text(encoding='utf-8'))
            self.assertEqual(count, len(published), '/atlas-literario/: número generado distinto de los artículos publicados')
            self.assertEqual(public['items'], published, '/atlas-literario/atlas-literario-public.json: el contenido público no coincide con los registros aprobados')
            index = (out / 'index.html').read_text(encoding='utf-8')
            for item in planned:
                with self.subTest(planned=item['slug']):
                    detail = out / item['slug'] / 'index.html'
                    self.assertFalse(detail.exists(), f'/atlas-literario/{item["slug"]}/: se ha creado una ficha para un proyecto pendiente')
                    self.assertNotIn('href="/atlas-literario/' + item['slug'] + '/"', index, f'/atlas-literario/: se anuncia como disponible el proyecto {item["slug"]}')
            for item in published:
                with self.subTest(published=item['slug']):
                    self.assertTrue((out / item['slug'] / 'index.html').is_file(), f'/atlas-literario/{item["slug"]}/: falta la ficha publicada')


if __name__ == '__main__':
    unittest.main()
