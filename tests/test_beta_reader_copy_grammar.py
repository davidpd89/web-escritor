import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class MainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.depth += 1
        elif self.depth and tag not in {'br', 'img', 'input', 'meta', 'link', 'hr', 'source'}:
            self.depth += 1
    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1
    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)

class BetaGrammar(unittest.TestCase):
    def test_author_reader_person(self):
        parser = MainText()
        parser.feed((ROOT / 'lectores-beta/index.html').read_text(encoding='utf-8'))
        text = re.sub(r'\s+', ' ', ' '.join(parser.parts))
        self.assertIn('Qué implica apuntarte', text, '/lectores-beta/: falta el apartado de condiciones')
        self.assertNotRegex(text, r'\bPuede pedirte tu opinión\b', '/lectores-beta/: «Puede pedirte» cambia la persona gramatical; corresponde «Puedo pedirte»')

if __name__ == '__main__':
    unittest.main()