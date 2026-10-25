import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('analytics_checker', ROOT / 'scripts/check-analytics-taxonomy.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

class AnalyticsAttributeMetamorphicTests(unittest.TestCase):
    def test_equivalent_attribute_serializations(self):
        variants = [
            '<button data-gc="evento-no-registrado">Abrir</button>',
            "<button data-gc='evento-no-registrado'>Abrir</button>",
            '<button class="cta" data-gc="evento-no-registrado">Abrir</button>',
            '<button data-id="1" data-gc="evento-no-registrado" class="cta">Abrir</button>'
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'component.js'
            for html in variants:
                with self.subTest(html=html):
                    source.write_text('const markup = ' + repr(html) + ';', encoding='utf-8')
                    errors = checker.check_gc_events([source], root, set())
                    self.assertTrue(any('evento-no-registrado' in error for error in errors), errors)

    def test_registered_event_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'component.js'
            source.write_text('const html = `<button data-gc="registrado">Abrir</button>`;', encoding='utf-8')
            self.assertEqual(checker.check_gc_events([source], root, {'registrado'}), [])

if __name__ == '__main__':
    unittest.main()
