import importlib.util
import json
import unittest
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from email.utils import parsedate_to_datetime

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pin_embargo',ROOT/'scripts/build-reading-pinterest-rss.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
CONFIG = json.loads((ROOT/'data/reading-pinterest-boards.json').read_text(encoding='utf-8'))

class PinterestEmbargo(unittest.TestCase):
    def test_scheduled_book_is_not_exposed_early(self):
        board = CONFIG['boards'][0]
        book = {'id':'libro-prueba','slug':'libro-prueba',
                'titulo':'Libro de prueba','autores':['Autora'],
                'descripcion_breve':'Descripción de prueba para lectores',
                'fecha_publicacion':'2026-01-01'}
        entry = {'book':book,'board':board,'image':'/assets/reading-covers/prueba.webp'}
        state = {'pins':{'libro-prueba':{
            'book_id':'libro-prueba','slug':'libro-prueba',
            'board_slug':board['slug'],
            'scheduled_date':'2026-10-26',
            'guid':'urn:davidportodiaz:pinterest:libro:libro-prueba:v1'}}}
        cases = [
            (date(2026,10,24),0),
            (date(2026,10,25),0),
            (date(2026,10,26),1),
            (date(2026,10,27),1),
        ]
        dates = []
        for today,count in cases:
            with self.subTest(today=today):
                xml = mod.build_feed(board,[entry],state,today,CONFIG['site'],30)
                items = ET.fromstring(xml).findall('./channel/item')
                self.assertEqual(len(items),count)
                if items:
                    dates.append(parsedate_to_datetime(items[0].findtext('pubDate')))
        self.assertEqual(len(dates),2)
        self.assertEqual(dates[0],dates[1])

if __name__ == '__main__':
    unittest.main()
