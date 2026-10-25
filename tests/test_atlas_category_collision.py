import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'build-atlas-literario.py'
spec = importlib.util.spec_from_file_location('atlas_builder_category_test', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AtlasCategoryCollision(unittest.TestCase):
    def load_categories(self, categories):
        data = {
            'updated': '2026-10-25',
            'categories': categories,
            'items': []
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'atlas.json'
            path.write_text(json.dumps(data), encoding='utf-8')
            return module.load(path)

    def test_unique_categories_preserve_identity(self):
        categories = [
            {'slug': 'bibliotecas', 'name': 'Bibliotecas'},
            {'slug': 'librerias', 'name': 'Librerías'},
            {'slug': 'rutas', 'name': 'Rutas literarias'}
        ]
        _, result = self.load_categories(categories)
        self.assertEqual(result, {item['slug']: item['name'] for item in categories})
        self.assertEqual(len(result), len(categories))

    def test_duplicate_slug_rejected_in_both_orders(self):
        first = {'slug': 'bibliotecas', 'name': 'Bibliotecas históricas'}
        second = {'slug': 'bibliotecas', 'name': 'Bibliotecas contemporáneas'}
        for categories in ([first, second], [second, first]):
            with self.subTest(categories=categories):
                with self.assertRaises(ValueError):
                    self.load_categories(categories)

    def test_identical_duplicate_also_rejected(self):
        category = {'slug': 'bibliotecas', 'name': 'Bibliotecas'}
        with self.assertRaises(ValueError):
            self.load_categories([category, dict(category)])

    def test_collision_does_not_depend_on_position(self):
        base = [
            {'slug': 'bibliotecas', 'name': 'Bibliotecas'},
            {'slug': 'rutas', 'name': 'Rutas'},
            {'slug': 'librerias', 'name': 'Librerías'}
        ]
        duplicate = {'slug': 'rutas', 'name': 'Rutas alternativas'}
        for position in range(len(base) + 1):
            categories = list(base)
            categories.insert(position, duplicate)
            with self.subTest(position=position):
                with self.assertRaises(ValueError):
                    self.load_categories(categories)


if __name__ == '__main__':
    unittest.main()
