import importlib.util
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('site_shell_recovery', ROOT / 'scripts/build-site-shell.py')
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class MainContent(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = set()
        self.headings = []
        self.in_h1 = False

    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.depth += 1
        elif self.depth and tag == 'a':
            href = dict(attrs).get('href')
            if href:
                self.links.add(href)
        elif self.depth and tag == 'h1':
            self.in_h1 = True

    def handle_data(self, data):
        if self.in_h1:
            self.headings.append(data)

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.in_h1 = False
        elif tag == 'main':
            self.depth -= 1


class RecoveryPreservation(unittest.TestCase):
    def test_recovery_survives_shell_generation(self):
        source = (ROOT / '404.html').read_text(encoding='utf-8')
        nav, registry, extras = MODULE.shell_sources()
        output = MODULE.apply_shell(source, '404.html', nav, registry, extras)
        before, after = MainContent(), MainContent()
        before.feed(source)
        after.feed(output)
        self.assertTrue(after.headings, '404.html: falta el encabezado principal tras generar shell')
        self.assertEqual(before.links, after.links, f'404.html: los enlaces de recuperación cambiaron: antes={sorted(before.links)}, después={sorted(after.links)}')
        self.assertIn('/', after.links, '404.html: no existe enlace estático de retorno al inicio')
        self.assertGreaterEqual(len(after.links), 4, f'404.html: solo quedan {len(after.links)} destinos de recuperación')
        for href in after.links:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or not parsed.path.startswith('/'):
                continue
            target = parsed.path.lstrip('/')
            candidates = [ROOT / target / 'index.html', ROOT / target]
            self.assertTrue(any(p.is_file() for p in candidates), f'404.html: destino de recuperación inexistente: {href}')


if __name__ == '__main__':
    unittest.main()
