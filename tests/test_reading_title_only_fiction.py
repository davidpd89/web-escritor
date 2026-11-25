"""Pasatiempos y guías de adultos con un género de ficción que solo sale de una palabra del título, y cuentos
infantiles con «familia y crianza» o «desarrollo personal» (guías para los padres).

Origen (25/11, revisión con GPT de la web): «Turismo de terror» (crónica) y «Cuando todos se van» en terror,
«Crimoku» y «Minemurder» (pasatiempos de lógica) en misterio; «Enzo tiene una hermanita» y «Rosa, la nube Lupe»
(cuentos) en familia y crianza o desarrollo personal.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_taxonomy as tax  # noqa: E402
sys.path.insert(0, str(ROOT / 'tests'))
from contrato_libros import incumplen  # noqa: E402

AMAZON = 'https://www.amazon.es/dp/0000000000'
ADULT_FICTION_OUT = {'isbn-9788425372759': 'terror', 'isbn-9788408326731': 'terror',
                     'isbn-9788409923991': 'misterio-y-thriller', 'isbn-9788410442856': 'misterio-y-thriller',
                     'isbn-9780241837832': 'misterio-y-thriller'}
CHILD_GUIDES_OUT = ('isbn-9788410252585', 'isbn-9791399320060')


def catalogue(books, rels):
    ids = {c for _b, c in rels} | {'ocio-y-aficiones', 'infantil'}
    return {'categorias': [{'id': c, 'slug': c, 'nombre': c, 'orden': 1, 'activa': True,
                            'tipo': 'tematica' if c.startswith('tema-') else 'genero'} for c in sorted(ids)],
            'libros': books, 'libro_categorias': [{'libro_id': b, 'categoria_id': c} for b, c in rels]}


def book(ident, title, subjects, **extra):
    return {'id': ident, 'titulo': title, 'editorial': 'X', 'estado': 'publicado', 'fuente_bibliografica_url': AMAZON,
            'descripcion_breve': f'{title}. La editorial la incluye en {subjects}.', **extra}


def cats(data, ident):
    return {r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == ident}


class RepairTests(unittest.TestCase):
    def test_puzzle_book_loses_title_mystery(self):
        data = catalogue([book('crimoku', 'Crimoku: 85 enigmas de lógica y misterio', 'tiempo libre')],
                         [('crimoku', 'misterio-y-thriller'), ('crimoku', 'tema-ocio-y-tiempo-libre')])
        tax.repair_classification(data)
        self.assertEqual(cats(data, 'crimoku'), {'tema-ocio-y-tiempo-libre', 'ocio-y-aficiones'})
        before = json.dumps(data, sort_keys=True)
        tax.repair_classification(data)
        self.assertEqual(json.dumps(data, sort_keys=True), before)

    def test_real_fiction_is_kept(self):
        rels = [('nov', 'terror'), ('nov', 'tema-viajes'), ('juv', 'terror'), ('juv', 'tema-viajes'), ('juv', 'juvenil'),
                ('mat', 'terror'), ('mat', 'tema-viajes')]
        data = catalogue([book('nov', 'Viaje de terror: una novela', 'viajes'),
                          book('juv', 'Turismo de terror', 'viajes, juvenil'),
                          book('mat', 'Hotel', 'terror, viajes')], rels)
        tax.repair_classification(data)
        self.assertIn('terror', cats(data, 'nov'))  # «novela» en el título
        self.assertIn('terror', cats(data, 'juv'))  # público juvenil
        self.assertIn('terror', cats(data, 'mat'))  # la materia lo nombra

    def test_children_book_loses_parent_guides(self):
        data = catalogue([book('enzo', 'Enzo tiene una hermanita', 'infantil')],
                         [('enzo', 'infantil'), ('enzo', 'familia-y-crianza'), ('enzo', 'desarrollo-personal')])
        tax.repair_classification(data)
        self.assertEqual(cats(data, 'enzo'), {'infantil'})


class PublishedCatalogueTests(unittest.TestCase):
    def test_affected_books_are_repaired(self):
        data = json.loads((ROOT / 'data' / 'reading-catalogue.json').read_text(encoding='utf-8'))
        by_book = {}
        for r in data['libro_categorias']:
            by_book.setdefault(r['libro_id'], set()).add(r['categoria_id'])
        malos = {}
        for book in data['libros']:
            if book.get('estado') != 'publicado':
                continue
            assigned = by_book.get(book['id'], set())
            if sobra := tax.title_only_fiction(book, assigned):
                malos[book['id']] = 'ficción solo por el título: ' + ', '.join(sorted(sobra))
            if sobra := tax.children_drop(book, assigned):
                malos[book['id']] = 'género de adultos en un libro infantil: ' + ', '.join(sorted(sobra))
        for ident, genre in ADULT_FICTION_OUT.items():
            if genre in by_book.get(ident, set()):
                malos[ident] = f'conserva {genre}'
        for ident in CHILD_GUIDES_OUT:
            if by_book.get(ident, set()) & {'familia-y-crianza', 'desarrollo-personal'}:
                malos[ident] = 'conserva la guía para padres'
        incumplen('clasificación reparada (ficción del título, guías en cuentos)', malos)


if __name__ == '__main__':
    unittest.main()
