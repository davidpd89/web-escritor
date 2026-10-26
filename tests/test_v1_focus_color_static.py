import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / 'assets/v1-base.css').read_text(encoding='utf-8')
TOKENS = (ROOT / 'assets/v1-tokens.css').read_text(encoding='utf-8')


def value(name):
    match = re.search(r'--' + re.escape(name) + r'\s*:\s*([^;]+);', TOKENS)
    if not match:
        raise AssertionError(f'assets/v1-tokens.css: falta --{name}')
    result = match.group(1).strip()
    ref = re.fullmatch(r'var\(--([\w-]+)\)', result)
    return value(ref.group(1)) if ref else result


def lum(color):
    raw = color.lstrip('#')
    if len(raw) == 3:
        raw = ''.join(x * 2 for x in raw)
    assert len(raw) == 6, f'Color no compatible: {color}'
    channels = [int(raw[i:i+2], 16) / 255 for i in (0, 2, 4)]
    linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in channels]
    return sum(a * b for a, b in zip(linear, (.2126, .7152, .0722)))


class FocusColorContract(unittest.TestCase):
    def test_focus_indicator_geometry_and_color(self):
        match = re.search(r'html\.v1\s+:focus-visible\s*\{([^}]+)\}', BASE)
        self.assertIsNotNone(match, 'assets/v1-base.css: falta regla :focus-visible compartida')
        declaration = match.group(1)
        self.assertRegex(declaration, r'outline\s*:\s*(?:2|3|4)px\s+solid\s+var\(--focus-color\)', 'assets/v1-base.css: foco sin contorno sólido de al menos 2px')
        self.assertRegex(declaration, r'outline-offset\s*:\s*[1-9]\d*px', 'assets/v1-base.css: foco sin separación visible')
        self.assertNotRegex(declaration, r'outline\s*:\s*(?:none|0)(?:\s|;|$)', 'assets/v1-base.css: foco eliminado')

    def test_focus_contrast_on_page(self):
        foreground = value('focus-color')
        background = value('surface-page')
        a, b = sorted((lum(foreground), lum(background)), reverse=True)
        ratio = (a + .05) / (b + .05)
        self.assertGreaterEqual(ratio, 3, f'assets/v1-tokens.css: foco {foreground} sobre página {background} tiene {ratio:.2f}:1; mínimo 3:1')


if __name__ == '__main__':
    unittest.main()
