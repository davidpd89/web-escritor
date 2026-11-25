"""El público infantil sale de la mayoría de ramas de Amazon y no se pierde en el corte a tres materias.

Origen (25/11): «Narnia: El sobrino del mago» (Harperkids) salió como terror. Amazon lo tiene en siete ramas
infantiles y tres de adultos; «Infantil», el nodo más general, quedaba fuera del corte a tres materias y, sin
público infantil, nadie retiraba el terror de «Libros infantiles de fantasmas».
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import catalogo_amazon as ca  # noqa: E402
import reading_amazon_market as market  # noqa: E402
import reading_taxonomy as tax  # noqa: E402

TOP = {'displayName': 'Categorías', 'contextFreeName': 'Libros', 'ancestor': {'displayName': 'Libros', 'contextFreeName': 'Libros'}}
KIDS = {'displayName': 'Infantil', 'contextFreeName': 'Libros para niños', 'ancestor': TOP}
YOUTH = {'displayName': 'Juvenil', 'contextFreeName': 'Libros juveniles', 'ancestor': TOP}
ADULT = {'displayName': 'Literatura y ficción', 'contextFreeName': 'Literatura y ficción', 'ancestor': TOP}
STORE = {'displayName': 'Special Features Stores', 'contextFreeName': 'Special Features Stores',
         'ancestor': {'displayName': 'Self Service', 'contextFreeName': 'Self Service'}}


def branch(name, root):
    return {'displayName': name, 'contextFreeName': name, 'ancestor': root}


def item(*nodes, asin='B000000001'):
    return {'asin': asin, 'browseNodeInfo': {'browseNodes': list(nodes)}}


NARNIA = item(*[branch('Libros infantiles de fantasmas', KIDS)] + [branch(f'Fantasía infantil {i}', KIDS) for i in range(6)]
              + [branch('Fantasía', ADULT), branch('Clásicos', ADULT), branch('Aventuras', ADULT)])


class NodeAudienceTests(unittest.TestCase):
    def test_majority_of_branches_decides(self):
        self.assertEqual(tax.node_audience(NARNIA), 'infantil')
        self.assertEqual(tax.node_audience(item(branch('Cuentos', KIDS))), 'infantil')
        # Un nodo infantil suelto frente a uno de adultos no basta; dos de adultos frente a uno mandan.
        self.assertIsNone(tax.node_audience(item(branch('Cuentos', KIDS), branch('Novela', ADULT))))
        self.assertEqual(tax.node_audience(item(branch('Cuentos', KIDS), branch('Novela', ADULT), branch('Terror', ADULT))), 'otro')
        # «Juvenil» no es infantil: «Historias de miedo» de raíz juvenil se queda con su terror.
        self.assertEqual(tax.node_audience(item(branch('Terror juvenil', YOUTH), branch('Miedo', YOUTH))), 'otro')

    def test_store_branches_and_bad_shapes_do_not_count(self):
        self.assertEqual(tax.node_audience(item(branch('Cuentos', KIDS), branch('Ofertas', STORE), branch('Uuid', STORE))), 'infantil')
        for bad in (None, {}, {'browseNodeInfo': None}, {'browseNodeInfo': {'browseNodes': 'x'}}, item('x', None)):
            self.assertIsNone(tax.node_audience(bad))


class RecordSubjectsTests(unittest.TestCase):
    def test_infantil_survives_the_cut(self):
        out = ca.record_subjects(NARNIA, ['Terror', 'Fantasía', 'Clásicos', 'Aventuras'])
        self.assertEqual(out, ['Infantil', 'Terror', 'Fantasía', 'Clásicos'])
        out = ca.record_subjects(NARNIA, ['Terror', 'Fantasía', 'Clásicos', 'Aventuras', 'Infantil'])
        self.assertEqual(out, ['Terror', 'Fantasía', 'Clásicos', 'Infantil'])

    def test_adult_majority_drops_stray_infantil(self):
        adult = item(branch('Cuentos', KIDS), branch('Novela', ADULT), branch('Terror', ADULT))
        self.assertEqual(ca.record_subjects(adult, ['Terror', 'Infantil', 'Novela juvenil']), ['Terror', 'Novela juvenil'])

    def test_adult_topics_inside_kids_branches_are_ignored(self):
        kids = item(branch('Vida familiar', KIDS), branch('Emociones y sentimientos', KIDS))
        subjects = ca.node_subjects(kids)
        self.assertNotIn('Familia y crianza', subjects)
        self.assertNotIn('Autoayuda', subjects)
        self.assertIn('Infantil', subjects)
        self.assertIn('Familia y crianza', ca.node_subjects(item(branch('Vida familiar', ADULT))))


class PublishedBooksTests(unittest.TestCase):
    def test_price_sweep_marks_children_audience(self):
        book = {'id': 'narnia', 'formatos_compra': [{'formato': 'tapa-blanda', 'url': 'https://www.amazon.es/dp/B000000001'}]}
        payload = {'itemsResult': {'items': [NARNIA]}}
        self.assertIn('B000000001', market.price_asins(book))
        self.assertEqual(market.item_audience(book, payload), 'infantil')
        adult = {'itemsResult': {'items': [item(branch('Novela', ADULT))]}}
        self.assertIsNone(market.item_audience(book, adult))

    def test_listed_children_book_loses_terror(self):
        data = {'categorias': [{'id': c, 'slug': c, 'nombre': c, 'tipo': 'genero', 'orden': 1, 'activa': True}
                               for c in ('infantil', 'terror', 'fantasia', 'adultos')],
                'libros': [{'id': 'narnia', 'titulo': 'Narnia: El sobrino del mago', 'editorial': 'Harper', 'estado': 'publicado',
                            'publico_amazon': 'infantil'},
                           {'id': 'adulto', 'titulo': 'Cementerio', 'editorial': 'Harper', 'estado': 'publicado',
                            'publico_amazon': 'infantil'},
                           {'id': 'pegado', 'titulo': 'Monstruos', 'editorial': 'Kilikids', 'estado': 'publicado'}],
                'libro_categorias': [{'libro_id': 'narnia', 'categoria_id': 'terror'}, {'libro_id': 'narnia', 'categoria_id': 'fantasia'},
                                     {'libro_id': 'adulto', 'categoria_id': 'terror'}, {'libro_id': 'adulto', 'categoria_id': 'adultos'},
                                     {'libro_id': 'pegado', 'categoria_id': 'terror'}]}
        tax.repair_classification(data)
        cats = lambda b: {r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == b}  # noqa: E731
        self.assertEqual(cats('narnia'), {'infantil', 'fantasia'})
        self.assertEqual(cats('adulto'), {'terror', 'adultos'})
        self.assertEqual(cats('pegado'), {'infantil'})


if __name__ == '__main__':
    unittest.main()
