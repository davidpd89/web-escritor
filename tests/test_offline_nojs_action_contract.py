import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class OfflineParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.html_classes = set()
        self.main_depth = 0
        self.headings = []
        self.paragraphs = []
        self.buttons = []
        self.actions_depth = 0
        self.action_buttons = []
        self.active = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set(a.get('class', '').split())
        if tag == 'html':
            self.html_classes = classes
        if tag == 'main':
            self.main_depth += 1
        if self.main_depth and tag == 'div' and 'actions' in classes:
            self.actions_depth += 1
        if self.main_depth and tag == 'h1':
            self.active = 'heading'
        if self.main_depth and tag == 'p':
            self.active = 'paragraph'
        if self.main_depth and tag == 'button':
            self.buttons.append(a)
            if self.actions_depth:
                self.action_buttons.append(a)

    def handle_data(self, data):
        if self.active == 'heading':
            self.headings.append(data)
        elif self.active == 'paragraph':
            self.paragraphs.append(data)

    def handle_endtag(self, tag):
        if tag in ('h1', 'p'):
            self.active = None
        if tag == 'div' and self.actions_depth:
            self.actions_depth -= 1
        if tag == 'main':
            self.main_depth -= 1


class OfflineNoJSContract(unittest.TestCase):
    def test_static_recovery_and_action_visibility(self):
        page = 'offline.html'
        html = (ROOT / page).read_text(encoding='utf-8')
        parser = OfflineParser()
        parser.feed(html)
        self.assertIn('no-js', parser.html_classes, f'{page}: falta estado inicial no-js')
        self.assertTrue(''.join(parser.headings).strip(), f'{page}: falta título de recuperación estático')
        self.assertTrue(any('conexión' in p.lower() or 'red' in p.lower() for p in parser.paragraphs), f'{page}: faltan instrucciones estáticas de recuperación')
        self.assertTrue(parser.buttons, f'{page}: no se han encontrado acciones de recuperación')
        self.assertEqual(len(parser.buttons), len(parser.action_buttons), f'{page}: hay botones de recuperación fuera del contenedor de acciones')
        self.assertRegex(html, r'(?s)\.no-js\s+\.actions\s*\{[^}]*display\s*:\s*none\s*;', f'{page}: el estado sin JS no oculta los botones dependientes de scripts')


if __name__ == '__main__':
    unittest.main()
