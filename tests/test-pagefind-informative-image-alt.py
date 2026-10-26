import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Images(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = dict(attrs)
        if tag == 'a':
            self.links.append({'attrs': a, 'text': '', 'images': []})
        elif tag == 'img':
            self.images.append((a, self.links[-1] if self.links else None))
            if self.links:
                self.links[-1]['images'].append(a)

    def handle_data(self, data):
        if self.links:
            self.links[-1]['text'] += data

    def handle_endtag(self, tag):
        if tag.lower() == 'a' and self.links:
            self.links.pop()

class ImageAlternatives(unittest.TestCase):
    def test_real_content_images_have_accessible_equivalents(self):
        pages = json.loads((ROOT / 'pagefind/eligible-manifest.json').read_text(encoding='utf-8'))['pages']
        checked = 0
        for route in pages:
            parser = Images()
            parser.feed((ROOT / route).read_text(encoding='utf-8'))
            for attrs, link in parser.images:
                checked += 1
                alt = attrs.get('alt')
                self.assertIsNotNone(alt, f'{route}: img sin atributo alt: {attrs.get("src", "")}' )
                if alt and alt.strip():
                    continue
                if attrs.get('aria-label', '').strip() or attrs.get('aria-labelledby', '').strip():
                    continue
                if attrs.get('role', '').lower() in {'presentation', 'none'} or attrs.get('aria-hidden', '').lower() == 'true':
                    continue
                if link is not None:
                    a = link['attrs']
                    named = bool(a.get('aria-label', '').strip() or a.get('aria-labelledby', '').strip() or link['text'].strip())
                    self.assertTrue(named, f'{route}: enlace gráfico sin nombre accesible: {a.get("href", "")}; imagen={attrs.get("src", "")}')
        self.assertGreater(checked, 0, 'No se encontraron imágenes reales para verificar')

if __name__ == '__main__':
    unittest.main()