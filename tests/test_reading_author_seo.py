"""Title y description de las fichas de autor: datos propios de cada persona y nada falso («y otros libros» con uno)."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('build_reading_catalogue_seo', ROOT / 'scripts' / 'build-reading-catalogue.py')
b = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = b
_spec.loader.exec_module(b)


def book(titulo, editorial='Salamandra', fecha='2024-03-01'):
    return {'titulo': titulo, 'editorial': editorial, 'fecha_publicacion': fecha}


class AuthorRoleTest(unittest.TestCase):
    def test_role_from_biography(self):
        self.assertEqual(b.author_role('Neil Gaiman es un escritor y guionista británico nacido en Portchester en 1960.'), 'escritor y guionista británico')
        self.assertEqual(b.author_role('Roberto Saviano (Nápoles, 1979) es un escritor, periodista y guionista italiano. Con veintiséis…'), 'escritor, periodista y guionista italiano')

    def test_no_role_without_profession(self):
        self.assertEqual(b.author_role('La hija del veneno es la séptima novela de Sheila Masterson.'), '')
        self.assertEqual(b.author_role('Arturo Pérez-Reverte nació en Cartagena en 1951.'), '')


class AuthorSeoTest(unittest.TestCase):
    def test_single_book_does_not_claim_more(self):
        a = {'nombre': 'Ana Prueba', 'tipo': 'bibliografico', 'descripcion': ''}
        title, meta = b.author_seo(a, [book('El faro')], None, [], False, True)
        self.assertEqual(title, 'Libros de Ana Prueba: «El faro»')
        self.assertNotIn('otros libros', title)
        self.assertIn('«El faro», de Ana Prueba', meta)
        self.assertIn('Salamandra, 2024', meta)

    def test_several_books_list_titles_and_role(self):
        a = {'nombre': 'Ana Prueba', 'tipo': 'bibliografico', 'biografia_breve': 'Ana Prueba es una novelista gallega que vive en Vigo.'}
        books = [book('Uno'), book('Dos'), book('Tres'), book('Cuatro')]
        title, meta = b.author_seo(a, books, None, [{'nombre': 'Novela negra'}], True, True)
        self.assertEqual(title, 'Libros de Ana Prueba: Uno, Dos y más')
        self.assertTrue(meta.startswith('Libros de Ana Prueba, novelista gallega: Uno, Dos, Tres y más.'), meta)
        self.assertLessEqual(len(meta), 158)

    def test_own_text_uses_where_to_start_and_sagas(self):
        a = {'nombre': 'Ana Prueba', 'tipo': 'bibliografico'}
        own = {'intro': 'Ana Prueba es una escritora.', 'por_donde_empezar': [{'titulo': 'Uno'}, {'titulo': 'Dos'}],
               'sagas': [{'nombre': 'La Saga'}]}
        title, meta = b.author_seo(a, [book('Uno')], own, [], True, True)
        self.assertIn('por dónde empezar: Uno o Dos', meta)
        self.assertIn('La Saga', meta)
        self.assertLessEqual(len(title), 60)


if __name__ == '__main__':
    unittest.main()
