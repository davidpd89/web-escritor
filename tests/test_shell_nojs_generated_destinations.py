import importlib.util
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('site_shell_under_test', ROOT / 'scripts/build-site-shell.py')
MODULE = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class LinksInNoscript(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'noscript':
            self.depth += 1
        elif tag == 'a' and self.depth:
            self.links.add(attrs.get('href'))

    def handle_endtag(self, tag):
        if tag == 'noscript':
            self.depth -= 1


class ShellNoJSNavigation(unittest.TestCase):
    def test_generated_header_preserves_essential_destinations(self):
        nav, registry, extras = MODULE.shell_sources()
        required = {'/libros/', '/recomendaciones/', '/herramientas/'}
        for page in ('index.html', '404.html'):
            with self.subTest(page=page):
                source = (ROOT / page).read_text(encoding='utf-8')
                generated = MODULE.apply_shell(source, page, nav, registry, extras)
                parser = LinksInNoscript()
                parser.feed(generated)
                missing = required - parser.links
                self.assertFalse(missing, f'{page}: destinos sin JS ausentes: {sorted(missing)}; encontrados={sorted(str(x) for x in parser.links)}')


if __name__ == '__main__':
    unittest.main()
