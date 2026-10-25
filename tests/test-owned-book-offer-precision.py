import json
import re
import unittest
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from pathlib import Path

PAGE = Path(__file__).resolve().parents[1] / 'las-manecillas-del-recuerdo/index.html'

class JSONScripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []
        self.documents = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.active = dict(attrs).get('type') == 'application/ld+json'
            self.parts = []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.documents.append(json.loads(''.join(self.parts)))
            self.active = False

def offers(value):
    if isinstance(value, list):
        for child in value:
            yield from offers(child)
    elif isinstance(value, dict):
        kind = value.get('@type', [])
        if kind == 'Offer' or isinstance(kind, list) and 'Offer' in kind:
            yield value
        for child in value.values():
            yield from offers(child)

class TestOfferPrecision(unittest.TestCase):
    def test_published_offers(self):
        parser = JSONScripts()
        parser.feed(PAGE.read_text(encoding='utf-8'))
        found = [offer for document in parser.documents for offer in offers(document) if 'price' in offer]
        self.assertTrue(found, f'{PAGE}: ninguna oferta con precio; comprobación vacía')
        for offer in found:
            with self.subTest(offer=offer.get('url', offer.get('@id', 'sin-id'))):
                self.assertEqual(offer.get('priceCurrency'), 'EUR', f'{PAGE}: moneda de oferta incorrecta: {offer}')
                raw = str(offer['price'])
                self.assertRegex(raw, r'^\d+(?:\.\d{1,2})?$', f'{PAGE}: precio mal formado: {raw}')
                try:
                    amount = Decimal(raw)
                except InvalidOperation:
                    self.fail(f'{PAGE}: precio no decimal: {raw}')
                self.assertGreater(amount, 0, f'{PAGE}: precio no positivo: {raw}')
                self.assertEqual(amount * 100, (amount * 100).to_integral_value(), f'{PAGE}: precio sin precisión de céntimos: {raw}')

if __name__ == '__main__':
    unittest.main()