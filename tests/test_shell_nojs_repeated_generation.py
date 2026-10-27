import importlib.util
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('site_shell_repeat', ROOT / 'scripts/build-site-shell.py')
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class NoscriptLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'noscript':
            self.depth += 1
        elif tag == 'a' and self.depth:
            href = dict(attrs).get('href')
            if href:
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag == 'noscript':
            self.depth -= 1


def destinations(html):
    parser = NoscriptLinks()
    parser.feed(html)
    return parser.links


class RepeatedShellGeneration(unittest.TestCase):
    def test_repeated_generation_preserves_nojs_navigation(self):
        nav, registry, extras = MODULE.shell_sources()
        for page in ('index.html', '404.html'):
            with self.subTest(page=page):
                original = (ROOT / page).read_text(encoding='utf-8')
                once = MODULE.apply_shell(original, page, nav, registry, extras)
                twice = MODULE.apply_shell(once, page, nav, registry, extras)
                self.assertEqual(once, twice, f'{page}: la segunda regeneración modifica el documento')
                self.assertEqual(destinations(once), destinations(twice), f'{page}: cambia la navegación sin JS después de regenerar')
                self.assertTrue(destinations(twice), f'{page}: no quedan enlaces noscript después de regenerar')


if __name__ == '__main__':
    unittest.main()
