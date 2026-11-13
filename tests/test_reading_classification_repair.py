"""Clasificación de las cargas de Amazon: no-libros fuera, etiquetas de nodo fuera y género para todo publicado.

Origen: carga del 2026-11-13 (Nacho con nutrición, «Madrid siglo 21» sin género, «Watashi no nihongo» y
«Sorry! But I Am With Hurry» como ensayo). Sin red: datos sintéticos y el catálogo del repositorio."""
import copy
import json
import sys
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_quarantine as q  # noqa: E402
from reading_amazon_market import item_non_reading  # noqa: E402
from reading_taxonomy import (FALLBACK_GENRES, READER_TYPES, GenreFallback, collection_genre,  # noqa: E402
                              non_reading_reason, repair_classification)  # noqa: E402

DATA = json.loads((ROOT / q.CATALOGUE).read_text(encoding='utf-8'))
NACHO, MADRID, CONSPIRACY = 'isbn-9788419913982', 'isbn-9788449602122', 'isbn-9791388204272'
WATASHI, SORRY, MYSTERY = 'isbn-9788419441928', 'isbn-9788495794161', 'isbn-9788425375989'


def labels(data):
    found = {}
    for rel in data['libro_categorias']:
        found.setdefault(rel['libro_id'], set()).add(rel['categoria_id'])
    return found


class NonReadingTests(unittest.TestCase):
    def test_titles_that_are_not_reading(self):
        for title in ('Libro para colorear de dinosaurios', 'Agenda escolar 2027', 'Pegatinas de animales',
                      'Cuaderno de vacaciones 3.º primaria', 'Aprende japonés en 30 días', 'Calendario de Adviento',
                      'Libro de actividades del mar', 'Diario de 5 años'):
            with self.subTest(title):
                self.assertTrue(non_reading_reason(title))

    def test_reading_titles_with_risky_words_stay(self):
        for title in ('Misterio en la noche de Reyes', 'La libreta de Dani', 'Hasta que el calendario nos separe',
                      'Cuaderno blanco', 'El cuaderno de Maya', 'La agenda oculta del rey'):
            with self.subTest(title):
                self.assertIsNone(non_reading_reason(title))

    def test_language_learning_node_without_a_telling_title(self):
        self.assertEqual(non_reading_reason('Sorry! But I Am With Hurry', ['Aprendizaje y enseñanza de idiomas']),
                         'método de idiomas')
        self.assertIsNone(non_reading_reason('Sorry! But I Am With Hurry', ['Lingüística', 'Libros']))

    def test_price_sweep_reads_nodes_only_of_the_printed_edition(self):
        book = {'id': 'x', 'isbn13': '9788495794161', 'asins_amazon': {'8495794160': 'tapa-blanda'}}
        node = {'displayName': 'Inglés', 'ancestor': {'contextFreeName': 'Aprendizaje y enseñanza de idiomas'}}
        payload = {'itemsResult': {'items': [{'asin': '8495794160', 'browseNodeInfo': {'browseNodes': [node]}}]}}
        with unittest.mock.patch('reading_amazon_market.price_asins', return_value={'8495794160': 'tapa-blanda'}):
            self.assertEqual(item_non_reading(book, payload), 'método de idiomas')
        with unittest.mock.patch('reading_amazon_market.price_asins', return_value={'8495794160': 'ebook'}):
            self.assertIsNone(item_non_reading(book, payload))
        with unittest.mock.patch('reading_amazon_market.price_asins', return_value={'OTRO': 'tapa-blanda'}):
            self.assertIsNone(item_non_reading(book, payload))


