"""Contrato de la tarjeta y la ficha (docs/contrato-tarjeta-libro.md), sobre casos límite y sobre el catálogo real."""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_card_contract', ROOT / 'scripts/build-reading-catalogue.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

CAT = lambda tipo, i: {'tipo': tipo, 'id': f'{tipo}-{i}', 'nombre': f'{tipo} {i}', 'orden': i}


class CardContractTest(unittest.TestCase):
    def test_badge_three_states_by_date(self):
        anchor = '2026-11-03'
        self.assertEqual(m.badge({'fecha_publicacion': '2026-11-04'}, anchor), 'proximamente')
        self.assertEqual(m.badge({'fecha_publicacion': '2026-11-03'}, anchor), 'novedad')
        self.assertEqual(m.badge({'fecha_publicacion': '2026-10-04'}, anchor), 'novedad')
        self.assertEqual(m.badge({'fecha_publicacion': '2026-10-03'}, anchor), '')
        self.assertEqual(m.badge({}, anchor), '')

    def test_tags_two_on_card_eight_on_detail(self):
        cats = [CAT(t, i) for t in ('genero', 'tematica', 'epoca', 'edad') for i in range(4)]
        count = lambda html: html.count('<li>')
        self.assertEqual(count(m.tags(cats, compact=True)), m.CARD_TAGS)
        self.assertEqual(count(m.tags(cats, limit=m.DETAIL_TAGS)), m.DETAIL_TAGS)
        # Autores y editoriales: sin tope, pero solo tipos de fuente fiable (sin temática ni época propias).
        self.assertEqual(count(m.tags(cats)), len(m.public(cats)))
        self.assertNotIn('tematica-0', m.tags(cats))
        self.assertNotIn('edad', m.tags(cats, compact=True))
        self.assertIn('genero-0', m.tags(cats, compact=True))

    def test_title_fits_two_lines_with_ellipsis(self):
        long = {'titulo': 'Una historia larguísima que no cabe de ninguna manera en dos líneas de tarjeta'}
        self.assertLessEqual(len(m.card_title(long)), m.CARD_TITLE_CHARS + 1)
        self.assertTrue(m.card_title(long).endswith('…'))
        self.assertEqual(m.card_title({'titulo': 'Coraline'}), 'Coraline')
        self.assertEqual(m.card_title({'titulo': 'Alas de sangre: edición coleccionista con cantos tintados y más'}), 'Alas de sangre')

    def test_synopsis_shorter_with_badge(self):
        book = {'descripcion_breve': 'palabra ' * 80, 'fecha_publicacion': '2026-11-20'}
        self.assertLessEqual(len(m.card_synopsis(book, anchor='2026-11-03')), m.CARD_SYNOPSIS_BADGE + 1)
        self.assertGreater(len(m.card_synopsis(dict(book, fecha_publicacion='2020-01-01'), anchor='2026-11-03')),
                           m.CARD_SYNOPSIS_BADGE + 1)

    def test_js_and_python_share_the_novelty_window(self):
        js = (ROOT / 'assets/reading-catalogue.js').read_text(encoding='utf-8')
        self.assertIn(f"isNew(label.dataset.releaseLabel, '{m.NOVELTY_DAYS}')", js)

    def test_published_cards_respect_the_contract(self):
        pages = [ROOT / 'recomendaciones/index.html', *sorted(ROOT.glob('recomendaciones/pagina/*/index.html'))]
        html = '\n'.join(page.read_text(encoding='utf-8') for page in pages)
        cards = html.split('<li class="catalogue-card"')[1:]  # cada tarjeta lleva listas anidadas: se corta por la siguiente
        self.assertGreater(len(cards), 100)
        for card in cards:
            title = re.search(r'<h3><a [^>]*>(.*?)</a></h3>', card, re.S).group(1)
            self.assertLessEqual(len(m.html.unescape(title)), m.CARD_TITLE_CHARS + 1, title)
            tags = re.search(r'<ul class="catalogue-tags catalogue-tags--compact">(.*?)</ul>', card, re.S)
            self.assertLessEqual(tags.group(1).count('<li>') if tags else 0, m.CARD_TAGS)
            self.assertEqual(card.count('data-purchase-format=') + card.count('data-missing-format='), 4)
            self.assertIn('>Ver ficha</a>', card)

    def test_published_detail_pages_respect_the_contract(self):
        # Antes lo hacía el navegador libro a libro (más de 15 min en CI); aquí cubre todas las fichas en segundos.
        books = [b for b in json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['libros']
                 if b['estado'] == 'publicado']
        self.assertGreater(len(books), 100)
        known_authors = {a['nombre'] for a in m.author_records()}
        for b in books:
            page = (ROOT / 'recomendaciones/libros' / b['slug'] / 'index.html').read_text(encoding='utf-8')
            with self.subTest(b['slug']):
                buy = re.search(r'<a class="catalogue-buy-link" href="([^"]+)"[^>]*rel="([^"]+)"[^>]*>([^<]*)', page)
                self.assertRegex(buy.group(3), r'^Comprar en Amazon(\s|$)')
                self.assertIn('sponsored', buy.group(2))
                href = m.html.unescape(buy.group(1))
                self.assertIn('tag=davidporto-21', href)
                if '/dp/' not in href:
                    self.assertIn('k=' + b['isbn13'], href)
                cover = re.search(r'class="catalogue-cover-panel"><a href="([^"]+)"', page)
                self.assertEqual(cover.group(1), buy.group(1), 'portada y botón comparten enlace')
                authors = re.search(r'<p class="catalogue-author">(.*?)</p>', page, re.S)
                # El catálogo no crea fichas de autor ni de sello: sin ficha, el nombre va en texto plano.
                self.assertEqual(authors.group(1).count('<a '), sum(n in known_authors for n in b['autores']))
                ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1))
                self.assertEqual(next(x for x in ld['@graph'] if x['@type'] == 'Book')['isbn'], b['isbn13'])
                self.assertNotIn('aggregateRating', json.dumps(ld))
                if b.get('editorial_slug') or b.get('editorial_catalogo_slug'):
                    publisher = ('/editoriales/' + b['editorial_slug'] if b.get('editorial_slug')
                                 else '/recomendaciones/editoriales/' + b['editorial_catalogo_slug']) + '/'
                    self.assertIn(f'href="{publisher}"', page)
                else:
                    self.assertIn(m.esc(b['editorial']), page)


if __name__ == '__main__':
    unittest.main()
