import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def function_body(source, name):
    match = re.search(r'function\s+' + re.escape(name) + r'\s*\([^)]*\)\s*\{', source)
    if not match:
        raise AssertionError(f'No se encuentra la función {name}')
    depth = 1
    pos = match.end()
    start = pos
    while pos < len(source) and depth:
        if source[pos] == '{':
            depth += 1
        elif source[pos] == '}':
            depth -= 1
        pos += 1
    return source[start:pos - 1]


class SharedDialogFocusFilterTest(unittest.TestCase):
    def test_popup_excludes_hidden_and_inert_controls(self):
        popup_path = ROOT / 'assets/newsletter-popup.js'
        shell_path = ROOT / 'assets/v1-shell.js'
        popup = popup_path.read_text(encoding='utf-8')
        shell = shell_path.read_text(encoding='utf-8')
        self.assertIn('isTabbable', shell, f'{shell_path}: falta referencia del filtro compartido')
        body = function_body(popup, 'trapTabCycle')
        self.assertIn('Tab', body, f'{popup_path}: no se comprueba Tab')
        self.assertRegex(body, r'(?:querySelectorAll|focusable)', f'{popup_path}: no se enumeran controles')
        for marker in ('hidden', 'inert', 'aria-hidden'):
            self.assertIn(marker, body, f'{popup_path}: trapTabCycle no excluye controles bajo {marker}')
        self.assertRegex(
            body,
            r'(?:getComputedStyle|visibility|getClientRects|offsetParent)',
            f'{popup_path}: falta comprobación de visibilidad efectiva',
        )


if __name__ == '__main__':
    unittest.main()
