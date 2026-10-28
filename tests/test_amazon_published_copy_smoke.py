import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / 'data/reading-catalogue.json'
PLACEHOLDERS = re.compile(r'\b(?:lorem ipsum|texto de prueba|texto pendiente|pendiente de redactar|sinopsis pendiente|todo:|tbd)\b|\[\[pendiente\]\]', re.I)

class PublishedCommercialCopySmoke(unittest.TestCase):
    def test_published_commercial_cards_have_real_copy(self):
        catalogue = json.loads(CATALOGUE.read_text(encoding='utf-8'))
        books = [book for book in catalogue['libros'] if book.get('estado') == 'publicado' and (book.get('url_amazon_afiliada') or book.get('formatos_compra') or book.get('amazon_busqueda_isbn'))]
        self.assertTrue(books, 'data/reading-catalogue.json: no se encontraron libros publicados con acceso comercial')
        for book in books:
            with self.subTest(book=book.get('id')):
                title = book.get('titulo')
                self.assertIsInstance(title, str, f"{book.get('id')}: título ausente")
                self.assertGreaterEqual(len(title.strip()), 2, f"{book['id']}: título vacío o ilegible")
                description = book.get('descripcion_breve') or book.get('sinopsis_breve')
                self.assertIsInstance(description, str, f"{book['id']}: falta descripción comercial")
                self.assertGreaterEqual(len(description.strip()), 35, f"{book['id']}: descripción insuficiente: {description!r}")
                for field, value in [('titulo', title), ('descripcion', description)]:
                    self.assertIsNone(PLACEHOLDERS.search(value), f"{book['id']}: marcador editorial en {field}: {value!r}")

if __name__ == '__main__':
    unittest.main()
