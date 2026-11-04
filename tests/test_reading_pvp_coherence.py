"""El PVP editorial y el precio de Amazon de la misma encuadernación tienen que ser coherentes.

Con la ley del precio fijo, Amazon vende un libro nuevo a su PVP o hasta un 5 % por debajo. Si lo vende a más de
1,5 veces el PVP, el PVP se extrajo mal. 2026-11-04: Nórdica publica en el JSON-LD el precio del ebook que vende su
tienda, y 14 fichas mostraban un PVP de ebook (10,99 €) para un papel de 21,50 €.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 1.5


def incoherent(books):
    out = []
    for book in books:
        pvp, edition = book.get('pvp_centimos'), book.get('formato_edicion')
        for offer in book.get('formatos_compra') or []:
            price = offer.get('precio_centimos')
            if pvp and price and offer.get('formato') == edition and price > pvp * LIMIT:
                out.append(f"{book['id']}: {edition} a {price} céntimos con PVP {pvp}")
    return out


class PvpCoherence(unittest.TestCase):
    def test_detects_ebook_price_stored_as_pvp(self):
        book = {'id': 'x', 'pvp_centimos': 1099, 'formato_edicion': 'tapa-blanda',
                'formatos_compra': [{'formato': 'tapa-blanda', 'precio_centimos': 2042},
                                    {'formato': 'ebook', 'precio_centimos': 1044}]}
        self.assertEqual(incoherent([book]), ['x: tapa-blanda a 2042 céntimos con PVP 1099'])
        book['pvp_centimos'] = 2150
        self.assertEqual(incoherent([book]), [])

    def test_catalogue_pvp_matches_amazon_for_the_same_binding(self):
        books = json.loads((ROOT / 'data' / 'reading-catalogue.json').read_text(encoding='utf-8'))['libros']
        self.assertEqual(incoherent(books), [], 'PVP incoherente con Amazon: revisa el extractor de la fuente')


if __name__ == '__main__':
    unittest.main()
