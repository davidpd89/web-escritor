import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hub', ROOT / 'scripts/build-tools-hub.py')
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)
BASE = json.loads((ROOT / 'data/tools-hub.json').read_text(encoding='utf-8'))

class NavigationPathBoundaries(unittest.TestCase):
    def test_invalid_tool_paths(self):
        cases = ['//evil.example/', '/../../', '/herramientas/../privado/', '/herramientas/obra/?origen=externo/']
        for href in cases:
            with self.subTest(href=href):
                data = copy.deepcopy(BASE)
                data['tools'][0]['href'] = href
                with self.assertRaises(ValueError):
                    hub.validate(data)

    def test_invalid_directory_paths(self):
        cases = ['//evil.example/', '/../../', 'https://evil.example/', '/directorio/../privado/']
        for href in cases:
            with self.subTest(href=href):
                data = copy.deepcopy(BASE)
                data.setdefault('directories', []).append({'name': 'Destino adversarial', 'href': href, 'summary': 'Prueba de validación'})
                with self.assertRaises(ValueError):
                    hub.validate(data)

    def test_real_dataset_stays_valid(self):
        tools, directories = hub.validate(copy.deepcopy(BASE))
        self.assertGreaterEqual(len(tools), 5)
        self.assertIsInstance(directories, list)

if __name__ == '__main__':
    unittest.main()