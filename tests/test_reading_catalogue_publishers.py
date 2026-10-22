"""Sellos del catálogo fuera del directorio de manuscritos; sin red."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_catalogue_publishers import PublisherError, catalogue_publisher, display_name, slugify

SOURCE = 'https://www.penguinlibros.com/es/libros/1-libro-x-9780140328721'
DIRECTORY = {'alfaguara', 'grijalbo'}


def make(name, store=None, **kw):
    store = store if store is not None else {'schema_version': 1, 'editoriales': []}
    return catalogue_publisher(name, store, kw.get('source', SOURCE), '2026-10-22',
                               directory_names=kw.get('names', DIRECTORY), directory_slugs=kw.get('slugs', {'alfaguara'})), store


class CataloguePublisherTests(unittest.TestCase):
    def test_display_names_keep_acronyms_and_small_words(self):
        self.assertEqual(display_name('PENGUIN CLÁSICOS'), 'Penguin Clásicos')
        self.assertEqual(display_name('DK'), 'DK')
        self.assertEqual(display_name('B DE BLOK'), 'B de Blok')
        self.assertEqual(slugify('Penguin Clásicos'), 'penguin-clasicos')

    def test_new_sello_is_registered_once_with_its_source(self):
        first, store = make('DEBATE')
        again, _ = make('Debate', store, source=SOURCE.replace('/1-libro', '/2-libro'))
        self.assertEqual((first['slug'], first['nombre']), ('debate', 'Debate'))
        self.assertEqual(len(store['editoriales']), 1)
        self.assertEqual(len(again['fuentes']), 2)

    def test_directory_names_are_never_duplicated(self):
        with self.assertRaises(PublisherError):
            make('ALFAGUARA')

    def test_untrusted_or_generic_names_and_hosts_are_refused(self):
        for bad in ('', 'Editorial', '<script>', 'x' * 80):
            with self.subTest(bad=bad), self.assertRaises(PublisherError):
                make(bad)
        with self.assertRaises(PublisherError):
            make('Debate', source='https://example.com/libro')

    def test_slug_collision_with_directory_is_refused(self):
        with self.assertRaises(PublisherError):
            make('Grijalbo!', slugs={'grijalbo'}, names=set())


if __name__ == '__main__':
    unittest.main()
