import json
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/editoriales.json'


def valid_date(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
        return parsed.isoformat() == value
    except ValueError:
        return False


def normalized_url(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            return None
        return (parsed.hostname.lower(), parsed.port or 443, parsed.path.rstrip('/') or '/', parsed.query)
    except ValueError:
        return None


class EditorialHistorySourceClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = json.loads(DATA.read_text(encoding='utf-8'))['publishers']

    def test_history_sources_and_dates(self):
        self.assertGreater(len(self.records), 0)
        checked = 0
        for record in self.records:
            with self.subTest(editorial=record['slug']):
                sources = {normalized_url(source.get('url')) for source in record['sources']}
                self.assertNotIn(None, sources)
                self.assertTrue(sources)
                history = record.get('history', [])
                self.assertTrue(history, 'Expediente sin historial documental')
                for event in history:
                    checked += 1
                    self.assertTrue(valid_date(event.get('date')), 'Fecha histórica inválida')
                    self.assertGreaterEqual(len(event.get('event', '').strip()), 20)
                    url = normalized_url(event.get('source_url'))
                    self.assertIsNotNone(url, 'Fuente histórica no HTTPS')
                    self.assertIn(url, sources, 'Fuente histórica no declarada en el expediente')
                    self.assertLessEqual(event['date'], record['page_updated_at'])
        self.assertGreater(checked, 0)


if __name__ == '__main__':
    unittest.main()
