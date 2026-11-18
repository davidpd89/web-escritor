"""Invariantes de las categorías: un libro es ficción o no ficción, y «nutrición» no se hereda de una estantería.

Origen (2026-11-16): 283 publicados estaban en las dos caras («Los hermanos Karamázov» en historia, «Vida de
Tolstói» en narrativa, el manga «Flechazo» en biografías) y 170 de los 298 de «nutrición y bienestar» venían solo
de la raíz «Salud, familia y desarrollo personal» de Amazon («Horóscopo chino 2027», «Tarot»).
Sin red: casos sintéticos y el catálogo del repositorio, sobre una copia reparada (la carga lo repara en cuarentena)."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_quarantine as q  # noqa: E402
import reading_taxonomy as t  # noqa: E402
from catalogo_amazon import AMAZON_SUBJECTS  # noqa: E402

DATA = json.loads((ROOT / q.CATALOGUE).read_text(encoding='utf-8'))
AMAZON = 'https://www.' + t.AMAZON_SOURCE + 'B000000000'


def labels(data):
    found = {}
    for rel in data['libro_categorias']:
        found.setdefault(rel['libro_id'], set()).add(rel['categoria_id'])
    return found


def book(title, subjects='', publisher='', source=AMAZON):
    text = 'La editorial la incluye en %s.' % subjects if subjects else ''
    return {'id': 'x', 'titulo': title, 'editorial': publisher, 'descripcion_breve': text,
            'fuente_bibliografica_url': source, 'estado': 'publicado', 'autores': []}


class AxisTests(unittest.TestCase):
    CASES = (
        # título, materia, sello, etiquetas, cara
        ('Los hermanos Karamázov', 'clásicos, historia', '', {'narrativa', 'historia'}, 'ficcion'),
        ('Vida de Tolstói: Una experiencia de lectura', 'biografías y memorias, ensayo, narrativa', '',
         {'biografias-y-memorias', 'ensayo', 'narrativa'}, 'no-ficcion'),
        ('Flechazo: 42', 'biografías y memorias, novelas juveniles', '',
         {'biografias-y-memorias', 'comic-y-novela-grafica', 'narrativa-juvenil'}, 'ficcion'),
        ('Las memorias de Xiaolan', 'cómic y novela gráfica, novelas juveniles', '',
         {'biografias-y-memorias', 'comic-y-novela-grafica', 'narrativa-juvenil'}, 'ficcion'),
        ('Pensad en Flebas', 'ensayo, ciencia ficción', '', {'ciencia-ficcion', 'ensayo'}, 'ficcion'),
        ('Vera, una historia de amor', 'familia y crianza, narrativa', '', {'familia-y-crianza', 'narrativa'},
         'ficcion'),
        ('Cuando el viento hable', 'familia y crianza, historia, narrativa', '',
         {'familia-y-crianza', 'historia', 'narrativa'}, 'ficcion'),
        ('La aventura de educar', 'para padres', '', {'aventuras', 'familia-y-crianza'}, 'no-ficcion'),
        ('El Manifiesto comunista', 'cómic y novela gráfica, filosofía', '',
         {'comic-y-novela-grafica', 'filosofia', 'narrativa-juvenil'}, 'no-ficcion'),
        ('Tor', 'biografías y memorias', '', {'biografias-y-memorias', 'misterio-y-thriller'}, 'no-ficcion'),
        ('Jane Austen Citas', 'narrativa, historia', 'Editorial Reverté', {'narrativa', 'historia'}, 'no-ficcion'),
        ('Breve historia de Roma', 'narrativa, historia', '', {'narrativa', 'historia'}, 'no-ficcion'),
    )

    def test_each_case_falls_on_its_side(self):
        for title, subjects, publisher, assigned, side in self.CASES:
            with self.subTest(title):
                self.assertEqual(t.axis_side(book(title, subjects, publisher), assigned), side)

    def test_one_side_only_is_left_alone(self):
        self.assertIsNone(t.axis_side(book('Una novela'), {'narrativa', 'romance', 'tema-familia'}))
        self.assertIsNone(t.axis_side(book('Un ensayo'), {'ensayo', 'historia', 'comic-y-novela-grafica'}))

    def test_every_genre_is_on_one_side_at_most(self):
        self.assertEqual(t.FICTION_GENRES & t.NON_FICTION_GENRES, set())
        self.assertEqual(set(t.AXIS_FICTION) - t.FICTION_GENRES, set())
        self.assertEqual(set(t.AXIS_NON_FICTION) - t.NON_FICTION_GENRES, set())

    def test_repair_removes_the_other_side_and_what_derived_from_it(self):
        data = {'categorias': copy.deepcopy(DATA['categorias']), 'libros': [book('La aventura de educar', 'para padres')],
                'libro_categorias': [{'libro_id': 'x', 'categoria_id': c} for c in ('aventuras', 'familia-y-crianza')]}
        t.repair_classification(data)
        self.assertEqual(labels(data)['x'] & (t.FICTION_GENRES | t.NON_FICTION_GENRES), {'familia-y-crianza'})
        again = copy.deepcopy(data)
        t.repair_classification(again)
        self.assertEqual(again, data)


class HealthTests(unittest.TestCase):
    def repaired(self, title, subjects, assigned=(t.HEALTH_ID,), source=AMAZON):
        data = {'categorias': copy.deepcopy(DATA['categorias']), 'libros': [book(title, subjects, source=source)],
                'libro_categorias': [{'libro_id': 'x', 'categoria_id': c} for c in assigned]}
        t.repair_classification(data)
        return labels(data).get('x', set()), data['libros'][0]

    def test_shelf_root_health_goes(self):
        got, item = self.repaired('Guía práctica de herencias', 'salud, derecho', (t.HEALTH_ID, 'derecho'))
        self.assertNotIn(t.HEALTH_ID, got)
        self.assertNotIn('salud', t.subject_text(item))

    def test_esoteric_title_moves_to_its_genre(self):
        for title in ('Horóscopo chino 2027', 'Tarot', 'El oráculo de las brujas', 'No estamos solos: OVNIS'):
            with self.subTest(title):
                got, _item = self.repaired(title, 'salud')
                self.assertNotIn(t.HEALTH_ID, got)
                self.assertIn(t.ESOTERIC_ID, got)

    def test_real_health_stays(self):
        for title, subjects in (('Keto mediterránea', 'salud'), ('La microbiota y tu salud', 'salud, cocina'),
                                ('Dormir bien', 'salud, autoayuda'), ('Estimula tu nervio vago', 'salud')):
            with self.subTest(title):
                self.assertIn(t.HEALTH_ID, self.repaired(title, subjects)[0])

    def test_other_sources_are_not_touched(self):
        got, _item = self.repaired('Tarot', 'salud', source='https://www.todostuslibros.com/libros/x')
        self.assertIn(t.HEALTH_ID, got)

    def test_amazon_shelf_root_is_not_a_health_subject(self):
        self.assertNotIn('salud, familia y desarrollo personal', AMAZON_SUBJECTS['Salud'])


class RealCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = labels(DATA)
        cls.data = copy.deepcopy(DATA)
        t.repair_classification(cls.data)
        cls.after = labels(cls.data)
        cls.genres = {c['id'] for c in cls.data['categorias'] if c['tipo'] == 'genero'}
        cls.published = [b for b in cls.data['libros'] if b.get('estado') == 'publicado']

    def test_no_published_book_is_fiction_and_non_fiction(self):
        both = [b['id'] for b in self.published
                if self.after.get(b['id'], set()) & t.FICTION_GENRES
                and self.after.get(b['id'], set()) & t.NON_FICTION_GENRES]
        self.assertEqual(both, [], 'libros en las dos caras del eje tras la reparación')

    def test_no_published_book_keeps_inherited_health(self):
        left = [b['id'] for b in self.published if t.inherited_health(b, self.after.get(b['id'], set()))]
        self.assertEqual(left, [], 'libros con «nutrición y bienestar» heredada de la estantería')

    def test_repair_never_leaves_a_book_without_the_genre_it_had(self):
        lost = [b['id'] for b in self.published
                if self.before.get(b['id'], set()) & self.genres and not self.after.get(b['id'], set()) & self.genres]
        self.assertEqual(lost, [], 'libros que tenían género y la reparación dejó sin ninguno')

    def test_repair_is_idempotent(self):
        again = copy.deepcopy(self.data)
        t.repair_classification(again)
        changed = sorted(i for i in set(self.after) | set(labels(again)) if self.after.get(i) != labels(again).get(i))
        self.assertEqual(changed, [], 'libros cuya clasificación cambia en una segunda pasada')
        self.assertEqual(again, self.data)


if __name__ == '__main__':
    unittest.main()
