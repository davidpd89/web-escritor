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
        cls.hub = builder.render_hub(cls.data, cls.books, cls.template)

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
            self.assertIn(f'data-format-prices="{expected}"', card, b['id'])


if __name__ == "__main__":
    unittest.main()
