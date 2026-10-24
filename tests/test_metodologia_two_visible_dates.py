import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TwoVisibleDates(unittest.TestCase):
    def test_both_dates_are_explained_in_details(self):
        raw = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
        method = (ROOT / 'metodologia-editorial/index.html').read_text(encoding='utf-8')
        self.assertIn('última comprobación', method)
        self.assertIn('última actualización de la página', method)
        for record in raw['publishers']:
            if not record.get('publish'):
                continue
            with self.subTest(slug=record['slug']):
                detail = (ROOT / 'editoriales' / record['slug'] / 'index.html').read_text(encoding='utf-8')
                body = detail.split('<main id="contenido"', 1)[-1].split('</main>', 1)[0]
                self.assertIn('Última comprobación', body)
                self.assertIn('Última actualización de la página', body)
                self.assertIn('datetime="{}"'.format(record['verified_at']), body)
                self.assertIn('datetime="{}"'.format(record['page_updated_at']), body)

if __name__ == '__main__':
    unittest.main()