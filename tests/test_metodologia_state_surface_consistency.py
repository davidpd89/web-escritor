import html
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'open': 'Acepta manuscritos', 'closed': 'Recepción cerrada', 'indirect': 'Vía indirecta', 'award_only': 'Solo convocatoria/premio', 'unknown': 'Estado por verificar'}

class StateSurfaceConsistency(unittest.TestCase):
    def test_all_published_states(self):
        data = json.loads((ROOT / 'data/editoriales.json').read_text(encoding='utf-8'))
        index = (ROOT / 'editoriales/index.html').read_text(encoding='utf-8')
        for record in data['publishers']:
            if not record.get('publish'):
                continue
            with self.subTest(slug=record['slug']):
                status = record['status']
                self.assertIn(status, LABELS)
                if status != 'open':
                    self.assertFalse(record['direct_submission'], 'Estado no abierto con recepción directa')
                detail = (ROOT / 'editoriales' / record['slug'] / 'index.html').read_text(encoding='utf-8')
                self.assertIn('<dt>Estado de originales</dt> <dd>{}</dd>'.format(LABELS[status]), detail)
                self.assertIn('data-status="{}"'.format(status), detail if 'data-editorial-card' in detail else index)
                self.assertIn('href="/editoriales/{}/"'.format(record['slug']), index)
                if status != 'open':
                    self.assertNotIn('mailto:', detail)

if __name__ == '__main__':
    unittest.main()