"""El ✕ de un formato sin edición en Amazon cumple el contraste AA (4.5:1) sobre su fondo, como exige pa11y."""
import re
import unittest
from pathlib import Path

CSS = (Path(__file__).resolve().parents[1] / 'assets/reading-catalogue.css').read_text(encoding='utf-8')


def luminance(hex_color):
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


class MissingFormatContrastTest(unittest.TestCase):
    def test_missing_mark_and_label_reach_aa_contrast(self):
        box = re.search(r'\.catalogue-format\.is-missing\{[^}]*background:(#[0-9a-f]{6});color:(#[0-9a-f]{6})', CSS)
        mark = re.search(r'\.catalogue-format\.is-missing strong\{[^}]*color:(#[0-9a-f]{6})', CSS)
        self.assertTrue(box and mark)
        background, label = box.groups()
        self.assertGreaterEqual(contrast(label, background), 4.5)
        self.assertGreaterEqual(contrast(mark[1], background), 4.5)


if __name__ == '__main__':
    unittest.main()
