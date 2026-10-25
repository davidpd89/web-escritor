import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('analytics_checker', ROOT / 'scripts/check-analytics-taxonomy.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

class BridgeEmissionMatrixTests(unittest.TestCase):
    def test_unregistered_events_across_emission_forms(self):
        expressions = [
            "emit('evento-desconocido')",
            'analytics("evento-desconocido")',
            "dispatchShareEvent('evento-desconocido')",
            "dispatchEvent(new CustomEvent('dp:analytics', {detail:{event:'evento-desconocido'}}))",
            'emit(`evento-desconocido`)'
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'article.js'
            for expression in expressions:
                with self.subTest(expression=expression):
                    source.write_text(expression, encoding='utf-8')
                    errors = checker.check_article_bridge([source], root, {'article.js': []})
                    self.assertTrue(any('evento-desconocido' in error for error in errors), errors)

    def test_registered_event_does_not_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'article.js'
            source.write_text("emit('evento-permitido')", encoding='utf-8')
            errors = checker.check_article_bridge([source], root, {'article.js': ['evento-permitido']})
            self.assertEqual(errors, [])

    def test_new_module_with_bridge_requires_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'new-module.js'
            source.write_text("document.dispatchEvent(new CustomEvent('dp:analytics', {detail:{event:'nuevo'}}))", encoding='utf-8')
            errors = checker.check_article_bridge([source], root, {})
            self.assertTrue(errors)

if __name__ == '__main__':
    unittest.main()
