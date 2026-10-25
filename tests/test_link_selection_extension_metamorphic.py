import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('selector', ROOT / 'scripts/select-link-check-inputs.py')
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)

class SelectionMetamorphicTests(unittest.TestCase):
    def test_public_html_selection_is_permutation_invariant(self):
        pages = ['index.html', 'books/index.html', 'cuaderno/index.html']
        expected = selector.public_html(pages)
        for variant in [list(reversed(pages)), pages + pages, sorted(pages)]:
            with self.subTest(variant=variant):
                self.assertEqual(selector.public_html(variant), expected)

    def test_valid_nested_paths_are_preserved(self):
        pages = ['a/b/c/index.html', 'a-b/c_d.html', '2026/10/index.html']
        self.assertEqual(selector.public_html(pages), sorted(pages))

    def test_unsafe_paths_fail_explicitly(self):
        for path in ['a/../b.html', 'a/./../b.html', 'a/file name.html', 'a/$(cmd).html', 'a/;cmd.html']:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    selector.public_html([path])

    def test_case_variants_cannot_disappear_silently(self):
        for path in ['INDEX.HTML', 'Books/Index.HTML', 'books/page.Html']:
            with self.subTest(path=path):
                try:
                    selected = selector.public_html([path])
                except ValueError:
                    continue
                self.assertIn(path, selected, 'Una página HTML válida no debe desaparecer silenciosamente')

if __name__ == '__main__':
    unittest.main()
