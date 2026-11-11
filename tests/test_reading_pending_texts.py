"""La PR de textos (bucle local con ChatGPT) no bloquea la carga diaria de libros."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('refresh_reading_catalogue', ROOT / 'scripts/refresh-reading-catalogue.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


class PendingTextsTests(unittest.TestCase):
    def test_texts_proposal_is_not_a_pending_batch(self):
        opened = [{'headRefName': 'automation/reading-catalogue-textos-2026-11-02-163627'},
                  {'headRefName': 'automation/reading-catalogue-2026-11-02-1'},
                  {'headRefName': 'automation/reading-catalogue-amazon-2026-11-10-181614'},
                  {'headRefName': 'automation/reading-catalogue-futuro-bucle'},
                  {'headRefName': 'feat/otra-cosa'}]
        self.assertEqual(refresh.pending_batches(opened), ['automation/reading-catalogue-2026-11-02-1'])

    def test_own_branch_shape_matches_the_writer(self):
        src = (ROOT / 'scripts/refresh-reading-catalogue.py').read_text(encoding='utf-8')
        self.assertIn("fresh_branch('automation/reading-catalogue-' + day + '-'", src)
        self.assertTrue(refresh.OWN_BATCH.fullmatch('automation/reading-catalogue-2026-11-11-3'))

    def test_texts_prefix_matches_the_texts_loop(self):
        src = (ROOT / 'scripts/reading-texts.py').read_text(encoding='utf-8')
        self.assertIn(f"branch = '{refresh.TEXTS_PREFIX}'", src)


if __name__ == '__main__':
    unittest.main()
