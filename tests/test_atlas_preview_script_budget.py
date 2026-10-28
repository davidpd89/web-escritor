import unittest
from html.parser import HTMLParser
from test_atlas_static_preview import fixture, mod


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.entries = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.entries.append(dict(attrs))


class AtlasScriptBudgetTest(unittest.TestCase):
    def test_no_executable_scripts_or_network_dependencies(self):
        for path, html in mod.pages_from(fixture()).items():
            with self.subTest(page=path):
                parser = Scripts()
                parser.feed(html)
                executable = [s for s in parser.entries if (s.get('type') or '').strip().lower() not in ('application/ld+json', 'application/json')]
                external = [s for s in parser.entries if s.get('src')]
                self.assertEqual(executable, [], f'{path}: scripts ejecutables: {executable}')
                self.assertEqual(external, [], f'{path}: peticiones externas de scripts: {external}')
                self.assertIn('<main', html, f'{path}: falta contenido principal estático')


if __name__ == '__main__':
    unittest.main()