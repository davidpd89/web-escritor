import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]

class PublishedOfferURLs(unittest.TestCase):
    def test_published_purchase_destinations(self):
        market = json.loads((ROOT / 'assets/reading-market.json').read_text(encoding='utf-8'))
        offers = market['offers']
        self.assertTrue(offers, 'reading-market.json: no hay ofertas que verificar')
        for offer in offers:
            with self.subTest(book=offer.get('libro_id'), format=offer.get('formato')):
                url = offer['url']
                parsed = urlsplit(url)
                self.assertEqual(parsed.scheme, 'https', f'{offer["libro_id"]}: esquema inseguro: {url}')
                self.assertIn(parsed.hostname, ('amazon.es', 'www.amazon.es'), f'{offer["libro_id"]}: destino comercial inesperado: {url}')
                self.assertIsNone(parsed.username, f'{offer["libro_id"]}: URL con credenciales')
                self.assertIsNone(parsed.password, f'{offer["libro_id"]}: URL con credenciales')
                self.assertIn(parsed.port, (None, 443), f'{offer["libro_id"]}: puerto no permitido')
                self.assertRegex(parsed.path, r'^/(?:dp|gp/product)/[A-Z0-9]{10}/?$', f'{offer["libro_id"]}: producto no identificable: {url}')
                tags = parse_qs(parsed.query).get('tag', [])
                self.assertEqual(len(tags), 1, f'{offer["libro_id"]}: etiqueta de afiliación ausente o duplicada: {url}')
                self.assertRegex(tags[0], r'^[A-Za-z0-9-]+$', f'{offer["libro_id"]}: etiqueta inválida: {url}')
                self.assertFalse(parsed.fragment, f'{offer["libro_id"]}: fragmento inesperado: {url}')

if __name__ == '__main__':
    unittest.main()
