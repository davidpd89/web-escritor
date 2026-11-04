"""Usabilidad del catálogo: compra junto a la cabecera, edades ordenadas y precios por formato.

Usa datos y plantillas reales; sin peticiones HTTP.
"""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reading_catalogue_navigation_ux", ROOT / "scripts/build-reading-catalogue.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class CatalogueNavigationUX(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/reading-catalogue.json").read_text(encoding="utf-8"))
        cls.template = (ROOT / "scripts/templates/reading-catalogue.html.tmpl").read_text(encoding="utf-8")
        builder.OWN_TEXTS.clear()
        builder.OWN_TEXTS.update(builder.load_own_texts(ROOT))
        cls.books = builder.validate(cls.data, ROOT)
        cls.hub = '\n'.join(builder.render_hub(cls.data, cls.books, cls.template, n)
                            for n in range(1, max(1, builder.math.ceil(len(cls.books) / builder.CATALOGUE_PAGE_SIZE)) + 1))

    def test_amazon_box_follows_the_heading_before_the_orientation_texts(self):
        priced = [b for b in self.books if builder.amazon_prices(b) and builder.own_text_section(b, self.data)]
        self.assertTrue(priced)
        for b in priced[:20]:
            html = builder.render_book(self.data, b, self.template)
            heading_end = html.index('</header>', html.index('catalogue-book-heading'))
            formats, buy = html.index('catalogue-formats', heading_end), html.index('catalogue-buy-link', heading_end)
            self.assertLess(max(formats, buy), html.index('catalogue-own-text'), b['id'])
            self.assertLess(max(formats, buy), html.index('data-catalogue-description'), b['id'])

    def test_age_filter_lists_adults_juvenile_then_ages_from_youngest(self):
        group = re.search(r'data-facet-group="edad".*?</details>', self.hub, re.S).group(0)
        ids = re.findall(r'value="([^"]+)" data-facet="edad"', group)
        named = [i for i in ('adultos', 'juvenil') if i in ids]
        self.assertEqual(ids[:len(named)], named)
        ages = [[int(n) for n in re.findall(r'\d+', i)] for i in ids[len(named):]]
        self.assertEqual(ages, sorted(ages, key=lambda a: (a[0], a[-1] if len(a) > 1 else 99)))
        order = [builder.age_order({'id': i}) for i in ('edad-a-partir-de-9-anos', 'adultos', 'edad-a-partir-de-4-anos', 'juvenil', 'edad-de-0-a-3-anos')]
        self.assertEqual(sorted(order), [builder.age_order({'id': i}) for i in ('adultos', 'juvenil', 'edad-de-0-a-3-anos', 'edad-a-partir-de-4-anos', 'edad-a-partir-de-9-anos')])

    def test_price_sort_and_filter_are_per_format(self):
        sort = re.search(r'<select name="orden".*?</select>', self.hub, re.S).group(0)
        self.assertNotIn('precio_asc', sort)
        for key, label in builder.FORMATS.items():
            self.assertIn(f'value="precio_{key}">{label} · del más barato al más caro', sort)
        self.assertIn('data-filter="precio_formato"', self.hub)
        for b in self.books:
            expected = ' '.join(f"{o['formato']}:{o['precio_centimos']}" for o in builder.amazon_prices(b))
            self.assertIn(f'data-book-id="{b["id"]}"', self.hub)
            card = re.search(r'data-book-id="' + re.escape(b['id']) + r'"[^>]*', self.hub).group(0)
            actual = re.search(r'data-format-prices="([^"]*)"', card)
            self.assertEqual(actual.group(1) if actual else '', expected, b['id'])


if __name__ == "__main__":
    unittest.main()


class CatalogueDealsAndFilters(unittest.TestCase):
    def test_deals_feed_and_card_discounts(self):
        option = {'formato': 'ebook', 'url': 'https://www.amazon.es/dp/B000000001?tag=x', 'fuente_url': 'https://www.amazon.es/dp/B000000001',
                  'fecha_verificacion': '2026-11-03', 'precio_centimos': 750, 'precio_anterior_centimos': 1000, 'bajada_fecha': '2026-11-03'}
        book = {'id': 'lib-1', 'slug': 'libro', 'titulo': 'Libro', 'autores': ['A'], 'portada_local': '/assets/reading-covers/x.webp', 'formatos_compra': [option]}
        self.assertEqual(builder.format_discounts(book), 'ebook:25')
        deals = json.loads(builder.render_deals([book]))['ofertas']
        self.assertEqual([(d['descuento_pct'], d['tipo'], d['precio_antes_centimos']) for d in deals], [(25, 'bajada', 1000)])
        book['formatos_compra'] = [{k: v for k, v in option.items() if k not in ('precio_anterior_centimos', 'bajada_fecha')}]
        self.assertEqual(builder.format_discounts(book), '')
        self.assertEqual(json.loads(builder.render_deals([book]))['ofertas'], [])

    def test_filters_drop_epoch_and_unknown_pages(self):
        html = (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
        self.assertNotIn('data-facet-group="epoca"', html)
        self.assertNotIn('Páginas sin confirmar', html)
        self.assertIn('data-filter="estado"', html)
        self.assertIn('value="menos-3"', html)
        self.assertIn('value="5"', html)
