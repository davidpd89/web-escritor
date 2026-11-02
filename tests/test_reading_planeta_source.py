"""Contrato del lector de fichas de Planeta de Libros con una ficha real recortada."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from reading_editorial_sources import SourceError  # noqa: E402
from reading_planeta_source import planeta_edition, planeta_links  # noqa: E402

URL = 'https://www.planetadelibros.com/libro-cosamala/458658'
PAGE = (ROOT / 'tests/fixtures/planeta-ficha-cosamala.html').read_text(encoding='utf-8')


class PlanetaSourceTests(unittest.TestCase):
    def test_reads_edition_from_technical_sheet(self):
        record = planeta_edition(PAGE, URL)
        self.assertEqual(record['isbn13'], '9788432251436')
        self.assertEqual((record['titulo'], record['autores'], record['editorial']), ('Cosamala', ['Alana S. Portero'], 'Seix Barral'))
        self.assertEqual((record['fecha_publicacion_edicion'], record['precision_fecha']), ('2026-10-14', 'dia'))
        self.assertEqual((record['formato_edicion'], record['numero_paginas'], record['pvp_centimos']), ('tapa-blanda', 272, 2090))
        self.assertTrue(record['portada_fuente_url'].startswith('https://proassetspdlcom.cdnstatics2.com/usuaris/libros/thumbs/'))
        self.assertEqual(record['fuentes_autores']['Alana S. Portero'], 'https://www.planetadelibros.com/autor/alana-s-portero/000059415')
        self.assertLessEqual(len(record['sinopsis_breve'].split()), 25, 'Solo un extracto breve, nunca la sinopsis completa')

    def test_age_band_comes_from_the_topics_row_and_is_not_a_subject(self):
        self.assertEqual(planeta_edition(PAGE, URL)['edad_recomendada'], '')
        kids = PAGE.replace('<li><a href="https://www.planetadelibros.com/libros/novela-literaria/00012">Novela literaria</a></li>',
                            '<li><a href="https://www.planetadelibros.com/libros/de-9-a-12-anos/00099">De 9 a 12 años</a></li>'
                            '<li><a href="https://www.planetadelibros.com/libros/novela-literaria/00012">Novela literaria</a></li>')
        record = planeta_edition(kids, URL)
        self.assertEqual((record['edad_recomendada'], record['materias']), ('De 9 a 12 años', ['Novela literaria']))

    def test_rejects_other_hosts_and_changed_canonical(self):
        with self.assertRaises(SourceError):
            planeta_edition(PAGE, 'https://evil.example/libro-cosamala/458658')
        with self.assertRaises(SourceError):
            planeta_edition(PAGE, 'https://www.planetadelibros.com/libro-cosamala/999999')

    def test_rejects_invalid_isbn_non_physical_and_foreign_cover(self):
        for old, new in (('978-84-322-5143-6', '978-84-322-5143-1'), ('Rústica con solapas', 'Audiolibro digital'),
                         ('proassetspdlcom.cdnstatics2.com', 'cdn.invalid')):
            self.assertIn(old, PAGE)
            with self.subTest(old=old), self.assertRaises(SourceError):
                planeta_edition(PAGE.replace(old, new), URL)

    def test_canonical_reordering_cannot_hide_conflicting_edition(self):
        original = f'<link rel="canonical" href="{URL}"/>'
        self.assertIn(original, PAGE)
        mismatched = PAGE.replace(original, '<link href="https://www.planetadelibros.com/libro-cosamala/999999" rel="canonical"/>', 1)
        with self.assertRaises(SourceError):
            planeta_edition(mismatched, URL)
        reordered_valid = PAGE.replace(original, f"<link href='{URL}' REL='canonical'/>", 1)
        self.assertEqual(planeta_edition(reordered_valid, URL)['isbn13'], '9788432251436')
        duplicate = PAGE.replace(original, original + original, 1)
        with self.assertRaises(SourceError):
            planeta_edition(duplicate, URL)
        missing_href = PAGE.replace(original, '<link rel="canonical"/>', 1)
        with self.assertRaises(SourceError):
            planeta_edition(missing_href, URL)

    def test_rejects_catalan_edition(self):
        catalan = ('Una novel·la que els lectors no podran deixar perquè amb aquesta història els personatges també ' * 3)
        start = PAGE.find('<article>')
        self.assertGreater(start, 0)
        page = PAGE[:start] + '<article><p>' + catalan + '</p>' + PAGE[PAGE.find('</article>'):]
        with self.assertRaises(SourceError):
            planeta_edition(page.replace('Cosamala', 'Novel·la'), URL)

    def test_links_only_official_book_sheets(self):
        index = ('<a href="/libro-cosamala/458658">a</a><a href="https://www.planetadelibros.com/libro-cosamala/458658">b</a>'
                 '<a href="/autor/alana-s-portero/000059415">autor</a><a href="https://otro.example/libro-x/1">x</a>'
                 '<a href="/libro-con-parametro/12?soporte=12">p</a>')
        self.assertEqual(planeta_links(index, 'https://www.planetadelibros.com/libros-novedades/p/1'), [URL])


if __name__ == '__main__':
    unittest.main()
