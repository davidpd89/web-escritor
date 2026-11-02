"""Caja de formatos de Amazon, enlace en español y calendario de lanzamientos con enlace de compra."""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_catalogue_formats', ROOT / 'scripts/build-reading-catalogue.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

URL = 'https://www.amazon.es/dp/B0TEST1234?tag=davidporto-21'
BOOK = {'id': 'lib-1', 'titulo': 'El volumen del tiempo', 'autores': ['Solvej Balle'], 'editorial': 'Anagrama',
        'fecha_publicacion': '2999-01-01', 'fecha_actualizacion': '2026-11-01', 'slug': 'el-volumen-del-tiempo',
        'formatos_compra': [{'formato': 'ebook', 'url': URL, 'precio_centimos': 1044},
                            {'formato': 'tapa-blanda', 'url': URL.replace('B0TEST1234', '8433929000')}]}


class FormatBoxTest(unittest.TestCase):
    def test_four_formats_always_in_the_same_order_with_price_or_cross(self):
        box = m.format_box(BOOK)
        order = [box.index(f'data-{kind}-format="{f}"') for f, kind in
                 (('tapa-dura', 'missing'), ('tapa-blanda', 'purchase'), ('ebook', 'purchase'), ('audiolibro', 'missing'))]
        self.assertEqual(order, sorted(order))
        self.assertIn('<span>Kindle</span><strong>10,44 €</strong>', box)
        self.assertIn('<span>Tapa blanda</span><strong>Ver precio</strong>', box)
        self.assertEqual(box.count('✕'), 2)
        self.assertEqual(box.count('rel="sponsored nofollow noopener noreferrer"'), 2)
        self.assertIn('<h2>Formatos y precios en Amazon</h2>', box)
        card = m.format_box(BOOK, compact=True)
        self.assertIn('catalogue-formats--card', card)
        self.assertNotIn('<h2>', card)

    def test_main_button_names_and_highlights_the_format_it_buys(self):
        self.assertEqual(m.primary_format(BOOK), 'tapa-blanda')
        box = m.format_box(BOOK)
        self.assertEqual(box.count('is-primary'), 1)
        self.assertIn('catalogue-format is-primary" data-purchase-format="tapa-blanda"', box)
        self.assertNotIn('is-primary', m.format_box(BOOK, compact=True))
        search = {**BOOK, 'formatos_compra': [], 'amazon_busqueda_isbn': 'https://www.amazon.es/s?k=9788433929000&tag=davidporto-21'}
        self.assertIsNone(m.primary_format(search))
        self.assertNotIn('is-primary', m.format_box(search))

    def test_book_without_amazon_formats_shows_four_crosses(self):
        self.assertEqual(m.format_box({**BOOK, 'formatos_compra': []}).count('is-missing'), 4)

    def test_amazon_links_ask_for_spanish(self):
        self.assertEqual(m.amazon_es(URL), URL + '&language=es_ES')
        self.assertEqual(m.amazon_es('https://www.amazon.es/dp/X'), 'https://www.amazon.es/dp/X?language=es_ES')
        self.assertEqual(m.amazon_es(URL + '&language=es_ES'), URL + '&language=es_ES')
        self.assertEqual(m.amazon_es('https://www.example.com/x'), 'https://www.example.com/x')
        self.assertIsNone(m.amazon_es(None))
        self.assertIn('language=es_ES', m.format_box(BOOK))

    def test_release_calendar_carries_the_tagged_amazon_link(self):
        ics = m.render_release_ics([BOOK]).replace('\r\n ', '')
        self.assertIn('Comprar en Amazon: ' + m.amazon_destination(BOOK), ics)
        self.assertIn('tag=davidporto-21', ics)
        self.assertIn('Ficha: ' + m.SITE + m.url(BOOK), ics)

    def test_real_catalogue_has_no_catch_all_type(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        groups = {m.book_group(m.categories(data, b)) for b in data['libros'] if b['estado'] == 'publicado'}
        self.assertNotIn('otros', groups)
        self.assertIn('poesia', groups)
        self.assertNotIn('Otros', m.render_filters(data, m.group_options(dict.fromkeys(groups, 1))))


if __name__ == '__main__':
    unittest.main()
