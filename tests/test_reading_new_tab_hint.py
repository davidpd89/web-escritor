"""Todo enlace del catálogo que abre otra pestaña lo anuncia a quien no ve la flecha (WCAG G201)."""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth, self.open, self.links = 0, None, []

    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.depth += 1
        if tag == 'a' and self.depth:
            self.open = {**dict(attrs), 'text': ''}

    def handle_endtag(self, tag):
        if tag == 'main':
            self.depth -= 1
        if tag == 'a' and self.open is not None:
            self.links.append(self.open)
            self.open = None

    def handle_data(self, data):
        if self.open is not None:
            self.open['text'] += data


class NewTabHintTest(unittest.TestCase):
    def test_every_new_tab_link_says_so(self):
        pages = [ROOT / "recomendaciones/index.html", *sorted(ROOT.glob("recomendaciones/*/*/index.html"))]
        self.assertGreater(len(pages), 100)
        missing = set()
        for page in pages:
            parser = Anchors()
            parser.feed(page.read_text(encoding='utf-8'))
            for a in parser.links:
                name = a.get('aria-label') or a['text']
                if a.get('target') == '_blank' and 'otra pestaña' not in name:
                    missing.add(re.sub(r'\s+', ' ', name).strip()[:40] + ' · ' + a.get('class', ''))
        self.assertEqual(sorted(missing)[:10], [])


if __name__ == '__main__':
    unittest.main()
