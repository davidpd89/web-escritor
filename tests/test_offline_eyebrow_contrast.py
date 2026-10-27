import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def luminance(color):
    values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
    return sum(a * b for a, b in zip(channels, (.2126, .7152, .0722)))


def contrast(a, b):
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return (x + .05) / (y + .05)


class OfflineEyebrowContrast(unittest.TestCase):
    def test_small_gold_label_meets_wcag_aa(self):
        page = 'offline.html'
        source = (ROOT / page).read_text(encoding='utf-8')
        tokens = dict(re.findall(r'(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;', source))
        self.assertIn('--gold', tokens, f'{page}: falta el token dorado')
        self.assertIn('--paper', tokens, f'{page}: falta el fondo de referencia')
        eyebrow = re.search(r'\.eyebrow\s*\{([^}]+)\}', source)
        self.assertIsNotNone(eyebrow, f'{page}: falta el estilo del rótulo')
        self.assertRegex(eyebrow.group(1), r'color\s*:\s*var\(--gold\)', f'{page}: revisar el selector real del rótulo')
        ratio = contrast(tokens['--gold'], tokens['--paper'])
        self.assertGreaterEqual(ratio, 4.5, f'{page} .eyebrow: contraste {ratio:.2f}:1 con {tokens["--gold"]} sobre {tokens["--paper"]}; mínimo WCAG AA 4.5:1')


if __name__ == '__main__':
    unittest.main()
