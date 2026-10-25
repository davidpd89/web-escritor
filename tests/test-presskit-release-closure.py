import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('press_builder', ROOT / 'scripts/build-press-kit.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class ReleaseClosure(unittest.TestCase):
    def test_every_member_requires_approval(self):
        book = json.loads((ROOT / 'tests/fixtures/press-kit/book.json').read_text())
        author = json.loads((ROOT / 'tests/fixtures/press-kit/author.json').read_text())
        editorial = json.loads((ROOT / 'tests/fixtures/press-kit/editorial.json').read_text())
        original_root = builder.ROOT
        try:
            with tempfile.TemporaryDirectory() as directory:
                builder.ROOT = Path(directory)
                (builder.ROOT / 'assets').mkdir()
                (builder.ROOT / 'assets/cover.webp').write_bytes(b'FAKE-WEBP')
                for required in (False, True):
                    for status in ('approved', 'blocked-pending-editorial-clearance', 'pending'):
                        with self.subTest(required=required, status=status):
                            manifest = {'assets': [{'source': 'assets/cover.webp', 'archivePath': 'media/cover.webp', 'required': required, 'releaseStatus': status}], 'documents': []}
                            errors = builder.validate(manifest, copy.deepcopy(book), copy.deepcopy(author), copy.deepcopy(editorial))
                            if status == 'approved':
                                self.assertEqual(errors, [])
                            else:
                                self.assertTrue(errors, 'La obligatoriedad no debe anular una restricción editorial')
        finally:
            builder.ROOT = original_root

if __name__ == '__main__':
    unittest.main()