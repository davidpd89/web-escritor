import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reflow_reading_scope', ROOT / 'scripts' / 'ci-select-reflow.py')
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)


class ReadingDataScopeIntegration(unittest.TestCase):
    def test_real_catalogue_data_change_requires_complete_audit(self):
        source = ROOT / 'data/reading-catalogue.json'
        payload = json.loads(source.read_text(encoding='utf-8'))
        self.assertTrue(payload['libros'], f'{source}: catálogo vacío')
        self.assertTrue(any(book.get('titulo') for book in payload['libros']), f'{source}: faltan títulos publicados')
        self.assertTrue(any(book.get('isbn13') for book in payload['libros']), f'{source}: faltan ISBN para comprobar coherencia bibliográfica')
        for changed in ([str(source.relative_to(ROOT))], ['libros/index.html', str(source.relative_to(ROOT))]):
            with self.subTest(changed=changed):
                run, reason = selector.classify(changed)
                self.assertTrue(run, f'{changed}: no puede omitirse QA cuando cambian datos del catálogo: {reason}')
                routes = selector.scope_routes(changed, exists=lambda p: (ROOT / p).is_file())
                self.assertEqual(routes, [], f'{changed}: el JSON puede afectar títulos, ISBN y precios de páginas no incluidas en el diff; debe auditarse todo')


if __name__ == '__main__':
    unittest.main()