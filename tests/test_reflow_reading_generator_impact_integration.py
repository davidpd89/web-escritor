import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reflow_generator_impact', ROOT / 'scripts' / 'ci-select-reflow.py')
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)


class ReadingGeneratorImpactIntegration(unittest.TestCase):
    def test_real_generator_changes_never_narrow_audit_to_changed_html(self):
        generator = 'scripts/build-reading-catalogue.py'
        self.assertTrue((ROOT / generator).is_file(), f'{generator}: generador real ausente')
        content = (ROOT / generator).read_text(encoding='utf-8')
        self.assertIn('isbn13', content, f'{generator}: no se ha confirmado el tratamiento de ISBN')
        self.assertIn('titulo', content, f'{generator}: no se ha confirmado el tratamiento de títulos')
        for changed in ([generator], [generator, 'libros/index.html'], [generator, 'data/reading-catalogue.json']):
            with self.subTest(changed=changed):
                run, reason = selector.classify(changed)
                self.assertTrue(run, f'{changed}: generador bibliográfico ignorado por la auditoría: {reason}')
                scoped = selector.scope_routes(changed, exists=lambda p: (ROOT / p).is_file())
                self.assertEqual(scoped, [], f'{changed}: un generador puede alterar fichas no modificadas directamente; no debe limitarse el recorrido')


if __name__ == '__main__':
    unittest.main()