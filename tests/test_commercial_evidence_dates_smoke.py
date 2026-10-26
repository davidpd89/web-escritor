import json
import re
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CommercialEvidenceDatesSmoke(unittest.TestCase):
    def test_published_commercial_evidence_has_real_dates(self):
        catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        today = datetime.now(timezone.utc).date()
        checked = 0
        for book in catalogue['libros']:
            if book.get('estado') != 'publicado':
                continue
            entries = [('formatos_compra', entry) for entry in book.get('formatos_compra', [])]
            entries += [('resenas', entry) for entry in book.get('resenas', [])]
            for section, entry in entries:
                if 'fecha_verificacion' not in entry:
                    continue
                checked += 1
                value = entry['fecha_verificacion']
                context = f"data/reading-catalogue.json libro={book['id']} sección={section} fecha={value!r}"
                self.assertIsInstance(value, str, f'{context}: fecha no textual')
                self.assertRegex(value, r'^\d{4}-\d{2}-\d{2}$', f'{context}: formato distinto de AAAA-MM-DD')
                try:
                    verified = date.fromisoformat(value)
                except ValueError:
                    self.fail(f'{context}: fecha imposible')
                self.assertLessEqual(verified, today, f'{context}: evidencia fechada en el futuro')
        self.assertGreater(checked, 0, 'data/reading-catalogue.json: ninguna evidencia comercial fechada fue examinada')

if __name__ == '__main__':
    unittest.main()
