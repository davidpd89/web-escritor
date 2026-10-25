import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.main = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'main':
            self.main = True
        if tag == 'a' and self.main:
            self.links.append(a)

    def handle_endtag(self, tag):
        if tag == 'main':
            self.main = False

class TestOutboundPolicy(unittest.TestCase):
    def test_documentary_external_links(self):
        total = 0
        for filename in ('eventos.html', 'ferias.html'):
            parser = Anchors()
            parser.feed((ROOT / filename).read_text(encoding='utf-8'))
            for link in parser.links:
                href = link.get('href', '')
                parsed = urlsplit(href)
                if not parsed.netloc:
                    continue
                total += 1
                with self.subTest(page=filename, href=href):
                    self.assertEqual(parsed.scheme, 'https')
                    self.assertFalse(parsed.username or parsed.password)
                    self.assertFalse(any(ord(c) < 32 for c in href))
                    if link.get('target') == '_blank':
                        rel = set(link.get('rel', '').lower().split())
                        self.assertTrue({'noopener', 'noreferrer'} <= rel, f'Faltan protecciones: {href}')
        self.assertGreater(total, 0, 'No se encontraron enlaces documentales externos')

if __name__ == '__main__':
    unittest.main()
