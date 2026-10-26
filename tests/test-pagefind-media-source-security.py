import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]

class MediaParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.references = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() not in {'img', 'source', 'video', 'audio', 'track'}:
            return
        a = dict(attrs)
        for key in ('src', 'poster'):
            if a.get(key):
                self.references.append((tag, key, a[key]))
        if a.get('srcset'):
            for candidate in a['srcset'].split(','):
                parts = candidate.strip().split()
                if parts:
                    self.references.append((tag, 'srcset', parts[0]))

class MediaSecurity(unittest.TestCase):
    def test_real_indexed_media_have_safe_sources(self):
        pages = json.loads((ROOT / 'pagefind/eligible-manifest.json').read_text(encoding='utf-8'))['pages']
        checked = 0
        for route in pages:
            parser = MediaParser()
            parser.feed((ROOT / route).read_text(encoding='utf-8'))
            for tag, attribute, value in parser.references:
                checked += 1
                normalized = re.sub(r'[\x00-\x20\x7f]+', '', value).lower()
                self.assertFalse(normalized.startswith(('http:', 'javascript:', 'vbscript:', 'file:', 'blob:')), f'{route}: {tag}[{attribute}] inseguro: {value}')
                if normalized.startswith('data:'):
                    self.assertRegex(normalized, r'^data:image/(?:png|gif|jpeg|webp|svg\+xml);', f'{route}: recurso data no permitido: {value}')
                    continue
                parsed = urlsplit(value)
                self.assertIn(parsed.scheme.lower(), {'', 'https'}, f'{route}: esquema inseguro: {value}')
                self.assertFalse(parsed.username or parsed.password, f'{route}: credenciales en recurso: {value}')
                self.assertFalse(value.startswith('//'), f'{route}: origen sin protocolo: {value}')
        self.assertGreater(checked, 0, 'No se inspeccionó ningún recurso multimedia real del corpus')

if __name__ == '__main__':
    unittest.main()