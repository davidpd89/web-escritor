import json
import math
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/radar-opportunities.json'

class RadarPublishedFeePrecision(unittest.TestCase):
    def test_real_published_fees_have_exact_cent_precision(self):
        data = json.loads(SOURCE.read_text(encoding='utf-8'))
        checked = 0
        for item in data['items']:
            if not item.get('published'):
                continue
            checked += 1
            fee = item['fee_eur']
            if fee is None:
                continue
            with self.subTest(id=item['id'], fee=fee):
                self.assertIsInstance(
                    fee, (int, float),
                    f"{item['id']}: fee_eur no numérico: {fee!r}",
                )
                self.assertNotIsInstance(
                    fee, bool,
                    f"{item['id']}: fee_eur booleano: {fee!r}",
                )
                self.assertTrue(
                    math.isfinite(fee) and fee >= 0,
                    f"{item['id']}: fee_eur no finito o negativo: {fee!r}",
                )
                cents = Decimal(str(fee)) * 100
                self.assertEqual(
                    cents, cents.to_integral_value(),
                    f"{item['id']}: fee_eur={fee!r} no admite céntimos exactos",
                )
        self.assertGreater(checked, 0, 'No hay cuotas publicadas para verificar')

if __name__ == '__main__':
    unittest.main()
