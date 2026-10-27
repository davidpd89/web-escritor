import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/newsletter-popup.js'


class NewsletterConfirmationCloseTest(unittest.TestCase):
    def test_confirmation_preserves_manual_close(self):
        source = SOURCE.read_text(encoding='utf-8')
        match = re.search(
            r'if\s*\(result\.ok\s*&&\s*result\.state\s*===\s*[\'\"]pending_confirmation[\'\"]\)\s*\{(?P<body>.*?)\}\s*else',
            source,
            re.S,
        )
        self.assertIsNotNone(match, f'{SOURCE}: no se encuentra la rama de confirmación')
        body = match.group('body')
        replaces_panel = bool(re.search(r'panel\.(?:innerHTML\s*=|replaceChildren\s*\(|textContent\s*=)', body))
        if replaces_panel:
            self.assertRegex(
                body,
                r'(?:createElement\s*\(\s*[\'\"]button|nl-popup-close|nl-popup-skip|append\s*\([^)]*close|insertAdjacentHTML\s*\()',
                f'{SOURCE}: la confirmación sustituye el panel completo sin conservar un cierre manual',
            )
        else:
            self.assertIn('dismiss', source, f'{SOURCE}: falta mecanismo de cierre')


if __name__ == '__main__':
    unittest.main()
