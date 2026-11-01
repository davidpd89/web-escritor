import json
import re
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTC_FORMAT = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')

class PublishedOfferChronology(unittest.TestCase):
    def test_offer_validity_interval(self):
        market = json.loads((ROOT / 'assets/reading-market.json').read_text(encoding='utf-8'))
        self.assertTrue(market['offers'], 'reading-market.json: no hay fechas comerciales que comprobar')
        for offer in market['offers']:
            label = f'{offer["libro_id"]}/{offer["formato"]}'
            with self.subTest(offer=label):
                values = []
                for field in ('actualizado_en', 'caduca_en'):
                    value = offer[field]
                    self.assertIsInstance(value, str, f'{label}: {field} no es texto')
                    self.assertRegex(value, UTC_FORMAT, f'{label}: {field} no es UTC: {value}')
                    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    self.assertEqual(parsed.isoformat(timespec='seconds').replace('+00:00', 'Z'), value, f'{label}: {field} no representa una fecha UTC válida')
                    values.append(parsed)
                start, end = values
                self.assertGreater(end, start, f'{label}: precio caducado antes de su actualización')
                self.assertLessEqual(end - start, timedelta(days=7), f'{label}: vigencia comercial superior a 7 días')

if __name__ == '__main__':
    unittest.main()
