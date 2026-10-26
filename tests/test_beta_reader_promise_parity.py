import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, value):
        self.parts.append(value)

class PromiseParity(unittest.TestCase):
    def test_beta_program_copy(self):
        source = (ROOT / 'lectores-beta/index.html').read_text(encoding='utf-8')
        parser = TextParser()
        parser.feed(source)
        text = re.sub(r'\s+', ' ', ' '.join(parser.parts)).casefold()
        for phrase in ['no es la newsletter general', 'dos listas y dos consentimientos distintos', 'sin publicar', 'opinión']:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text, f'/lectores-beta/: falta la explicación «{phrase}»')
        self.assertRegex(source, r'data-newsletter-source=[\"\']lectores-beta[\"\']', '/lectores-beta/: el formulario debe identificar el programa beta')
        self.assertIn('lectores-beta-gdpr', source, '/lectores-beta/: falta el consentimiento específico')

if __name__ == '__main__':
    unittest.main()