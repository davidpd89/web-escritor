import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def luminance(value):
    values = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    values = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in values]
    return sum(x * w for x, w in zip(values, (.2126, .7152, .0722)))


class OfflineFocusColor(unittest.TestCase):
    def test_focus_ring_is_distinguishable(self):
        page = 'offline.html'
        source = (ROOT / page).read_text(encoding='utf-8')
        tokens = dict(re.findall(r'(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6})\s*;', source))
        rule = re.search(r'button:focus-visible\s*\{([^}]+)\}', source)
        self.assertIsNotNone(rule, f'{page}: falta el indicador de foco de los botones')
        outline = re.search(r'outline\s*:\s*([\d.]+)px\s+solid\s+var\((--[\w-]+)\)', rule.group(1))
        self.assertIsNotNone(outline, f'{page}: contorno no verificable; revisar color y grosor')
        width, token = outline.groups()
        self.assertGreaterEqual(float(width), 2, f'{page}: grosor del foco {width}px inferior a 2px')
        self.assertIn(token, tokens, f'{page}: token de foco {token} inexistente')
        a, b = sorted((luminance(tokens[token]), luminance(tokens['--paper'])), reverse=True)
        measured = (a + .05) / (b + .05)
        self.assertGreaterEqual(measured, 3, f'{page}: foco {tokens[token]} sobre {tokens["--paper"]} tiene contraste {measured:.2f}:1')


if __name__ == '__main__':
    unittest.main()
