import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['autor.html', 'cuaderno/index.html', 'recomendaciones/index.html', 'las-manecillas-del-recuerdo/fragmentos/index.html', 'herramientas/index.html', 'libros/index.html']


def route_of(source):
    if source == 'index.html':
        return '/'
    if source.endswith('/index.html'):
        return '/' + source[:-10]
    return '/' + source


class ContextCurrentRoute(unittest.TestCase):
    def test_active_context_link_identifies_its_document(self):
        inspected = 0
        for source in PAGES:
            html = (ROOT / source).read_text(encoding='utf-8')
            blocks = re.findall(r'<nav\b[^>]*class="section-context"[^>]*>(.*?)</nav>', html, re.S)
            for block in blocks:
                inspected += 1
                active = re.findall(r'<a\b(?=[^>]*aria-current="page")[^>]*href="([^"]+)"[^>]*>', block)
                self.assertLessEqual(len(active), 1, source)
                for href in active:
                    with self.subTest(source=source, href=href):
                        self.assertEqual(urlsplit(href).path, route_of(source))
        self.assertGreaterEqual(inspected, 4)


if __name__ == '__main__':
    unittest.main()