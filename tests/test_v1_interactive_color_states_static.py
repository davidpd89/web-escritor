import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / 'assets/v1-base.css').read_text(encoding='utf-8')
SHELL = (ROOT / 'assets/v1-shell-base.css').read_text(encoding='utf-8')
TOKENS = (ROOT / 'assets/v1-tokens.css').read_text(encoding='utf-8')


def token(name):
    match = re.search(r'--' + re.escape(name) + r'\s*:\s*([^;]+);', TOKENS)
    if not match:
        raise AssertionError(f'assets/v1-tokens.css: token ausente --{name}')
    raw = match.group(1).strip()
    ref = re.fullmatch(r'var\(--([\w-]+)\)', raw)
    return token(ref.group(1)) if ref else raw


def luminance(color):
    digits = color.lstrip('#')
    if len(digits) == 3:
        digits = ''.join(c * 2 for c in digits)
    if len(digits) != 6:
        raise AssertionError(f'Color no hexadecimal: {color}')
    channels = [int(digits[i:i+2], 16) / 255 for i in (0, 2, 4)]
    channels = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    return sum(x * y for x, y in zip(channels, (.2126, .7152, .0722)))


def ratio(fg, bg):
    a, b = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (a + .05) / (b + .05)


class InteractiveColorStates(unittest.TestCase):
    def test_text_actions_normal_and_hover(self):
        self.assertIn('color:var(--color-accent)', BASE, 'assets/v1-base.css: falta color de acciones textuales')
        self.assertIn('color:var(--color-accent-hover)', BASE, 'assets/v1-base.css: falta color de hover/focus')
        for state, name in [('normal', 'color-accent'), ('hover/focus', 'color-accent-hover')]:
            with self.subTest(state=state):
                actual = ratio(token(name), token('surface-page'))
                self.assertGreaterEqual(actual, 4.5, f'assets/v1-base.css: acción textual {state}, --{name}, contraste {actual:.2f}:1')

    def test_header_buy_normal_and_hover(self):
        self.assertRegex(SHELL, r'\.header-buy\{[^}]*background:var\(--color-accent-strong\);color:#fff', 'assets/v1-shell-base.css: CTA sin combinación cromática esperada')
        self.assertRegex(SHELL, r'\.header-buy:hover,html\.v1 \.header-buy:focus-visible\{[^}]*background:var\(--dp-ink\)', 'assets/v1-shell-base.css: hover/focus del CTA sin fondo definido')
        for state, background in [('normal', 'color-accent-strong'), ('hover/focus', 'dp-ink')]:
            with self.subTest(state=state):
                actual = ratio('#ffffff', token(background))
                self.assertGreaterEqual(actual, 4.5, f'assets/v1-shell-base.css: .header-buy {state} contraste {actual:.2f}:1')


if __name__ == '__main__':
    unittest.main()
