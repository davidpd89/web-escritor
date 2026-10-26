import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def luminance(value):
    rgb = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    rgb = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in rgb]
    return sum(x * weight for x, weight in zip(rgb, (.2126, .7152, .0722)))


def ratio(a, b):
    light, dark = sorted((luminance(a), luminance(b)), reverse=True)
    return (light + .05) / (dark + .05)


class OfflinePaletteRegression(unittest.TestCase):
    def test_recovery_text_and_primary_action(self):
        page = 'offline.html'
        source = (ROOT / page).read_text(encoding='utf-8')
        tokens = dict(re.findall(r'(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;', source))
        combinations = [('--ink', '--paper'), ('--paper-2', '--ink'), ('--accent', '--paper')]
        for foreground, background in combinations:
            with self.subTest(foreground=foreground, background=background):
                self.assertIn(foreground, tokens, f'{page}: falta {foreground}')
                self.assertIn(background, tokens, f'{page}: falta {background}')
                measured = ratio(tokens[foreground], tokens[background])
                self.assertGreaterEqual(measured, 4.5, f'{page}: {foreground}={tokens[foreground]} sobre {background}={tokens[background]} produce {measured:.2f}:1')
        self.assertRegex(source, r'\.primary\s*\{[^}]*background\s*:\s*var\(--ink\)[^}]*color\s*:\s*var\(--paper-2\)', f'{page}: cambió la combinación del botón primario; revisar auditoría')


if __name__ == '__main__':
    unittest.main()
