from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = 'ai/index.html'
IMPORT = re.compile(r'@import\s+(?:url\(\s*)?[\'\"]?([^\s\)\'\";]+)', re.I)

class Stylesheets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == 'link':
            data = dict(attrs)
            if 'stylesheet' in data.get('rel', '').lower().split():
                self.hrefs.append(data.get('href', ''))

class TestAICSSDependencies(unittest.TestCase):
    def test_all_stylesheets_resolve(self):
        parser = Stylesheets()
        parser.feed((ROOT / PAGE).read_text(encoding='utf-8'))
        self.assertTrue(parser.hrefs, f'{PAGE}: no se encontraron hojas CSS')
        visited = set()

        def inspect(href, parent):
            parts = urlsplit(href)
            self.assertFalse(parts.scheme or parts.netloc, f'{parent}: dependencia CSS externa: {href}')
            if parts.path.startswith('/'):
                candidate = ROOT / unquote(parts.path).lstrip('/')
            else:
                candidate = parent.parent / unquote(parts.path)
            candidate = candidate.resolve()
            self.assertTrue(candidate.is_relative_to(ROOT.resolve()), f'{parent}: CSS fuera del repositorio: {href}')
            self.assertTrue(candidate.is_file(), f'{PAGE}: recurso CSS inexistente: {href}, referenciado desde {parent}')
            self.assertEqual(candidate.suffix.lower(), '.css', f'{PAGE}: dependencia con extensión inesperada: {candidate}')
            if candidate in visited:
                return
            visited.add(candidate)
            content = candidate.read_text(encoding='utf-8')
            for imported in IMPORT.findall(re.sub(r'/\*.*?\*/', '', content, flags=re.S)):
                inspect(imported, candidate)

        for href in parser.hrefs:
            inspect(href, ROOT / PAGE)
        self.assertIn((ROOT / 'assets/v1-ai-authority.css').resolve(), visited, f'{PAGE}: falta la hoja específica de autoridad')

if __name__ == '__main__':
    unittest.main()
