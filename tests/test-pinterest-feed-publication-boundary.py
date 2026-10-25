import importlib.util
import unittest
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pinterest_feed', ROOT / 'scripts/build-reading-pinterest-rss.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class FeedBoundaryTests(unittest.TestCase):
    def test_publication_day_boundaries(self):
        today = date(2026, 10, 25)
        board = {'slug': 'fantasia', 'name': 'Fantasía', 'description': 'Lecturas de fantasía', 'keyword': 'fantasía'}
        book = {'id': 'lib-0001', 'slug': 'obra', 'titulo': 'Obra', 'autores': ['Autora'], 'descripcion_breve': 'Una novela de fantasía con una historia completa.'}
        entries = [{'book': book, 'board': board, 'image': '/assets/reading-covers/obra.jpg'}]
        for offset in (-1, 0, 1):
            scheduled = today + timedelta(days=offset)
            state = {'pins': {'lib-0001': {'book_id': 'lib-0001', 'slug': 'obra', 'board_slug': 'fantasia', 'scheduled_date': scheduled.isoformat(), 'guid': 'urn:davidportodiaz:pinterest:libro:lib-0001:v1'}}}
            for delta in (-1, 0, 1):
                clock = scheduled + timedelta(days=delta)
                with self.subTest(offset=offset, delta=delta):
                    xml = module.build_feed(board, entries, state, clock, 'https://davidportodiaz.com', 150)
                    items = ET.fromstring(xml).findall('./channel/item')
                    self.assertEqual(len(items), int(delta >= 0))
                    if items:
                        self.assertEqual(items[0].findtext('guid'), state['pins']['lib-0001']['guid'])

if __name__ == '__main__':
    unittest.main()