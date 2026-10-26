import importlib.util
import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('reading_builder_commerce_component', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class FactsParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text = []
    def handle_data(self, data):
        self.text.append(data)

class CommerceHomogeneity(unittest.TestCase):
    def test_price_and_purchase_components(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        checked = 0
        prices = 0
        for book in data['libros']:
            if book['estado'] != 'publicado':
                continue
            destination = builder.amazon_destination(book)
            expected_destination = book.get('url_amazon_afiliada') or book.get('amazon_busqueda_isbn')
            self.assertEqual(destination, expected_destination, f'{book["slug"]}: destino de compra modificado')
            self.assertEqual(builder.amazon_action_label(book), 'Comprar en Amazon', f'{book["slug"]}: etiqueta de compra distinta')
            if book.get('pvp_centimos') is not None:
                label = builder.pvp_label(book)
                cents = book['pvp_centimos']
                self.assertEqual(label, f'{cents // 100},{cents % 100:02d} €', f'{book["slug"]}: precio incorrecto: {label}')
                self.assertRegex(label, r'^\d+,\d{2} €$', f'{book["slug"]}: formato monetario no homogéneo')
                parser = FactsParser()
                parser.feed(builder.facts(book))
                self.assertIn(label, ''.join(parser.text), f'{book["slug"]}: precio ausente de los datos visibles')
                prices += 1
            checked += 1
        self.assertGreater(checked, 0, 'No hay libros publicados')
        self.assertGreater(prices, 0, 'No se han comprobado precios reales del catálogo')

if __name__ == '__main__':
    unittest.main()