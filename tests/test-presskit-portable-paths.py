import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('press_builder', ROOT / 'scripts/build-press-kit.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class PortablePaths(unittest.TestCase):
    def test_reject_unsafe_paths(self):
        cases = [
            '../secret.txt', '/etc/passwd', 'datos/../../secret',
            'C:\\Windows\\secret.txt', '\\\\server\\share\\secret',
            'media\\..\\secret.txt', '', '.', 'media/./cover.webp',
            'media//cover.webp', 'media/../cover.webp',
            'media/file\x00.json', 'media/file\n.json'
        ]
        for value in cases:
            with self.subTest(value=repr(value)):
                with self.assertRaises(ValueError):
                    builder.safe_rel(value)

    def test_keep_safe_unicode_paths(self):
        for value in ('datos/autor.json', 'media/retrato-galicia.webp', 'datos/sinopsis-español.json'):
            with self.subTest(value=value):
                self.assertEqual(builder.safe_rel(value), value)

if __name__ == '__main__':
    unittest.main()