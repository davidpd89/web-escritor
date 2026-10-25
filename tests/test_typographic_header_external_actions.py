import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


class HeaderLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'header':
            self.depth += 1
        if tag == 'a' and self.depth:
            self.links.append(values)

    def handle_endtag(self, tag):
        if tag == 'header' and self.depth:
            self.depth -= 1


class TypographicHeaderExternalActions(unittest.TestCase):
    def test_external_new_tabs_are_isolated(self):
        checked = 0
        for route in ('index.html', '404.html'):
            parser = HeaderLinks()
            parser.feed((ROOT / route).read_text(encoding='utf-8'))
            self.assertTrue(parser.links, f'{route}: no se encontraron enlaces de cabecera')
            for link in parser.links:
                href = link.get('href', '')
                parsed = urlsplit(href)
                if parsed.scheme not in ('http', 'https') or parsed.hostname == 'davidportodiaz.com':
                    continue
                if link.get('target', '').lower() != '_blank':
                    continue
                checked += 1
                rel = set(link.get('rel', '').lower().split())
                self.assertTrue({'noopener', 'noreferrer'} <= rel, f'{route}: enlace {href} sin aislamiento de pestaña: {sorted(rel)}')
        self.assertGreater(checked, 0, 'No se verificó ninguna acción externa de cabecera')


if __name__ == '__main__':
    unittest.main()
