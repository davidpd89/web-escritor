import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/v1-shell.js'


def extract_function(source, name):
    match = re.search(r'function\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', source)
    if not match:
        raise AssertionError(f'{SOURCE}: no existe {name}')
    start = match.end()
    depth = 1
    pos = start
    while pos < len(source) and depth:
        if source[pos] == '{':
            depth += 1
        elif source[pos] == '}':
            depth -= 1
        pos += 1
    return source[start:pos - 1]


class ExploreListenerIdempotenceTest(unittest.TestCase):
    def test_toggle_listeners_are_guarded(self):
        source = SOURCE.read_text(encoding='utf-8')
        body = extract_function(source, 'initExploreToggles')
        self.assertIn('exploreToggleBound', body)
        self.assertIn("addEventListener('click'", body)

    def test_main_dialog_initialization_has_duplicate_guard(self):
        source = SOURCE.read_text(encoding='utf-8')
        body = extract_function(source, 'initExplore')
        self.assertRegex(body, r'opens\.forEach\s*\(')
        self.assertRegex(body, r'open\.addEventListener\s*\(')
        self.assertRegex(body, r'dialog\.addEventListener\s*\(')
        guarded = bool(re.search(r'(?:dataset\.[A-Za-z]+|WeakSet|WeakMap|AbortController|removeEventListener)', body))
        self.assertTrue(
            guarded,
            f'{SOURCE}: initExplore registra listeners sin un mecanismo explícito de idempotencia',
        )


if __name__ == '__main__':
    unittest.main()
