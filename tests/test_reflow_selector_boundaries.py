import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('selector', ROOT / 'scripts/ci-select-reflow.py')
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)

class SelectorBoundaries(unittest.TestCase):
    def test_unknown_files_trigger(self):
        for name in ['unknown.bin', 'data/new.json', 'assets/new.woff2', 'PACKAGE-LOCK.JSON', 'new-directory/file']:
            with self.subTest(name=name):
                self.assertTrue(selector.classify([name])[0])

    def test_mixed_changes_trigger(self):
        self.assertTrue(selector.classify(['docs/notes.md', 'assets/styles.css'])[0])

    def test_empty_list_fails_open(self):
        self.assertTrue(selector.classify([])[0])

    def test_windows_separator_normalization(self):
        self.assertEqual(selector.classify(['assets\\styles.css'])[0], selector.classify(['assets/styles.css'])[0])

    def test_relevant_builder(self):
        self.assertTrue(selector.classify(['scripts/build-feed.py'])[0])

if __name__ == '__main__':
    unittest.main()