#!/usr/bin/env python3
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = False
        self.main = False
    def handle_starttag(self, tag, attrs):
        if tag == 'title': self.title = True
        if tag == 'main': self.main = True

class TestManifestShortcuts(unittest.TestCase):
    def test_shortcuts_have_real_documents(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
        shortcuts = manifest.get('shortcuts', [])
        self.assertTrue(shortcuts, 'manifest.json: no hay accesos directos')
        for shortcut in shortcuts:
            url = shortcut['url']
            with self.subTest(url=url):
                parsed = urlsplit(url)
                self.assertFalse(parsed.scheme or parsed.netloc, f'{url}: destino externo')
                self.assertTrue(parsed.path.startswith('/'), f'{url}: ruta no absoluta')
                path = ROOT / unquote(parsed.path).lstrip('/')
                if path.is_dir(): path /= 'index.html'
                self.assertTrue(path.is_file(), f'{url}: documento inexistente')
                document = Document()
                document.feed(path.read_text(encoding='utf-8'))
                self.assertTrue(document.title, f'{url}: falta title')
                self.assertTrue(document.main, f'{url}: falta main')

if __name__ == '__main__': unittest.main()
