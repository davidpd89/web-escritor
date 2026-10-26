import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def luminance(color):
    rgb = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    rgb = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in rgb]
    return sum(x * w for x, w in zip(rgb, (.2126, .7152, .0722)))


class RecoveryKickerContrast(unittest.TestCase):
    def test_404_small_label_contrast(self):
        page = '404.html'
        html = (ROOT / page).read_text(encoding='utf-8')
        css = (ROOT / 'assets/v1-findability.css').read_text(encoding='utf-8')
        tokens_css = (ROOT / 'assets/v1-tokens.css').read_text(encoding='utf-8')
        self.assertIn('findability-hero__kicker', html, f'{page}: no existe el rótulo esperado')
        matches = re.findall(r'--findability-gold\s*:\s*(#[0-9a-fA-F]{6})', css)
        self.assertTrue(matches, 'assets/v1-findability.css: falta el color del rótulo')
        self.assertRegex(css, r'\.findability-hero__kicker\s*\{\s*color\s*:\s*var\(--findability-gold\)', 'assets/v1-findability.css: revisar color efectivo del rótulo')
        background = re.search(r'--surface-page\s*:\s*(#[0-9a-fA-F]{3,6})', tokens_css)
        self.assertIsNotNone(background, 'assets/v1-tokens.css: falta el fondo de página')
        bg = background.group(1)
        if len(bg) == 4:
            bg = '#' + ''.join(c * 2 for c in bg[1:])
        a, b = sorted((luminance(matches[-1]), luminance(bg)), reverse=True)
        measured = (a + .05) / (b + .05)
        self.assertGreaterEqual(measured, 4.5, f'{page} .findability-hero__kicker: {matches[-1]} sobre {bg}, contraste {measured:.2f}:1; mínimo 4.5:1')


if __name__ == '__main__':
    unittest.main()
