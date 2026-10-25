import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get('id'):
            self.ids.add(data['id'])
        if tag == 'a' and data.get('name'):
            self.ids.add(data['name'])

class NavigationDestinationResolution(unittest.TestCase):
    def test_navigation_documents_and_fragments(self):
        nav = json.loads((ROOT / 'data/navigation.json').read_text(encoding='utf-8'))
        registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
        entries = {entry['id']: entry for entry in registry['entries']}
        ids = set(nav.get('header', []) + nav.get('homeMap', []))
        for section in ('footer', 'localNavSets'):
            for group in nav.get(section, {}).values():
                ids.update(group)
        for group in nav.get('menu', {}).values():
            ids.update(item['targetId'] for item in group)
        checked = 0
        for target in sorted(ids):
            entry = entries.get(target)
            if not entry:
                continue
            parsed = urlsplit(entry['url'])
            if parsed.scheme or parsed.netloc:
                continue
            path = unquote(parsed.path)
            source = entry.get('sourceFile')
            file = ROOT / source if source else ROOT / path.lstrip('/')
            if file.is_dir():
                file = file / 'index.html'
            if not file.is_file() and not file.suffix:
                file = file / 'index.html'
            checked += 1
            with self.subTest(target=target, url=entry['url']):
                self.assertTrue(file.is_file(), f'{target}: {entry["url"]} no resuelve a HTML público ({file})')
                if file.is_file() and parsed.fragment:
                    parser = Anchors()
                    parser.feed(file.read_text(encoding='utf-8'))
                    self.assertIn(unquote(parsed.fragment), parser.ids, f'{target}: ancla #{parsed.fragment} inexistente en {file}')
        self.assertGreater(checked, 0, 'No se comprobaron destinos de navegación')

if __name__ == '__main__':
    unittest.main()