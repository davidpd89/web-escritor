import re
import unittest
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONTHS = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}

class PublicText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'template'):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'template') and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

class EditorialCopy(unittest.TestCase):
    def test_public_copy(self):
        parser = PublicText()
        parser.feed((ROOT / 'lectores-beta/index.html').read_text(encoding='utf-8'))
        text = re.sub(r'\s+', ' ', ' '.join(parser.parts))
        self.assertGreater(len(text), 300, '/lectores-beta/: no se ha extraído contenido público suficiente')
        forbidden = [r'\bTODO\b', r'\bTBD\b', r'\bFIXME\b', r'\blorem ipsum\b', r'\btexto de prueba\b', r'\bpendiente de redactar\b', r'\[\[pendiente\]\]']
        for pattern in forbidden:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, text, re.I), f'/lectores-beta/: marcador editorial publicado: {pattern}')
        future = re.compile(r'(?:próxima convocatoria|inscripciones abiertas hasta|apúntate antes del)\s+(\d{1,2})\s+de\s+(' + '|'.join(MONTHS) + r')\s+de\s+(20\d{2})', re.I)
        for match in future.finditer(text):
            day, month, year = match.groups()
            deadline = date(int(year), MONTHS[month.lower()], int(day))
            self.assertGreaterEqual(deadline, date.today(), f'/lectores-beta/: convocatoria futura con fecha vencida {match.group(0)}')

if __name__ == '__main__':
    unittest.main()