class CollectionGenreTests(unittest.TestCase):
    def test_amazon_collection_in_brackets_gives_the_genre(self):
        for title, genre in (('Los crímenes de Encina Rota (Alfaguara Negra)', 'misterio-y-thriller'),
                             ('La tormenta (Novela)', 'narrativa'), ('Estación Damasco (Best Seller | Ficción)', 'narrativa'),
                             ('¿Qué es una familia? (ÁLBUMES ILUSTRADOS)', 'infantil'),
                             ('Muchos, muchos animales (Otros Infantil)', 'infantil'),
                             ('Atlas de las cosas que vibran (ESPASAesPOESÍA)', 'poesia'),
                             ('Salamanca contada a los niños (Monumentos y ciudades)', 'infantil'),
                             ('Murdle JUNIOR 3 - Caso casi imposible', 'infantil'),
                             ('La maldición del amor verdadero (#Fantasy)', 'fantasia'),
                             ('Asesinato en la Casa Rosa (Los crímenes de Loeiro 1)', 'misterio-y-thriller')):
            with self.subTest(title):
                self.assertEqual(collection_genre(title), genre)

    def test_words_outside_the_collection_do_not_classify(self):
        for title in ('Forjando la Edad Media', 'CRUSH 1 - Un secreto llamado tú (Montena)',
                      'La novela de mi vida', 'Ficciones de la ciudad', 'La biblia del football (Ya lo sé)'):
            with self.subTest(title):
                self.assertIsNone(collection_genre(title))


class RepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = copy.deepcopy(DATA)
        q.repair_retire_non_reading(cls.data['libros'], ROOT, '2026-11-13')
        repair_classification(cls.data, '2026-11-13')
        cls.by_book = labels(cls.data)

    def test_nodes_no_longer_tag_a_childrens_fantasy_as_nutrition(self):
        self.assertTrue({'fantasia', 'infantil'} <= self.by_book[NACHO])
        self.assertFalse({'nutricion-y-bienestar', 'ciencia-ficcion'} & self.by_book[NACHO])

    def test_theme_gives_its_genre(self):
        self.assertIn('arte-y-diseno', self.by_book[MADRID])

    def test_no_genre_is_invented_from_a_title_word(self):
        self.assertNotIn('politica-y-actualidad', self.by_book.get(CONSPIRACY, set()))
        self.assertTrue(self.by_book.get(CONSPIRACY), 'conserva sus etiquetas aunque no haya género')

    def test_non_reading_titles_are_retired_and_novels_stay(self):
        state = {b['id']: b['estado'] for b in self.data['libros']}
        self.assertEqual(state[WATASHI], 'borrador')
        self.assertEqual(state[MYSTERY], 'publicado')

    def test_flag_from_the_price_sweep_retires(self):
        books = [{'id': SORRY, 'titulo': 'Sorry! But I Am With Hurry', 'estado': 'publicado',
                  'no_lectura': 'método de idiomas'}]
        self.assertEqual(q.repair_retire_non_reading(books, ROOT, '2026-11-13'), 1)
        self.assertEqual(books[0]['estado'], 'borrador')

    def test_retired_book_keeps_no_price(self):
        offer = {'formato': 'tapa-blanda', 'url': 'https://www.amazon.es/dp/X', 'precio_centimos': 1795,
                 'precio_referencia_centimos': 1890}
        books = [{'id': SORRY, 'titulo': 'Cuaderno de actividades', 'estado': 'publicado', 'no_lectura': 'actividades',
                  'formatos_compra': [offer]}]
        q.repair_retire_non_reading(books, ROOT, '2026-11-13')
        self.assertEqual(books[0]['formatos_compra'], [{'formato': 'tapa-blanda', 'url': 'https://www.amazon.es/dp/X'}])

    def test_no_published_book_is_left_without_labels(self):
        before = labels(DATA)
        for book in self.data['libros']:
            if book['estado'] == 'publicado' and before.get(book['id']):
                with self.subTest(book['id']):
                    self.assertTrue(self.by_book.get(book['id']))

    def test_no_published_book_loses_what_tells_the_reader_what_it_is(self):
        # «Para quién» (y la ficha) necesita género, temática, época o edad; «edición especial» no le dice nada.
        reader = {c['id'] for c in self.data['categorias'] if c.get('activa', True) and c['tipo'] in READER_TYPES}
        before = labels(DATA)
        for book in self.data['libros']:
            if book['estado'] == 'publicado' and before.get(book['id'], set()) & reader:
                with self.subTest(book['id']):
                    self.assertTrue(self.by_book.get(book['id'], set()) & reader)

    def test_fallback_genres_are_active_categories(self):
        cats = {c['id']: c for c in self.data['categorias']}
        for genre in set(FALLBACK_GENRES) & {c for s in self.by_book.values() for c in s}:
            self.assertEqual(cats[genre]['tipo'], 'genero')
            self.assertTrue(cats[genre].get('activa', True))

    def test_repair_is_idempotent(self):
        again = copy.deepcopy(self.data)
        q.repair_retire_non_reading(again['libros'], ROOT, '2026-11-14')
        repair_classification(again, '2026-11-14')
        self.assertEqual(labels(again), self.by_book)
        self.assertEqual([b['estado'] for b in again['libros']], [b['estado'] for b in self.data['libros']])

    def test_retired_book_page_is_dropped(self):
        slug = next(b['slug'] for b in self.data['libros'] if b['id'] == WATASHI)
        pages = q.retired_pages(self.data, ROOT)
        if (ROOT / f'recomendaciones/libros/{slug}/index.html').exists():
            self.assertIn(f'recomendaciones/libros/{slug}/index.html', pages)
        live = {b['slug'] for b in self.data['libros'] if b['estado'] == 'publicado'}
        self.assertFalse([p for p in pages if p.startswith('recomendaciones/libros/') and p.split('/')[2] in live])


