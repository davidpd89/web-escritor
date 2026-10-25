import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reflow_registry_scope', ROOT / 'scripts' / 'ci-select-reflow.py')
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)


class ContentRegistryScopeIntegration(unittest.TestCase):
    def test_registry_changes_preserve_full_route_coverage(self):
        registry_path = ROOT / 'data/content-registry.json'
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        entries = registry['entries']
        self.assertTrue(entries, f'{registry_path}: registro vacío')
        home = next((entry for entry in entries if entry.get('url') == '/'), None)
        self.assertIsNotNone(home, f'{registry_path}: falta la portada registrada')
        self.assertEqual(home.get('sourceFile'), 'index.html', f'{registry_path}: la portada debe corresponder al HTML real')
        self.assertTrue((ROOT / home['sourceFile']).is_file(), f'{registry_path}: no existe {home["sourceFile"]}')
        changed_sets = [
            ['data/content-registry.json'],
            ['data/content-registry.json', 'index.html'],
            ['data/content-registry.json', 'libros/index.html'],
        ]
        for changed in changed_sets:
            with self.subTest(changed=changed):
                run, reason = selector.classify(changed)
                self.assertTrue(run, f'{changed}: el registro de contenido afecta a rutas publicadas: {reason}')
                routes = selector.scope_routes(changed, exists=lambda p: (ROOT / p).is_file())
                self.assertEqual(routes, [], f'{changed}: el registro puede modificar el conjunto de rutas publicadas; debe mantenerse el recorrido completo')


if __name__ == '__main__':
    unittest.main()