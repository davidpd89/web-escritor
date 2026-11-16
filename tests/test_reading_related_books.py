"""«También te puede interesar»: mismo público y lo más parecido primero, no lo primero del alfabeto con una etiqueta común."""
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_catalogue_related', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class RelatedBooksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        cls.books = [b for b in cls.data['libros'] if b['estado'] == 'publicado']
        cls.by_url = {builder.url(b): b for b in cls.books}
        builder.index_categories(cls.data)  # sin índice, cada ficha recorre todas las relaciones: minutos

    def related(self, b):
        html = builder.related_books(self.data, b)
        return [self.by_url[u] for u in dict.fromkeys(re.findall(r'<a href="([^"]+)">', html))]

    def test_related_books_never_cross_audiences_or_distant_ages(self):
        for b in self.books:
            cats = {c['id'] for c in builder.categories(self.data, b)}
            for x in self.related(b):
                if set(x['autores']) & set(b['autores']):
                    continue
                other = {c['id'] for c in builder.categories(self.data, x)}
                pa, pb = builder.audience(cats), builder.audience(other)
                self.assertFalse(pa and pb and pa != pb, (b['titulo'], x['titulo']))
                ages = builder.min_age(b), builder.min_age(x)
                self.assertFalse(None not in ages and abs(ages[0] - ages[1]) > 4, (b['titulo'], x['titulo']))

    def test_rare_shared_categories_outrank_common_ones(self):
        """Con «Romance» y «Hockey» delante, gana quien comparte «Hockey» aunque su título vaya después en el alfabeto."""
        data = {'categorias': [{'id': 'romance', 'nombre': 'Romance', 'tipo': 'genero', 'orden': 1},
                               {'id': 'hockey', 'nombre': 'Hockey', 'tipo': 'tematica', 'orden': 2}], 'libros': []}
        template = self.books[0]
        book = lambda i, titulo, cats: {**template, 'id': i, 'slug': i, 'titulo': titulo, 'autores': [i], 'categorias': cats}
        data['libros'] = [book('a', 'Origen', ['romance', 'hockey']), book('b', 'Zeta sobre hielo', ['hockey']),
                          *[book(f'r{n}', f'A romance {n}', ['romance']) for n in range(6)]]
        original = builder.categories
        builder.categories = lambda d, b: [c for c in d['categorias'] if c['id'] in b['categorias']]
        try:
            html = builder.related_books(data, data['libros'][0])
        finally:
            builder.categories = original
        titles = re.findall(r'<a href="[^"]+">([^<]+)</a>', html)
        self.assertEqual(titles[0], 'Zeta sobre hielo')

    def test_links_are_spread_across_the_catalogue(self):
        """H8: el bloque reparte los enlaces; ≥ 95 % de fichas reciben alguno y ninguna más de 40."""
        inbound = {b['id']: 0 for b in self.books}
        for b in self.books:
            for x in self.related(b):
                inbound[x['id']] += 1
        reached = sum(1 for n in inbound.values() if n)
        self.assertGreaterEqual(reached / len(inbound), 0.95, f'{reached}/{len(inbound)} fichas con enlace entrante')
        self.assertLessEqual(max(inbound.values()), builder.RELATED_INBOUND_CAP)

    def test_ties_follow_publication_date_not_alphabet(self):
        """Con la misma categoría compartida gana la fecha más cercana, no el primer título del alfabeto."""
        data = {'categorias': [{'id': 'romance', 'nombre': 'Romance', 'tipo': 'genero', 'orden': 1}], 'libros': []}
        template = self.books[0]
        def book(i, titulo, fecha):
            out = {**template, 'id': i, 'slug': i, 'titulo': titulo, 'autores': [i], 'categorias': ['romance'],
                   'fecha_publicacion': fecha}
            out.pop('fecha_publicacion_parcial', None)
            return out
        data['libros'] = [book('a', 'Origen', '2026-11-01'), book('z', 'Zeta cercana', '2026-10-30'),
                          *[book(f'r{n}', f'A lejana {n}', f'19{50 + n}-01-01') for n in range(6)]]
        original = builder.categories
        builder.categories = lambda d, b: [c for c in d['categorias'] if c['id'] in b['categorias']]
        try:
            html = builder.related_books(data, data['libros'][0])
        finally:
            builder.categories = original
        titles = re.findall(r'<a href="[^"]+">([^<]+)</a>', html)
        self.assertEqual(titles, ['Zeta cercana', *[f'A lejana {n}' for n in range(5, 0, -1)]])  # 1950 queda fuera

    def test_publication_day_handles_partial_and_missing_dates(self):
        self.assertEqual(builder.publication_day({'fecha_publicacion': '2026-02-03'}), builder.date(2026, 2, 3).toordinal())
        self.assertEqual(builder.publication_day({'fecha_publicacion_parcial': '2026-02'}), builder.date(2026, 2, 15).toordinal())
        self.assertEqual(builder.publication_day({'anio_publicacion': 1999}), builder.date(1999, 7, 1).toordinal())
        self.assertEqual(builder.publication_day({'fecha_publicacion': 'basura'}), 0)
        self.assertEqual(builder.publication_day({}), 0)


if __name__ == '__main__':
    unittest.main()