class FallbackSignalTests(unittest.TestCase):
    CATS = [{'id': 'fantasia', 'tipo': 'genero'}, {'id': 'misterio-y-thriller', 'tipo': 'genero'},
            {'id': 'edicion-especial', 'tipo': 'formato'}]

    def catalogue(self, own):
        books = [{'id': f'b{i}', 'estado': 'publicado', 'autores': [author], 'editorial': 'Sello'}
                 for i, author in enumerate(own)]
        return {'categorias': self.CATS, 'libros': books}, {f'b{i}': {g} for i, g in enumerate(own.values())}

    def test_author_genre_comes_before_the_publisher(self):
        cat, by_book = self.catalogue({'Ana': 'fantasia'})
        cat['libros'] += [{'id': 'b9', 'estado': 'publicado', 'autores': ['Ana'], 'editorial': 'Otro'}]
        by_book['b9'] = {'fantasia'}
        for i in range(3):
            cat['libros'].append({'id': f'm{i}', 'estado': 'publicado', 'autores': [f'X{i}'], 'editorial': 'Sello'})
            by_book[f'm{i}'] = {'misterio-y-thriller'}
        fallback = GenreFallback(cat, by_book)
        self.assertEqual(fallback.pick({'autores': ['Ana'], 'editorial': 'Sello', 'titulo': 'Nueva'}, set()), 'fantasia')
        self.assertEqual(fallback.pick({'autores': ['Luis'], 'editorial': 'Sello', 'titulo': 'Nueva'}, set()),
                         'misterio-y-thriller')

    def test_one_title_of_the_author_is_not_enough(self):
        cat, by_book = self.catalogue({'Ana': 'fantasia'})
        self.assertIsNone(GenreFallback(cat, by_book).pick({'autores': ['Ana'], 'editorial': 'Otro', 'titulo': 'X'}, set()))

    def test_format_label_does_not_count_as_telling_the_reader(self):
        cat, by_book = self.catalogue({})
        fallback = GenreFallback(cat, by_book)
        self.assertNotIn('edicion-especial', fallback.reader)
        self.assertIn('fantasia', fallback.reader)


class RetiredRegistryTests(unittest.TestCase):
    """Una ficha retirada sigue declarada (deprecated): si no, el mapa del sitio pierde un destino sin explicación."""

    def test_retired_pages_stay_declared_and_live_ones_win(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('build_reading', ROOT / 'scripts/build-reading-catalogue.py')
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        old = [{'id': 'reading-book-a', 'url': '/a/', 'sourceFile': 'a/index.html'},
               {'id': 'reading-author-b', 'url': '/b/', 'sourceFile': 'b/index.html'},
               {'id': 'reading-book-c', 'url': '/c/', 'sourceFile': 'c/index.html'},
               {'id': 'reading-page-9', 'url': '/p/9/', 'sourceFile': 'p/9/index.html'}]
        gone = build.retired_entries(old, [{'id': 'reading-book-c'}])
        self.assertEqual([e['id'] for e in gone], ['reading-book-a', 'reading-author-b'])
        for entry in gone:
            self.assertEqual((entry['status'], entry['searchIndex'], entry['sitemap'], entry['sourceFile']),
                             ('deprecated', False, False, None))
        self.assertEqual(build.retired_entries(gone, []), gone, 'sigue declarada en las cargas siguientes')


if __name__ == '__main__':
    unittest.main()
