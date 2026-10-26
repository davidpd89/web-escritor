import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class GraphicLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = dict(attrs)
        if tag == 'a':
            self.stack.append({'href': a.get('href', ''), 'target': a.get('target', ''), 'rel': a.get('rel', ''), 'graphic': False})
        elif tag in {'img', 'svg'}:
            for link in self.stack:
                link['graphic'] = True

    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self.stack:
            self.links.append(self.stack.pop())

class LinkIsolation(unittest.TestCase):
    def test_graphic_external_blank_links_are_isolated(self):
        pages = json.loads((ROOT / 'pagefind/eligible-manifest.json').read_text(encoding='utf-8'))['pages']
        self.assertIn('mapa-del-sitio/index.html', pages)
        checked = 0
        for route in pages:
            parser = GraphicLinks()
            parser.feed((ROOT / route).read_text(encoding='utf-8'))
            for link in parser.links:
                if not link['graphic'] or link['target'].lower() != '_blank':
                    continue
                url = urlsplit(link['href'])
                if url.scheme.lower() not in {'http', 'https'} or url.hostname == 'davidportodiaz.com':
                    continue
                checked += 1
                tokens = set(link['rel'].lower().split())
                self.assertTrue(tokens.intersection({'noopener', 'noreferrer'}), f'{route}: enlace gráfico externo sin aislamiento: {link["href"]}, rel={link["rel"]!r}')
        self.assertGreater(checked, 0, 'No se verificó ningún enlace gráfico externo del corpus')

if __name__ == '__main__':
    unittest.main()