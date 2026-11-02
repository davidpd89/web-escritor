"""Contrato de navegación en catálogo: fichas en nueva pestaña y Amazon afiliado.

Usa datos/plantillas reales. No hace peticiones HTTP y no modifica `main`.
"""
import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "reading_catalogue_affiliate_test", ROOT / "scripts/build-reading-catalogue.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self._active = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._active = {"attrs": dict(attrs), "text": ""}
            self.links.append(self._active)

    def handle_data(self, text):
        if self._active is not None:
            self._active["text"] += text

    def handle_endtag(self, tag):
        if tag == "a":
            self._active = None


class AffiliateNavigationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/reading-catalogue.json").read_text(encoding="utf-8"))
        cls.template = (ROOT / "scripts/templates/reading-catalogue.html.tmpl").read_text(encoding="utf-8")
        cls.books = builder.validate(cls.data, ROOT)
        cls.coraline = next(b for b in cls.books if b["id"] == "lib-0001")
        cls.imported = next(b for b in cls.books if b["id"].startswith("isbn-"))

    @staticmethod
    def links(html):
        p = LinkCollector()
        p.feed(html)
        return p.links

    def test_imported_cover_opens_the_amazon_product_or_tagged_isbn_search(self):
        b = self.imported
        html = builder.render_book(self.data, b, self.template)
        candidate = [x for x in self.links(html)
                     if x["attrs"].get("aria-label", "").startswith("Comprar en Amazon:")]
        self.assertEqual(len(candidate), 1)
        # With a verified ASIN the cover goes straight to the product; otherwise to the ISBN search.
        self.assertEqual(candidate[0]["attrs"]["href"], builder.amazon_destination(b))
        self.assertTrue(candidate[0]["attrs"]["href"] == b["amazon_busqueda_isbn"]
                        or "/dp/" in candidate[0]["attrs"]["href"])
        self.assertEqual(candidate[0]["attrs"]["target"], "_blank")
        self.assertIn("sponsored", candidate[0]["attrs"]["rel"])
        self.assertIn("tag=davidporto-21", candidate[0]["attrs"]["href"])

    def test_manual_coraline_preserves_verified_direct_link(self):
        b = self.coraline
        html = builder.render_book(self.data, b, self.template)
        cover = [x for x in self.links(html) if x["attrs"].get("aria-label", "").startswith("Comprar en Amazon:")]
        self.assertEqual(len(cover), 1)
        self.assertEqual(cover[0]["attrs"]["href"], builder.amazon_es(b["url_amazon_afiliada"]))

    def test_cards_offer_ficha_and_amazon_separately(self):
        books = [self.coraline, self.imported]
        html = builder.render_hub(self.data, books, self.template)
        links = self.links(html)
        for b in books:
            page = builder.url(b)
            ficha = [x for x in links if x["attrs"].get("href") == page]
            self.assertGreaterEqual(len(ficha), 2, b["titulo"])
            self.assertTrue(all(x["attrs"].get("target") == "_blank" for x in ficha))
            self.assertTrue(all("noopener" in x["attrs"].get("rel", "") for x in ficha))
            buying = [x for x in links if x["attrs"].get("href") == builder.amazon_destination(b)]
            # El botón de compra y la casilla de su formato en la caja de precios llevan al mismo destino.
            self.assertGreaterEqual(len(buying), 1)
            self.assertTrue(all("sponsored" in x["attrs"].get("rel", "") for x in buying))
            self.assertTrue(all(x["attrs"].get("target") == "_blank" for x in buying))

    def test_cards_keep_categories_and_human_readable_edition_metadata(self):
        books = [self.coraline, self.imported]
        html = builder.render_hub(self.data, books, self.template)
        self.assertGreaterEqual(html.count('class="catalogue-tags'), 2)
        self.assertEqual(builder.publication_date_label(self.coraline), "1 de junio de 2009")
        self.assertIn('<p class="catalogue-byline">', html)
        self.assertNotIn('catalogue-facts', html)
        self.assertIn(self.imported["editorial"], html)
        if self.imported.get("numero_paginas"):
            self.assertIn('<span class="catalogue-pages">' + str(self.imported["numero_paginas"]) + " páginas</span>", html)
        self.assertNotIn("Edad:", html)
        if self.imported.get("fecha_publicacion"):
            self.assertIn(" de ", builder.publication_date_label(self.imported))
        self.assertNotIn("Los filtros de precio y oferta estarán disponibles", html)
        self.assertNotIn("Precios, ofertas y valoraciones: se mostrarán", html)

    def test_all_26_published_books_have_tagged_destination(self):
        for b in self.books:
            with self.subTest(book=b["id"]):
                url = builder.amazon_destination(b)
                self.assertIsNotNone(url)
                self.assertIn("amazon.es/", url)
                self.assertIn("tag=davidporto-21", url)
                self.assertNotIn("amazon.com/", url)


if __name__ == "__main__":
    unittest.main()
