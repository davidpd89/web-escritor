import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pagefind_builder', ROOT / 'scripts/build-pagefind-index.py')
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)

class ManifestIntegrity(unittest.TestCase):
    def test_manifest_matches_real_corpus(self):
        pages = builder.eligible_pages(ROOT)
        self.assertTrue(pages, 'El corpus real de Pagefind está vacío')
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            builder.write_manifest(out, pages, ROOT)
            manifest = json.loads((out / builder.MANIFEST_NAME).read_text(encoding='utf-8'))
            self.assertEqual(manifest['page_count'], len(pages), 'page_count no coincide con las páginas indexables reales')
            self.assertEqual(len(set(manifest['pages'])), len(pages), 'El manifiesto contiene rutas duplicadas')
            self.assertEqual(manifest['pages'], pages, 'El manifiesto no conserva el corpus real')
            hashes = manifest['source_sha256']
            self.assertEqual(set(hashes), set(pages), 'Las rutas y las huellas SHA-256 del manifiesto no coinciden')
            for rel, digest in hashes.items():
                self.assertRegex(digest, r'^[0-9a-f]{64}$', f'{rel}: huella SHA-256 inválida')

if __name__ == '__main__':
    unittest.main()
