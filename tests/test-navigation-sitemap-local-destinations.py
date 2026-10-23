import re
import unittest
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1].resolve()
SITE = ROOT / 'mapa-del-sitio/index.html'


def resolve(href):
    path = unquote(urlsplit(href).path)
    if '\x00' in path or '\\' in path:
        raise ValueError(f'Unsafe URL: {href}')
    target = (ROOT / path.lstrip('/')).resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError(f'Escapes repository: {href}')
    if path.endswith('/'):
        target = target / 'index.html'
    return target


class HumanSitemapDestinations(unittest.TestCase):
    def test_each_directory_link_has_a_local_destination(self):
        html = SITE.read_text(encoding='utf-8')
        match = re.search(r'<div class="findability-directory">(.*?)</main>', html, re.S)
        self.assertIsNotNone(match)
        links = [unescape(h) for h in re.findall(r'<a\b[^>]*href="([^"]+)"', match.group(1))]
        internal = [h for h in links if h.startswith('/') and not h.startswith('//')]
        self.assertGreaterEqual(len(internal), 30)
        for href in internal:
            with self.subTest(href=href):
                target = resolve(href)
                self.assertTrue(target.is_file(), f'{href} -> {target.relative_to(ROOT)} absent')
                self.assertGreater(target.stat().st_size, 0)


if __name__ == '__main__':
    unittest.main()