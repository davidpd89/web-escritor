"""GEO de las fichas: el JSON-LD describe el libro y el llms.txt lleva la orientación propia.

Usa datos reales; sin peticiones HTTP.
"""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reading_catalogue_geo", ROOT / "scripts/build-reading-catalogue.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class CatalogueGEO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/reading-catalogue.json").read_text(encoding="utf-8"))
        cls.template = (ROOT / "scripts/templates/reading-catalogue.html.tmpl").read_text(encoding="utf-8")
        builder.OWN_TEXTS.clear()
        builder.OWN_TEXTS.update(builder.load_own_texts(ROOT))
        cls.books = builder.validate(cls.data, ROOT)

    def graph(self, b):
        html = builder.render_book(self.data, b, self.template)
        block = next(x for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S) if '"Book"' in x)
        return {n['@type']: n for n in json.loads(block)['@graph']}, html

    def test_book_schema_is_described_by_its_synopsis_and_the_page_by_its_meta(self):
        for b in self.books[:40]:
            nodes, html = self.graph(b)
            meta = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
            self.assertEqual(nodes['Book']['description'], builder.schema_synopsis(b), b['id'])
            self.assertNotIn('Antes de elegirlo', nodes['Book']['description'], b['id'])
            self.assertLessEqual(len(nodes['Book']['description']), 501)
            self.assertEqual(builder.html.unescape(meta), nodes['WebPage']['description'], b['id'])

    def test_llms_index_carries_the_validated_audience_text(self):
        authors, publishers = [], []
        text = builder.render_llms_index(self.data, self.books, authors, publishers)
        with_audience = [b for b in self.books if builder.own_summary(b)]
        # Todo libro con «Para quién es» validado lo lleva; los recién incorporados esperan a su texto.
        self.assertEqual(len(with_audience), sum(1 for b in self.books if any(x['modulo'] == 'para_quien' for x in (builder.OWN_TEXTS.get(b['id']) or {}).get('bloques', []))))
        self.assertGreater(len(with_audience), 100)
        for b in with_audience:
            line = next(l for l in text.splitlines() if f"{builder.url(b)})" in l)
            who = builder.own_summary(b)
            # Entero, salvo cuando la línea llega al tope de 700: entonces cede espacio, pero empieza igual.
            self.assertIn('Para quién es: ' + (who if len(line) < 640 else who[:40]), line, b['id'])
            self.assertLessEqual(len(line), 700, b['id'])
            # Misma etiqueta que el generador: sin sinopsis breve de la editorial, el texto es una «Descripción».
            # La publicación de textos del 07/11 se paró aquí con el primer texto propio de un libro sin sinopsis.
            label = 'Sinopsis de la editorial:' if b.get('sinopsis_breve') else 'Descripción:'
            self.assertLess(line.index('Para quién es:'), line.index(label), b['id'])
        self.assertNotIn('sinopsis propia', text)

    def test_own_meta_descriptions_fit_without_cutting_a_sentence(self):
        metas = {b['id']: builder.own_meta_description(b) for b in self.books if builder.OWN_TEXTS.get(b['id'])}
        self.assertGreater(len(metas), 100)
        long = {i: m for i, m in metas.items() if len(m) > 160 or not m.endswith('.')}
        self.assertLessEqual(len(long), 2, long)


if __name__ == "__main__":
    unittest.main()
