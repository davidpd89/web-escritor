import html
import json
import pathlib
import re
import unittest
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/tools-hub.json'
TARGET = ROOT / 'herramientas/index.html'


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'template'):
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'template') and self.ignored:
            self.ignored -= 1

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def plain(value):
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()


class ToolsDirectoryTextParity(unittest.TestCase):
    def test_tool_names_survive_html_projection(self):
        tools = json.loads(SOURCE.read_text(encoding='utf-8'))['tools']
        self.assertTrue(tools, f'{SOURCE}: inventario vacío')
        self.assertTrue(TARGET.is_file(), f'{TARGET}: directorio inexistente')
        parser = TextParser()
        parser.feed(TARGET.read_text(encoding='utf-8'))
        visible = plain(' '.join(parser.parts))
        self.assertNotIn('\ufffd', visible, f'{TARGET}: texto Unicode deteriorado')
        for tool in tools:
            name = plain(tool['name'])
            self.assertTrue(name, f'{SOURCE}: herramienta {tool.get("slug")} sin nombre')
            self.assertIn(name, visible, f'{TARGET}: falta el nombre {name!r} de {SOURCE}')


if __name__ == '__main__':
    unittest.main()
