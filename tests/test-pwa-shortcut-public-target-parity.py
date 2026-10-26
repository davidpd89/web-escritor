import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://davidportodiaz.com'


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = None
        self.noindex = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and 'canonical' in attrs.get('rel', '').lower().split():
            self.canonical = attrs.get('href')
        if tag == 'meta' and attrs.get('name', '').lower() == 'robots':
            self.noindex |= 'noindex' in re.split(r'[\s,]+', attrs.get('content', '').lower())


class PWAShortcutParity(unittest.TestCase):
    def test_published_shortcuts(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        shortcuts = manifest['shortcuts']
        self.assertGreater(len(shortcuts), 0, 'manifest.json: no contiene accesos directos')
        urls = []
        for shortcut in shortcuts:
            url = shortcut['url']
            parsed = urlsplit(url)
            self.assertEqual(parsed.scheme, '', f'manifest.json: acceso externo {url}')
            self.assertEqual(parsed.netloc, '', f'manifest.json: autoridad externa {url}')
            self.assertTrue(parsed.path.startswith('/'), f'manifest.json: ruta no absoluta {url}')
            self.assertFalse(parsed.query or parsed.fragment, f'manifest.json: acceso no canónico {url}')
            urls.append(url)
            relative = parsed.path.lstrip('/')
            file = ROOT / (relative + 'index.html' if relative.endswith('/') else relative)
            self.assertTrue(file.is_file(), f'manifest.json: destino inexistente {url} ({file})')
            parser = MetadataParser()
            parser.feed(file.read_text(encoding='utf-8'))
            self.assertFalse(parser.noindex, f'{url}: acceso directo a página noindex')
            self.assertIsNotNone(parser.canonical, f'{url}: falta canonical')
            canonical = urlsplit(parser.canonical)
            self.assertEqual(canonical.scheme, 'https', f'{url}: canonical sin HTTPS')
            self.assertEqual(canonical.netloc, urlsplit(ORIGIN).netloc, f'{url}: canonical fuera del origen')
        self.assertEqual(len(urls), len(set(urls)), 'manifest.json: accesos directos duplicados')


if __name__ == '__main__':
    unittest.main()