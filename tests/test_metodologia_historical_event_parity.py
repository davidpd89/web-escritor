import html
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class HistoricalEventParity(unittest.TestCase):
    def test_all_events_have_visible_evidence(self):
        raw = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
        for record in raw['publishers']:
            if not record.get('publish'):
                continue
            page = (ROOT / 'editoriales' / record['slug'] / 'index.html').read_text(encoding='utf-8')
            marker = '<h2>Historial de comprobaciones y cambios</h2>'
            self.assertIn(marker, page)
            history = page.split(marker, 1)[1].split('</ul>', 1)[0]
            self.assertEqual(history.count('<li>'), len(record['history']), record['slug'])
            for event in record['history']:
                with self.subTest(slug=record['slug'], date=event['date']):
                    self.assertIn('<time datetime="{0}">{0}</time>'.format(event['date']), history)
                    self.assertIn(html.escape(event['event'], quote=True), history)
                    if event['source_url'] in record.get('unavailable_urls', []):
                        self.assertIn('enlace no disponible', history)
                    else:
                        self.assertIn('href="{}"'.format(html.escape(event['source_url'], quote=True)), history)

if __name__ == '__main__':
    unittest.main()