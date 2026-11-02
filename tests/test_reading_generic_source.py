"""Contrato del conector genérico (Anagrama, Nórdica, Periférica) con fichas reales recortadas; sin red."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from reading_editorial_sources import SourceError  # noqa: E402
from reading_generic_source import REVIEWED, _infer_subject, generic_edition, generic_links, reviewed_hosts  # noqa: E402

CONFIG = {s['id']: s for s in json.loads((ROOT / 'data/reading-intake-config.json').read_text(encoding='utf-8'))['sources']}
FIXTURES = ROOT / 'tests/fixtures'
ANAGRAMA = CONFIG['anagrama-es']
NORDICA = CONFIG['nordica-es']
A_URL = 'https://www.anagrama-ed.es/libro/cronicas/perder-la-guerra/9788433951298/CR_150'
A_PAGE = (FIXTURES / 'generic-ficha-anagrama.html').read_text(encoding='utf-8')
N_URL = 'https://nordicalibros.com/product/glifo/'
N_PAGE = (FIXTURES / 'generic-ficha-nordica.html').read_text(encoding='utf-8')
PERIFERICA = CONFIG['periferica-es']
P_URL = 'https://www.editorialperiferica.com/libros/munda/'
P_PAGE = (FIXTURES / 'generic-ficha-periferica.html').read_text(encoding='utf-8')


class GenericSourceTests(unittest.TestCase):
    def test_every_enabled_generic_source_is_reviewed_with_exact_hosts(self):
        for source in CONFIG.values():
            if source['provider'] == 'generic':
                self.assertEqual(reviewed_hosts(source), REVIEWED[source['id']])
        with self.assertRaises(SourceError):
            reviewed_hosts({**ANAGRAMA, 'cover_hosts': ['cms.anagrama-ed.es', 'evil.example']})
        with self.assertRaises(SourceError):
            reviewed_hosts({**ANAGRAMA, 'id': 'otra-editorial'})

    def test_anagrama_reads_schema_org_book(self):
        record = generic_edition(ANAGRAMA, A_PAGE, A_URL)
        self.assertEqual((record['isbn13'], record['titulo'], record['autores']), ('9788433951298', 'Perder la guerra', ['Jon Lee Anderson']))
        self.assertEqual((record['editorial'], record['fecha_publicacion_edicion'], record['precision_fecha']), ('Editorial Anagrama', '2026-11-11', 'dia'))
        self.assertEqual((record['formato_edicion'], record['numero_paginas'], record['pvp_centimos']), ('tapa-blanda', 408, 2990))
        self.assertEqual((record['coleccion'], record['materias']), ('Crónicas', ['Crónica']))
        self.assertTrue(record['portada_fuente_url'].startswith('https://cms.anagrama-ed.es/'))
        self.assertLessEqual(len(record['sinopsis_breve'].split()), 25, 'Solo un extracto breve')

    def test_nordica_reads_technical_sheet_and_flips_author_name(self):
        record = generic_edition(NORDICA, N_PAGE, N_URL)
        self.assertEqual((record['isbn13'], record['titulo'], record['autores']), ('9791388306174', 'Glifo', ['Ali Smith']))
        self.assertEqual((record['fecha_publicacion_edicion'], record['formato_edicion'], record['numero_paginas']), ('2026-09-21', 'tapa-blanda', 240))
        self.assertEqual(record['pvp_centimos'], 1099)
        self.assertEqual(record['materias'], ['Narrativa'], 'La materia sale del código Thema FBA de la ficha, no de «historia» en la sinopsis')

    def test_periferica_month_date_profile_synopsis_and_default_binding(self):
        record = generic_edition(PERIFERICA, P_PAGE, P_URL)
        self.assertEqual((record['isbn13'], record['titulo'], record['autores']), ('9788410171985', 'Munda', ['Juan Cárdenas']))
        self.assertEqual((record['fecha_publicacion_edicion'], record['precision_fecha']), ('2026-11', 'mes'))
        self.assertEqual((record['formato_edicion'], record['numero_paginas']), ('tapa-blanda', 224))
        self.assertTrue(record['sinopsis_breve'], 'La sinopsis sale del bloque #description del perfil')
        with self.assertRaises(SourceError):
            generic_edition({**PERIFERICA, 'default_format': ''}, P_PAGE, P_URL)

    def test_subject_needs_more_than_one_stray_word(self):
        self.assertEqual(_infer_subject('La comadrona', 'Una novela sobre la historia de una mujer y un poema de su madre, una novela coral'), ['Narrativa'])
        self.assertEqual(_infer_subject('Glosas', 'Un poemario: poemas sobre la poesía'), ['Poesía'])
        # Un misterio con «diarios secretos» y «memorias» del sospechoso sigue siendo narrativa.
        self.assertEqual(_infer_subject('Clue. El misterio del reloj', 'Los detectives leen los diarios secretos y las memorias del relojero'), ['Narrativa'])
        self.assertEqual(_infer_subject('Una vida', 'Libro de memorias de la autora'), ['Biografías y memorias'])
        self.assertEqual(_infer_subject('Sin pistas', 'La historia de un estudio'), [])

    def test_links_are_limited_to_reviewed_host_and_product_path(self):
        index = (FIXTURES / 'generic-index-anagrama.html').read_text(encoding='utf-8')
        links = generic_links(ANAGRAMA, index, 'https://www.anagrama-ed.es/catalogo')
        self.assertEqual(len(links), 6)
        self.assertTrue(all(url.startswith('https://www.anagrama-ed.es/libro/') for url in links))
        self.assertEqual(len(set(links)), len(links))

    def test_rejects_foreign_host_wrong_path_and_changed_canonical(self):
        with self.assertRaises(SourceError):
            generic_edition(ANAGRAMA, A_PAGE, 'https://evil.example/libro/cronicas/perder-la-guerra/9788433951298/CR_150')
        with self.assertRaises(SourceError):
            generic_edition(ANAGRAMA, A_PAGE, 'https://www.anagrama-ed.es/autor/anderson-jon-lee')
        with self.assertRaises(SourceError):
            generic_edition(NORDICA, N_PAGE.replace('<link rel="canonical" href="https://nordicalibros.com/product/glifo/" />',
                                                    '<link rel="canonical" href="https://nordicalibros.com/product/otro/" />'), N_URL)

    def test_rejects_invalid_isbn_unknown_binding_foreign_cover_and_non_spanish(self):
        cases = (
            (ANAGRAMA, A_PAGE, A_URL, '978-84-339-5129-8', '978-84-339-5129-1'),
            (ANAGRAMA, A_PAGE, A_URL, 'https://schema.org/Paperback', 'https://schema.org/AudiobookFormat'),
            (ANAGRAMA, A_PAGE, A_URL, 'cms.anagrama-ed.es', 'cdn.invalid'),
            (NORDICA, N_PAGE, N_URL, 'Encuadernación:', 'Tamaño:'),
        )
        for source, page, url, old, new in cases:
            self.assertIn(old, page)
            with self.subTest(old=old), self.assertRaises(SourceError):
                generic_edition(source, page.replace(old, new), url)

    def test_catalan_edition_is_not_published_as_castilian(self):
        catalan = A_PAGE.replace('Este libro reúne los reportajes', 'Aquest llibre aplega els reportatges')
        for word in (' el ', ' la ', ' los ', ' las ', ' que ', ' con ', ' por '):
            catalan = catalan.replace(word, ' els ' if word.strip() in ('el', 'los') else ' amb ')
        with self.assertRaises(SourceError):
            generic_edition(ANAGRAMA, catalan, A_URL)


if __name__ == '__main__':
    unittest.main()
