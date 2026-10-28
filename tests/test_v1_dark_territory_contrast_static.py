import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / 'assets/v1-tokens.css').read_text(encoding='utf-8')


def declarations():
    match = re.search(r'html\.v1\s*\{([^}]+)\}', CSS)
    if not match:
        raise AssertionError('assets/v1-tokens.css: falta bloque territorial html.v1')
    return dict(re.findall(r'(--[\w-]+)\s*:\s*([^;]+);', match.group(1)))


def root_tokens():
    match = re.search(r':root\s*\{([^}]+)\}', CSS)
    if not match:
        raise AssertionError('assets/v1-tokens.css: falta :root')
    return dict(re.findall(r'(--[\w-]+)\s*:\s*([^;]+);', match.group(1)))


def channels(color):
    raw = color.strip().lstrip('#')
    if len(raw) == 3:
        raw = ''.join(c * 2 for c in raw)
    if len(raw) != 6:
        raise AssertionError(f'Color inesperado: {color}')
    return [int(raw[i:i+2], 16) / 255 for i in (0, 2, 4)]


def luminance(rgb):
    values = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in rgb]
    return sum(a * b for a, b in zip(values, (.2126, .7152, .0722)))


def contrast(a, b):
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return (x + .05) / (y + .05)


def resolve(value, tokens):
    value = value.strip()
    ref = re.fullmatch(r'var\((--[\w-]+)\)', value)
    if ref:
        return resolve(tokens[ref.group(1)], tokens)
    return channels(value)


def mix(value, tokens):
    match = re.fullmatch(r'color-mix\(in srgb,\s*var\((--[\w-]+)\)\s+(\d+)%,\s*var\((--[\w-]+)\)\)', value.strip())
    if not match:
        raise AssertionError(f'assets/v1-tokens.css: mezcla territorial no reconocida: {value}')
    first, percent, second = match.groups()
    weight = int(percent) / 100
    a, b = resolve(tokens[first], tokens), resolve(tokens[second], tokens)
    return [x * weight + y * (1 - weight) for x, y in zip(a, b)]


class DarkTerritoryContrast(unittest.TestCase):
    def test_dark_territory_color_pairs(self):
        territory = declarations()
        tokens = {**root_tokens(), **territory}
        background = resolve(territory['--territory-bg'], tokens)
        cases = [
            ('--territory-text', 4.5),
            ('--territory-muted', 4.5),
            ('--territory-focus', 3.0),
        ]
        for name, minimum in cases:
            with self.subTest(token=name):
                value = territory[name]
                foreground = mix(value, tokens) if value.startswith('color-mix(') else resolve(value, tokens)
                actual = contrast(foreground, background)
                self.assertGreaterEqual(actual, minimum, f'assets/v1-tokens.css: {name} sobre --territory-bg: {actual:.2f}:1, mínimo {minimum}:1')

    def test_dark_territory_is_not_global(self):
        root = root_tokens()
        territory = declarations()
        for name in ('--territory-bg', '--territory-text', '--territory-muted', '--territory-focus'):
            with self.subTest(token=name):
                self.assertIn(name, territory, f'assets/v1-tokens.css: {name} no está delimitado a html.v1')
                self.assertNotIn(name, root, f'assets/v1-tokens.css: {name} invade :root')


if __name__ == '__main__':
    unittest.main()
