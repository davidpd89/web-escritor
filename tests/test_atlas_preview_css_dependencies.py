import re
import unittest
from html.parser import HTMLParser
from test_atlas_static_preview import fixture, mod


class Styles(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.inline = []
        self.inside_style = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'link' and 'stylesheet' in (a.get('rel') or '').lower().split():
            self.links.append(a)
        if tag == 'style':
            self.inside_style = True
        if 'style' in a:
            self.inline.append(a['style'])

    def handle_data(self, data):
        if self.inside_style:
            self.inline.append(data)

    def handle_endtag(self, tag):
        if tag == 'style':
            self.inside_style = False


class AtlasCSSDependenciesTest(unittest.TestCase):
    def test_preview_has_no_network_css_dependencies(self):
        for path, html in mod.pages_from(fixture()).items():
            with self.subTest(page=path):
                parser = Styles()
                parser.feed(html)
                self.assertEqual(parser.links, [], f'{path}: hojas CSS bloqueantes: {parser.links}')
                css = '\n'.join(parser.inline)
                self.assertIsNone(re.search(r'@import\s|url\s*\(', css, re.I), f'{path}: dependencia CSS de red o importación inesperada')
                self.assertIn('<h1>', html, f'{path}: falta el encabezado estático principal')


if __name__ == '__main__':
    unittest.main()