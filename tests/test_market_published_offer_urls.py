import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]


def priced():
    """Amazon prices now live per format in the catalogue (formatos_compra)."""
    catalogue = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
    return [(book, option) for book in catalogue['libros']
            for option in book.get('formatos_compra', []) if 'precio_centimos' in option]


class PublishedOfferURLs(unittest.TestCase):
    def test_priced_purchase_destinations(self):
        self.assertTrue(priced(), 'reading-catalogue.json: no hay enlaces con precio que verificar')
        for book, option in priced():
            url = option['url']
            label = f'{book["id"]}/{option["formato"]}'
            with self.subTest(price=label):
                parsed = urlsplit(url)
                self.assertEqual(parsed.scheme, 'https', f'{label}: esquema inseguro: {url}')
                self.assertIn(parsed.hostname, ('amazon.es', 'www.amazon.es'), f'{label}: destino inesperado: {url}')
                self.assertIsNone(parsed.username, f'{label}: URL con credenciales')
                self.assertIn(parsed.port, (None, 443), f'{label}: puerto no permitido')
                self.assertRegex(parsed.path, r'^/(?:dp|gp/product)/[A-Z0-9]{10}/?$', f'{label}: producto no identificable: {url}')
                tags = parse_qs(parsed.query).get('tag', [])
                self.assertEqual(len(tags), 1, f'{label}: etiqueta de afiliación ausente o duplicada: {url}')
                self.assertRegex(tags[0], r'^[A-Za-z0-9-]+$', f'{label}: etiqueta inválida: {url}')
                self.assertFalse(parsed.fragment, f'{label}: fragmento inesperado: {url}')

if __name__ == '__main__':
    unittest.main()
