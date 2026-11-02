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
        self.assertLess(html.index('Zeta sobre hielo'), html.index('A romance 0'))


if __name__ == '__main__':
    unittest.main()
