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
        option = {'formato': 'tapa-blanda', 'url': 'https://www.amazon.es/dp/B000000001?tag=x', 'fuente_url': 'https://www.amazon.es/dp/B000000001',
                  'fecha_verificacion': '2026-11-04', 'precio_centimos': 1329, 'precio_referencia_centimos': 1899}
        book = {'id': 'lib-1', 'slug': 'libro', 'titulo': 'Libro', 'autores': ['A'], 'portada_local': '/assets/reading-covers/x.webp',
                'fecha_actualizacion': '2026-11-05', 'formatos_compra': [option]}
        self.assertEqual(builder.format_discounts(book, '2026-11-05'), 'tapa-blanda:30:2026-11-04')
        # Audible: el -30 % es el precio de socio, no una oferta (2026-11-05: colaba libros en «25 % o más»).
        audible = {**book, 'formatos_compra': [{**option, 'formato': 'audiolibro'}]}
        self.assertEqual(builder.format_discounts(audible, '2026-11-05'), '')
        deals = json.loads(builder.render_deals([book]))['ofertas']
        self.assertEqual([(d['descuento_pct'], d['tipo'], d['precio_antes_centimos']) for d in deals], [(30, 'descuento', 1899)])
        # Red percentage next to the price, with the check date the browser uses to expire it.
        box = builder.format_box(book, compact=True, anchor='2026-11-05')
        self.assertIn('13,29 € <em class="catalogue-format__off" data-offer-checked="2026-11-04">-30 %</em>', box)
        # Expired check: no badge, no filter entry, no deal.
        self.assertEqual(builder.format_discounts(book, '2026-11-09'), '')
        self.assertNotIn('catalogue-format__off', builder.format_box(book, anchor='2026-11-09'))
        book['fecha_actualizacion'] = '2026-11-09'
        self.assertEqual(json.loads(builder.render_deals([book]))['ofertas'], [])
        # A drop against an earlier price of ours is not an offer.
        book['formatos_compra'] = [{k: v for k, v in option.items() if k != 'precio_referencia_centimos'} | {'precio_anterior_centimos': 2000}]
        self.assertEqual(builder.format_discounts(book), '')

    def test_published_cards_show_every_current_discount(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = [b for b in data['libros'] if b['estado'] == 'publicado']
        anchor = builder.data_anchor(books)
        pages = [ROOT / 'recomendaciones/index.html', *sorted((ROOT / 'recomendaciones/pagina').glob('*/index.html'))]
        html = ''.join(p.read_text(encoding='utf-8') for p in pages)
        expected = sum(1 for b in books for o in builder.amazon_prices(b) if builder.price_discount(b, o, anchor))
        self.assertGreater(expected, 0)
        self.assertEqual(html.count('class="catalogue-format__off"'), expected)

    def test_only_reliable_filters_and_no_scores_are_public(self):
        # David 2026-11-08: «Día de la Madre» mostraba cualquier libro de crianza. Temática, temporada, contenido
        # y época son reglas propias sobre palabras clave: ni etiqueta, ni filtro, ni texto. Y la Creators API
        # no da valoraciones: ni caja en la tarjeta, ni filtro, ni orden por nota.
        pages = [ROOT / 'recomendaciones/index.html', *sorted((ROOT / 'recomendaciones/pagina').glob('*/index.html'))]
        hub = ''.join(p.read_text(encoding='utf-8') for p in pages)
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        kinds = {c['id']: c['tipo'] for c in data['categorias']}
        for hidden in ('temporada', 'tematica', 'contenido', 'epoca'):
            self.assertNotIn(f'data-facet="{hidden}"', hub)
            self.assertNotIn(f'data-facet-group="{hidden}"', hub)
        self.assertNotIn('data-filter="valoracion"', hub)
        self.assertNotIn('valoracion_desc', hub)
        self.assertNotIn('data-rating-book', hub)
        self.assertNotIn(builder.DEALS_SEASON, hub)
        shown = {c for found in re.findall(r'data-categories="([^"]*)"', hub) for c in found.split()}
        self.assertTrue(shown)
        self.assertEqual({kinds.get(c) for c in shown} - {'genero', 'edad'}, set(), 'data-categories solo con género y edad')
        script = (ROOT / 'assets/reading-catalogue.js').read_text(encoding='utf-8')
        self.assertIn("const FACETS = ['grupo', 'genero', 'edad', 'formato'];", script)
        for key in ('temporada', 'tematica', 'valoracion'):
            self.assertNotIn("{key: '" + key + "'", script)

    def test_public_categories_and_tags_keep_only_genre_and_age(self):
        cats = [{'id': 'fantasia', 'nombre': 'Fantasía', 'tipo': 'genero'}, {'id': 'adultos', 'nombre': 'Adultos', 'tipo': 'edad'},
                {'id': 'dia-de-la-madre', 'nombre': 'Día de la Madre', 'tipo': 'temporada'},
                {'id': 'familia-y-crianza', 'nombre': 'Familia', 'tipo': 'tematica'}, {'id': 'clasicos', 'nombre': 'Clásicos', 'tipo': 'epoca'}]
        self.assertEqual([c['id'] for c in builder.public(cats)], ['fantasia', 'adultos'])
        html = builder.tags(cats)
        self.assertIn('Fantasía', html)
        self.assertNotIn('Día de la Madre', html)
        self.assertNotIn('Familia', html)

    def test_discount_rounds_like_amazon_and_ignores_kindle_print_price(self):
        # 2026-11-04: «-4 %» where Amazon shows the legal 5 %, and ebooks at «-50 %» against the print price.
        paper = {'formato': 'tapa-dura', 'url': 'https://www.amazon.es/dp/8400000001?tag=x', 'fuente_url': 'https://www.amazon.es/dp/8400000001',
                 'fecha_verificacion': '2026-11-04', 'precio_centimos': 2081, 'precio_referencia_centimos': 2190}
        ebook = {'formato': 'ebook', 'url': 'https://www.amazon.es/dp/B000000001?tag=x', 'fuente_url': 'https://www.amazon.es/dp/B000000001',
                 'fecha_verificacion': '2026-11-04', 'precio_centimos': 1139, 'precio_referencia_centimos': 2190}
        book = {'id': 'lib-1', 'slug': 'libro', 'titulo': 'Libro', 'autores': ['A'], 'portada_local': '/assets/reading-covers/x.webp',
                'pvp_centimos': 2190, 'formatos_compra': [paper, ebook]}
        self.assertEqual(builder.format_discounts(book), 'tapa-dura:5:2026-11-04')
        self.assertEqual([d['formato'] for d in json.loads(builder.render_deals([book]))['ofertas']], ['tapa-dura'])
        ebook['precio_referencia_centimos'] = 1199  # real Kindle list price
        self.assertEqual(builder.format_discounts(book), 'tapa-dura:5:2026-11-04 ebook:5:2026-11-04')
        ebook['precio_referencia_centimos'] = 1990  # print price of another edition (El portero, 2026-11-05)
        self.assertEqual(builder.format_discounts(book), 'tapa-dura:5:2026-11-04')

    def test_filters_drop_epoch_and_unknown_pages(self):
        html = (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
        self.assertNotIn('data-facet-group="epoca"', html)
        self.assertNotIn('Páginas sin confirmar', html)
        self.assertIn('data-filter="estado"', html)
        # Sin valoraciones fuera de la ficha (David, 08/11): ni «Menos de 3 estrellas» ni «5 estrellas».
        self.assertNotIn('value="menos-3"', html)
        self.assertNotIn('estrellas</option>', html)
        self.assertIn('value="5">5 % o más', html)
