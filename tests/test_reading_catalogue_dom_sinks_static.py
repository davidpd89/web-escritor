import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/reading-catalogue.js'


class ReadingCatalogueDOMSinkTest(unittest.TestCase):
    def test_no_interpreted_html_sinks(self):
        source = SOURCE.read_text(encoding='utf-8')
        forbidden = {
            'innerHTML': r'\.innerHTML\s*=(?!=)',
            'outerHTML': r'\.outerHTML\s*=(?!=)',
            'insertAdjacentHTML': r'\.insertAdjacentHTML\s*\(',
            'document.write': r'\bdocument\.write\s*\(',
            'Range.createContextualFragment': r'\.createContextualFragment\s*\(',
        }
        for label, pattern in forbidden.items():
            with self.subTest(sink=label):
                matches = list(re.finditer(pattern, source))
                locations = [source.count('\n', 0, m.start()) + 1 for m in matches]
                self.assertFalse(locations, f'{SOURCE}: destino HTML {label} en líneas {locations}')

    def test_market_links_are_validated_before_rendering(self):
        source = SOURCE.read_text(encoding='utf-8')
        self.assertRegex(source, r'const\s+safeURL\s*=')
        self.assertRegex(source, r'const\s+validOffer\s*=')
        self.assertRegex(source, r'const\s+validRating\s*=')
        self.assertRegex(source, r'market\.offers\.filter\(validOffer\)')
        self.assertRegex(source, r'market\.ratings\.filter\(validRating\)')
        self.assertIn("u.protocol === 'https:'", source)
        self.assertIn('!u.username', source)
        self.assertIn('!u.password', source)
        self.assertIn('!u.port', source)

    def test_market_text_is_rendered_as_text(self):
        source = SOURCE.read_text(encoding='utf-8')
        self.assertRegex(source, r'link\.textContent\s*=')
        self.assertRegex(source, r'link\.append\(')
        self.assertRegex(source, r'box\.replaceChildren\(')


if __name__ == '__main__':
    unittest.main()
