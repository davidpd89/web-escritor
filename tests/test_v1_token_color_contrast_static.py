import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / 'assets/v1-tokens.css').read_text(encoding='utf-8')


def token(name):
    match = re.search(r'--' + re.escape(name) + r'\s*:\s*([^;]+);', CSS)
    if not match:
        raise AssertionError(f'assets/v1-tokens.css: falta --{name}')
    return match.group(1).strip()


def resolve(name, seen=None):
    seen = set() if seen is None else seen
    if name in seen:
        raise AssertionError(f'Referencia circular en --{name}')
    value = token(name)
    ref = re.fullmatch(r'var\(--([\w-]+)\)', value)
    return resolve(ref.group(1), seen | {name}) if ref else value


def rgb(value):
    if not re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?', value):
        raise AssertionError(f'Color no hexadecimal: {value}')
    digits = value[1:]
    if len(digits) == 3:
        digits = ''.join(x * 2 for x in digits)
    return [int(digits[i:i+2], 16) / 255 for i in (0, 2, 4)]


def luminance(value):
    channels = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in rgb(value)]
    return sum(a * b for a, b in zip(channels, (.2126, .7152, .0722)))


def contrast(fg, bg):
    a, b = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (a + .05) / (b + .05)


class TokenContrastTest(unittest.TestCase):
    def test_real_editorial_text_pairs(self):
        pairs = [
            ('--color-text', '--surface-page', 4.5),
            ('--color-muted', '--surface-page', 4.5),
            ('--color-accent', '--surface-page', 4.5),
            ('--color-accent-hover', '--surface-page', 4.5),
            ('--dp-petrol-ink', '--surface-page', 4.5),
            ('--color-on-inverse', '--surface-inverse', 4.5),
        ]
        for foreground, background, minimum in pairs:
            with self.subTest(foreground=foreground, background=background):
                fg, bg = resolve(foreground[2:]), resolve(background[2:])
                actual = contrast(fg, bg)
                self.assertGreaterEqual(actual, minimum, f'assets/v1-tokens.css: {foreground}={fg} sobre {background}={bg}: {actual:.2f}:1, mínimo {minimum}:1')


if __name__ == '__main__':
    unittest.main()
