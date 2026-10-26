import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'assets/reading-catalogue.js'


def function_body(source, name):
    match = re.search(r'\bfunction\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', source)
    if not match:
        raise AssertionError(f'{PATH}: función ausente: {name}')
    start = match.end()
    depth = 1
    for index in range(start, len(source)):
        if source[index] == '{':
            depth += 1
        elif source[index] == '}':
            depth -= 1
            if depth == 0:
                return source[start:index]
    raise AssertionError(f'{PATH}: función sin cierre: {name}')


class CatalogueURLStateReview(unittest.TestCase):
    def test_url_state_is_written_and_restored(self):
        source = PATH.read_text(encoding='utf-8')
        apply = function_body(source, 'apply')
        restore = function_body(source, 'restore')
        for token in ('URLSearchParams', 'FACETS', 'currentPage', 'history.replaceState', 'location.search'):
            self.assertIn(token, apply, f'{PATH}: apply() no conserva {token}')
        for token in ('location.hash', 'URLSearchParams', 'params.getAll', 'currentPage', 'apply(false)'):
            self.assertIn(token, restore, f'{PATH}: restore() no contempla {token}')
        self.assertRegex(source, r'addEventListener\(\s*[\'\"]hashchange[\'\"]\s*,\s*restore\s*\)')
        self.assertRegex(source, r'fields\.forEach\(f\s*=>\s*f\.addEventListener\([\'\"]input[\'\"],\s*\(\)\s*=>\s*\{\s*currentPage\s*=\s*1;\s*apply\(\)')
        self.assertRegex(source, r'boxes\.forEach\(b\s*=>\s*b\.addEventListener\([\'\"]change[\'\"],\s*\(\)\s*=>\s*\{\s*currentPage\s*=\s*1;\s*apply\(\)')


if __name__ == '__main__':
    unittest.main()