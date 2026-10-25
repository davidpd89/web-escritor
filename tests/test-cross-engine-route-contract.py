from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'qa/cross-engine-smoke.mjs'

class CrossEngineRouteContract(unittest.TestCase):
    def test_routes_exist_and_http_is_checked(self):
        code = SOURCE.read_text(encoding='utf-8')
        match = re.search(r'const ROUTES\s*=\s*\[([\s\S]*?)\]', code)
        self.assertIsNotNone(match, 'No se encontró ROUTES')
        routes = re.findall(r"['\"](/[^'\"]*)['\"]", match.group(1))
        self.assertGreaterEqual(len(routes), 5)
        missing = []
        for route in routes:
            relative = route.lstrip('/')
            candidate = ROOT / relative
            if route.endswith('/'):
                candidate = candidate / 'index.html'
            if not candidate.is_file():
                missing.append(route)
        self.assertEqual(missing, [], f'Rutas inexistentes: {missing}')
        self.assertRegex(code, r'\.goto\s*\(')
        self.assertRegex(code, r'response\s*&&\s*!response\.ok\(\)')

if __name__ == '__main__':
    unittest.main()
