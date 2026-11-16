"""P1-1: /recomendaciones/novedades/ — cuatro días consecutivos desde la fecha de los datos y cada libro en su día.

Propiedad con anclas límite (31/12, 28/02, 29/02, cambios de hora de marzo y octubre) y 300 anclas
pseudoaleatorias con semilla fija (stdlib; sin dependencia nueva).
"""
import importlib.util
import json
import random
import re
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_reading_catalogue', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

EDGES = [date(2026, 12, 31), date(2027, 2, 28), date(2028, 2, 28), date(2028, 2, 29), date(2027, 3, 27), date(2027, 3, 28), date(2026, 10, 24), date(2026, 10, 25)]


def anchors():
    rnd = random.Random(1611)
    return EDGES + [date(2024, 1, 1) + timedelta(days=rnd.randrange(3650)) for _ in range(300)]


def fake_books(anchor, rnd):
    books = [{'id': 'ancla', 'titulo': 'Ancla', 'fecha_actualizacion': anchor.isoformat()}]
    for n in range(40):
        when = anchor + timedelta(days=rnd.randrange(-6, 9))
        books.append({'id': f'b{n}', 'titulo': f'Libro {n}', 'fecha_publicacion': when.isoformat(), 'fecha_actualizacion': anchor.isoformat()})
    return books


class NoveltyDaysProperty(unittest.TestCase):
    def test_four_consecutive_days_and_each_book_in_its_section(self):
        rnd = random.Random(7)
        for anchor in anchors():
            books = fake_books(anchor, rnd)
            days = builder.novelty_days(books)
            self.assertEqual([d for d, _ in days], [anchor + timedelta(days=n) for n in range(4)], anchor)
            placed = {b['id']: d for d, bs in days for b in bs}
            for b in books:
                when = b.get('fecha_publicacion')
                inside = when is not None and 0 <= (date.fromisoformat(when) - anchor).days < 4
                self.assertEqual(b['id'] in placed, inside, (anchor, b))
                if inside:
                    self.assertEqual(placed[b['id']].isoformat(), when)

    def test_day_label_is_absolute(self):
        self.assertEqual(builder.day_label(date(2028, 2, 29)), 'martes 29 de febrero de 2028')


class NoveltiesPage(unittest.TestCase):
    def test_generated_page_contract(self):
        html = (ROOT / 'recomendaciones/novedades/index.html').read_text(encoding='utf-8')
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        books = builder.published_books(data)
        days = builder.novelty_days(books)
        self.assertEqual(re.findall(r'data-novelty-day="([\d-]+)"', html), [d.isoformat() for d, _ in days])
        self.assertIn('<link rel="canonical" href="https://davidportodiaz.com/recomendaciones/novedades/">', html)
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
        item_list = next(n for n in ld['@graph'] if n['@type'] == 'ItemList')
        self.assertEqual(item_list['numberOfItems'], sum(len(bs) for _, bs in days))
        self.assertIn('/assets/catalogue-novedades.js?v=', html)
        hub = (ROOT / 'recomendaciones/index.html').read_text(encoding='utf-8')
        self.assertIn('<a class="text-action" href="/recomendaciones/novedades/">', hub)
        registry = json.loads((ROOT / 'data/content-registry.json').read_text(encoding='utf-8'))
        self.assertIn('/recomendaciones/novedades/', {e['url'] for e in registry['entries']})


class TelegramDigestLink(unittest.TestCase):
    def test_daily_digest_points_to_novelties_page(self):
        import sys
        sys.path.insert(0, str(ROOT / 'scripts'))
        import reading_telegram
        msg = reading_telegram.digest([{'isbn13': '9788400000001', 'release_date': '2026-11-16', 'title': 'T', 'author': 'A'}], '2026-11-16')
        self.assertIn('href="https://davidportodiaz.com/recomendaciones/novedades/"', msg['text'])


if __name__ == '__main__':
    unittest.main()
