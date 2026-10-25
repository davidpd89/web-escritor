import json
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class MarketFormatUniqueness(unittest.TestCase):
    def test_one_published_offer_per_book_and_format(self):
        market = json.loads((ROOT / 'assets/reading-market.json').read_text(encoding='utf-8'))
        grouped = defaultdict(list)
        for offer in market['offers']:
            grouped[(offer['libro_id'], offer['formato'])].append(offer)
        self.assertTrue(grouped, 'reading-market.json: no hay formatos comerciales que comprobar')
        for (book_id, fmt), offers in grouped.items():
            self.assertEqual(len(offers), 1, f'reading-market.json: {book_id}, formato {fmt}: {len(offers)} ofertas contradictorias; precios={[o.get("precio_centimos") for o in offers]}')

if __name__ == '__main__':
    unittest.main()
