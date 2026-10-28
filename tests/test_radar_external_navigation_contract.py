import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

PAGE = Path(__file__).resolve().parents[1] / 'convocatorias-escritores/index.html'


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.active = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and 'data-radar-source' in a:
            self.active = {'attrs': a, 'text': ''}

    def handle_data(self, data):
        if self.active is not None:
            self.active['text'] += data

    def handle_endtag(self, tag):
        if tag == 'a' and self.active is not None:
            self.links.append(self.active)
            self.active = None


class ExternalNavigation(unittest.TestCase):
    def test_source_links(self):
        parser = Links()
        parser.feed(PAGE.read_text(encoding='utf-8'))
        self.assertTrue(parser.links, '/convocatorias-escritores/: faltan enlaces de consulta')
        for link in parser.links:
            a = link['attrs']
            href = a.get('href', '')
            parsed = urlsplit(href)
            self.assertEqual(parsed.scheme, 'https', f'/convocatorias-escritores/: URL no HTTPS: {href}')
            self.assertTrue(parsed.hostname, f'/convocatorias-escritores/: host ausente: {href}')
            self.assertTrue(link['text'].strip() or a.get('aria-label'), f'/convocatorias-escritores/: enlace sin nombre: {href}')
            if a.get('target', '').lower() == '_blank':
                rel = set(a.get('rel', '').lower().split())
                self.assertTrue({'noopener', 'noreferrer'} <= rel, f'/convocatorias-escritores/: rel inseguro: {href}')


if __name__ == '__main__':
    unittest.main()
