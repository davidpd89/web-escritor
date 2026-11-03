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
        self.assertEqual(count(m.tags(cats)), len(cats))  # autores y editoriales: sin tope
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
        html = (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
        cards = html.split('<li class="catalogue-card"')[1:]  # cada tarjeta lleva listas anidadas: se corta por la siguiente
        self.assertGreater(len(cards), 100)
        for card in cards:
            title = re.search(r'<h3><a [^>]*>(.*?)</a></h3>', card, re.S).group(1)
            self.assertLessEqual(len(m.html.unescape(title)), m.CARD_TITLE_CHARS + 1, title)
            tags = re.search(r'<ul class="catalogue-tags catalogue-tags--compact">(.*?)</ul>', card, re.S)
            self.assertLessEqual(tags.group(1).count('<li>') if tags else 0, m.CARD_TAGS)
            self.assertEqual(card.count('data-purchase-format=') + card.count('data-missing-format='), 4)
            self.assertIn('>Ver ficha</a>', card)


if __name__ == '__main__':
    unittest.main()
