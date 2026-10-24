import re
import unittest
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ('cuaderno', 'fragmento', 'universo', 'recomendaciones',
            'asistente', 'gracias-suscripcion', 'convocatorias-escritores',
            'accesibilidad', 'herramientas', 'lecturas', 'editoriales')
ROOT_PAGES = ('eventos.html','ferias.html','premios.html',
              '404.html','offline.html','privacidad.html')
CIVIL = re.compile(r'^\d{4}-\d{2}-\d{2}$')
INSTANT = re.compile(r'^\d{4}-\d{2}-\d{2}T')

class TimeCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []
    def handle_starttag(self, tag, attrs):
        if tag == 'time':
            attributes = dict(attrs)
            if 'datetime' in attributes:
                self.values.append((self.getpos()[0], attributes['datetime']))

class CrossFamilyDates(unittest.TestCase):
    def test_every_calendar_time_is_valid(self):
        paths = [ROOT / x for x in ROOT_PAGES]
        for family in FAMILIES:
            base = ROOT / family
            if base.is_dir():
                paths.extend(base.rglob('*.html'))
        paths = sorted(set(p for p in paths if p.is_file()))
        self.assertGreater(len(paths), 10)
        checked = 0
        for path in paths:
            parser = TimeCollector()
            parser.feed(path.read_text(encoding='utf-8'))
            for line, raw in parser.values:
                with self.subTest(page=str(path.relative_to(ROOT)), line=line, raw=raw):
                    if CIVIL.fullmatch(raw):
                        date.fromisoformat(raw)
                        checked += 1
                    elif INSTANT.match(raw):
                        dt = datetime.fromisoformat(raw.replace('Z','+00:00'))
                        self.assertTrue(0 <= dt.hour <= 23)
                        checked += 1
        self.assertGreater(checked, 0)

if __name__ == '__main__':
    unittest.main()
