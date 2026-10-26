import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ('recomendaciones', 'editoriales', 'libros')
SAFE = {'no-referrer', 'same-origin', 'strict-origin', 'origin', 'strict-origin-when-cross-origin'}

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []
        self.external_links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('name', '').lower() == 'referrer':
            self.policies.append(attrs.get('content', '').lower().strip())
        if tag == 'a':
            href = attrs.get('href', '')
            if href.startswith(('https://', 'http://')) and not href.startswith(('https://davidportodiaz.com/', 'http://davidportodiaz.com/')):
                self.external_links.append(href)

class TestReferrerPrivacy(unittest.TestCase):
    def test_referrer_policy(self):
        checked = 0
        for family in FAMILIES:
            for path in sorted((ROOT / family).rglob('*.html')):
                parser = PageParser()
                parser.feed(path.read_text(encoding='utf-8'))
                if not parser.external_links:
                    continue
                with self.subTest(page=str(path.relative_to(ROOT))):
                    self.assertEqual(len(parser.policies), 1, f'{path}: política referrer ausente o duplicada: {parser.policies}')
                    self.assertIn(parser.policies[0], SAFE, f'{path}: política que puede filtrar rutas completas: {parser.policies[0]}')
                    checked += 1
        self.assertGreater(checked, 0, 'No se encontraron páginas con enlaces externos')

if __name__ == '__main__':
    unittest.main()