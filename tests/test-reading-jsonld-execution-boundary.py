import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ('recomendaciones', 'editoriales', 'libros')

class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.active = None
        self.foreign_inside_json = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.active is not None:
            self.foreign_inside_json.append(tag)
        if tag == 'script' and attrs.get('type', '').lower() == 'application/ld+json':
            self.active = []

    def handle_data(self, data):
        if self.active is not None:
            self.active.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active is not None:
            self.blocks.append(''.join(self.active))
            self.active = None

class TestJSONLDBoundary(unittest.TestCase):
    def test_generated_documents(self):
        checked = 0
        for family in FAMILIES:
            for path in sorted((ROOT / family).rglob('*.html')):
                parser = Document()
                parser.feed(path.read_text(encoding='utf-8'))
                for index, block in enumerate(parser.blocks, 1):
                    with self.subTest(page=str(path.relative_to(ROOT)), block=index):
                        try:
                            value = json.loads(block)
                        except json.JSONDecodeError as exc:
                            self.fail(f'{path}: JSON-LD bloque {index} inválido: {exc}')
                        self.assertIsInstance(value, (dict, list), f'{path}: JSON-LD sin objeto o lista')
                        checked += 1
                self.assertFalse(parser.foreign_inside_json, f'{path}: elementos HTML dentro de JSON-LD: {parser.foreign_inside_json}')
        self.assertGreater(checked, 0, 'No se analizaron bloques JSON-LD reales')

if __name__ == '__main__':
    unittest.main()