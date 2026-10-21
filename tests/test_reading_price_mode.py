"""El modo de precios no debe publicar comparativas con afiliación Amazon.

Tests sintéticos; el navegador/HTML generados necesitan QA tras habilitación.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_builder_price_mode', ROOT / 'scripts/build-reading-catalogue.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PriceModeTest(unittest.TestCase):
    def setUp(self):
        self.book = {
            'isbn13': '9788401039560', 'fuente_bibliografica_url':
            'https://www.penguinlibros.com/es/libros-de-fantasia/635029-libro-otros-mundos-el-talisman-3-9788401039560'
        }

    def test_official_canonical_book_destination_only(self):
        self.assertEqual(mod.publisher_purchase_destination(self.book), self.book['fuente_bibliografica_url'])
        for other in [
            'https://www.amazon.es/dp/B123456789',
            'https://www.penguinlibros.com/es/libros-de-fantasia/635029-libro-otros-mundos-el-talisman-3-9788401039546',
            'https://www.penguinlibros.com/es/libros-de-fantasia/635029-libro-otros-mundos-el-talisman-3-9788401039560?utm=x',
            'https://www.penguinlibros.com.evil.tld/es/libros-de-fantasia/635029-libro-otros-mundos-el-talisman-3-9788401039560',
        ]:
            with self.subTest(other=other):
                self.assertIsNone(mod.publisher_purchase_destination({**self.book, 'fuente_bibliografica_url': other}))

    def test_mode_requires_explicit_publisher_choice(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(mod.purchase_price_mode(root), 'amazon_affiliate')
            (root / 'data').mkdir()
            config = root / 'data/reading-intake-config.json'
            config.write_text(json.dumps({'purchase_price_mode': 'publisher_only'}), encoding='utf-8')
            self.assertEqual(mod.purchase_price_mode(root), 'publisher_only')
            config.write_text(json.dumps({'purchase_price_mode': 'unknown'}), encoding='utf-8')
            with self.assertRaises(mod.ValidationError):
                mod.purchase_price_mode(root)

    def test_publisher_hub_does_not_render_amazon_cta(self):
        data = {'categorias': [], 'libro_categorias': []}
        book = {**self.book, 'id': 'isbn-9788401039560', 'titulo': 'Una obra',
                'slug': 'una-obra', 'estado': 'publicado', 'autores': ['Autora ficticia'],
                'descripcion_breve': 'Una descripción de prueba.', 'fecha_actualizacion': '2026-10-21',
                'edicion': 'Tapa dura', 'portada_local': '/assets/reading-covers/isbn-9788401039560.webp',
                'portada_ancho': 400, 'portada_alto': 600,
                'amazon_busqueda_isbn': 'https://www.amazon.es/s?k=9788401039560&tag=davidporto-21'}
        with unittest.mock.patch.object(mod, 'author_links', return_value='Autora ficticia'):
            with unittest.mock.patch.object(mod, 'inject_shell_auto', side_effect=lambda html: html):
                output = mod.render_hub(data, [book], '<main data-reading-catalogue data-family="recomendaciones">{{catalogue}}</main>', 'publisher_only')
        self.assertIn('data-price-mode="publisher_only"', output)
        self.assertIn('Consultar precio en Penguin Libros', output)
        self.assertNotIn('href="https://www.amazon.es/', output)


if __name__ == '__main__':
    unittest.main()
