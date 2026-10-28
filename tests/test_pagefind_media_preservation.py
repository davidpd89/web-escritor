import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('pagefind_media_preservation', ROOT / 'scripts/build-pagefind-index.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
MEDIA = {'img', 'picture', 'source', 'video', 'audio', 'track'}

class MediaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag in MEDIA:
            self.items.append(('start', tag, tuple(attrs)))

    def handle_startendtag(self, tag, attrs):
        if tag in MEDIA:
            self.items.append(('empty', tag, tuple(attrs)))

    def handle_endtag(self, tag):
        if tag in MEDIA:
            self.items.append(('end', tag))

def media(text):
    parser = MediaParser()
    parser.feed(text)
    return parser.items

class PagefindMediaPreservation(unittest.TestCase):
    def test_registry_title_injection_preserves_media(self):
        registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
        checked = 0
        for rel in BUILDER.eligible_pages(ROOT):
            original = (ROOT / rel).read_text(encoding='utf-8')
            entries = [entry for entry in registry['entries'] if entry.get('sourceFile') == rel and entry.get('label')]
            if not entries:
                continue
            transformed = BUILDER.inject_registry_search_title(original, entries[0])
            before = media(original)
            after = media(transformed)
            self.assertEqual(before, after, f'{rel}: Pagefind altera elementos o atributos multimedia')
            checked += 1
        self.assertGreater(checked, 0, 'No se verificaron páginas indexables con etiqueta editorial')

if __name__ == '__main__':
    unittest.main()
