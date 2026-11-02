"""Sinopsis completa en la ficha y taxonomía canónica de las materias editoriales."""
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_editorial_sources import editorial_excerpt, editorial_synopsis, publisher_author_bio
import reading_intake_pipeline as pipeline

spec = importlib.util.spec_from_file_location('reading_catalogue_synopsis', ROOT / 'scripts/build-reading-catalogue.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

HTML = ('<p>Harry Hole ha encontrado trabajo en una compañía de seguros, investigando posibles fraudes de sus clientes. '
        'Podría ser pan comido si Harry no se empeñara una y otra vez en hacerse la vida imposible.</p>'
        '<p>Un asesino en serie está montando su obra maestra, y a Harry le va a ser imposible mantenerse al margen.</p>'
        '<p>Reseñas:</p><p>«Una novela extraordinaria», dice la crítica.</p>')


def catalogue():
    return {'categorias': [
        {'id': 'narrativa', 'slug': 'narrativa', 'nombre': 'Narrativa contemporánea', 'tipo': 'genero', 'descripcion': '.', 'orden': 1, 'activa': True},
        {'id': 'juvenil', 'slug': 'juvenil', 'nombre': 'Juvenil', 'tipo': 'edad', 'descripcion': '.', 'orden': 110, 'activa': True},
    ], 'libros': [], 'libro_categorias': []}


class FullSynopsisTests(unittest.TestCase):
    def test_full_synopsis_keeps_every_paragraph_and_stops_at_reviews(self):
        full = editorial_synopsis(HTML)
        self.assertIn('se empeñara una y otra vez', full)
        self.assertIn('mantenerse al margen.', full)
        self.assertNotIn('extraordinaria', full)
        self.assertEqual(full.count('\n\n'), 1)
        self.assertFalse(editorial_excerpt(HTML).endswith('margen.'))

    def test_broken_utf8_never_becomes_a_full_synopsis(self):
        # Penguin sirve a veces un byte UTF-8 cortado («estÃ</BR>»): decodificado con replace deja U+FFFD.
        page = '<p>' + 'En este libro aprenderás a detectar si alguno de tus órganos est' + '�' + ' sufriendo y cómo cuidarlo.</p>'
        self.assertEqual(editorial_synopsis(page), '')

    def test_inline_tags_do_not_add_spaces_before_punctuation_or_inside_words(self):
        html = '<p>En <em>El paraíso perdido</em>, de Milton, el arcángel revela una histo<b>ria</b> futura que Eva no debe escuchar nunca.</p>'
        self.assertEqual(editorial_synopsis(html), 'En El paraíso perdido, de Milton, el arcángel revela una historia futura que Eva no debe escuchar nunca.')
        self.assertIn('perdido, de', editorial_excerpt(html))

    def test_published_synopses_have_no_space_before_punctuation(self):
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        bad = [b['id'] for b in data['libros'] for k in ('sinopsis_completa', 'sinopsis_breve') if re.search(r'\w [,.;:)]', b.get(k) or '')]
        self.assertEqual(bad, [])

    def test_month_only_publication_date_still_reaches_the_book_schema(self):
        page = (ROOT / 'recomendaciones/libros/eva-esta-dormida-9788410171817/index.html').read_text(encoding='utf-8')
        self.assertIn('"datePublished": "2026-04"', page)

    def test_too_short_text_is_not_a_synopsis(self):
        self.assertEqual(editorial_synopsis('<p>Novela negra.</p>'), '')

    def test_ficha_renders_paragraphs_and_cards_stay_short(self):
        book = {'sinopsis_completa': 'Primer párrafo con texto suficiente. ' * 5 + '\n\n' + 'Segundo párrafo. ' * 40,
                'sinopsis_tipo': 'extracto_editorial', 'sinopsis_breve': 'Breve.'}
        self.assertEqual(len(builder.synopsis_paragraphs(book)), 2)
        self.assertLessEqual(len(builder.card_synopsis(book)), 201)
        self.assertTrue(builder.card_synopsis(book).endswith('…'))
        self.assertNotIn('\n', builder.meta_synopsis(book))

    def test_backfill_reads_official_page_once_and_checks_isbn(self):
        data = {'libros': [{'isbn13': '9791387740382', 'fuente_bibliografica_url': 'https://editorial.example/ficha'},
                           {'isbn13': '9780000000002', 'sinopsis_tipo': 'resumen_propio', 'fuente_bibliografica_url': 'https://editorial.example/otra'}]}

        class HTTP:
            requests, budget = 0, 10
            def get(self, url, ttl=None):
                self.requests += 1
                return b'<html></html>'
        http = HTTP()
        record = {'isbn13': '9791387740382', 'sinopsis_completa': editorial_synopsis(HTML), 'sinopsis_breve': 'Breve.'}
        with patch.object(pipeline, 'provider_of', return_value='generic'), patch.object(pipeline, 'read_edition', return_value=record):
            self.assertEqual(pipeline.fill_full_synopses(data, {}, http), 1)
        self.assertIn('mantenerse al margen', data['libros'][0]['sinopsis_completa'])
        self.assertNotIn('sinopsis_completa', data['libros'][1])
        self.assertEqual(http.requests, 1)
        with patch.object(pipeline, 'provider_of', return_value='generic'), patch.object(pipeline, 'read_edition', return_value={**record, 'isbn13': '9780000000019'}):
            other = {'libros': [{'isbn13': '9791387740382', 'fuente_bibliografica_url': 'https://editorial.example/ficha'}]}
            self.assertEqual(pipeline.fill_full_synopses(other, {}, http), 0)


class AuthorBiographyTests(unittest.TestCase):
    def page(self, text):
        return ('<html><head><link rel="canonical" href="https://www.penguinlibros.com/es/773-autora">'
                '<meta property="og:title" content="Autora Ejemplo"><meta name="description" content="' + text + '"></head></html>')

    def test_biography_keeps_whole_sentences(self):
        text = 'Autora Ejemplo nació en Cartagena en 1951 y fue reportera de guerra durante muchos años. ' * 3
        bio = publisher_author_bio(self.page(text), 'https://www.penguinlibros.com/es/773-autora', 'Autora Ejemplo')
        self.assertEqual(bio, ' '.join(text.split()))
        long = bio + ' ' + bio + ' ' + bio + ' ' + bio + ' ' + bio + ' ' + bio + ' ' + bio
        clipped = publisher_author_bio(self.page(long), 'https://www.penguinlibros.com/es/773-autora', 'Autora Ejemplo')
        self.assertLessEqual(len(clipped), 650)
        self.assertTrue(clipped.endswith('años.'))

    def test_published_biographies_are_not_clipped(self):
        import json
        authors = json.loads((ROOT / 'data/reading-authors.json').read_text(encoding='utf-8'))['autores']
        self.assertFalse([a['nombre'] for a in authors if (a.get('biografia_breve') or '').endswith('…')])


class TaxonomyTests(unittest.TestCase):
    def classify(self, *subjects):
        data = catalogue()
        with patch.object(pipeline, 'extra_categories', return_value=[]):
            return pipeline.classify({'materias': list(subjects)}, data), data

    def test_synonyms_share_one_filter_option(self):
        for subject in ('Narrativa', 'Novela contemporánea', 'Novela literaria'):
            found, data = self.classify(subject)
            self.assertEqual(found, ['narrativa'])
            self.assertEqual(len(data['categorias']), 2)

    def test_juvenile_subject_maps_to_genre_plus_age(self):
        found, _ = self.classify('Ciencia ficción juvenil')
        self.assertEqual(found, ['juvenil', 'ciencia-ficcion'])

    def test_section_names_are_not_topics(self):
        found, data = self.classify('Temáticas', 'Novela literaria')
        self.assertEqual(found, ['narrativa'])
        self.assertFalse(any(c['id'] == 'tema-tematicas' for c in data['categorias']))

    def test_age_bands_sort_by_age(self):
        data = catalogue()
        with patch.object(pipeline, 'extra_categories', return_value=[]):
            for subject in ('A partir de 9 años', 'De 0 a 3 años', 'A partir de 4 años'):
                pipeline.classify({'materias': [subject]}, data)
        bands = sorted((c for c in data['categorias'] if c['id'].startswith('edad-')), key=lambda c: c['orden'])
        self.assertEqual([c['nombre'] for c in bands], ['De 0 a 3 años', 'A partir de 4 años', 'A partir de 9 años'])

    def test_manga_subjects_join_comic_instead_of_a_new_topic(self):
        # Planeta etiqueta su manga como «Manga», «Manga Shonen» o «Manga Seinen»; sin mapa, la ingesta creaba tema-manga.
        data = catalogue()
        with patch.object(pipeline, 'extra_categories', return_value=[]):
            for subject in ('Manga', 'Manga Shonen', 'Manga Seinen', 'Cómic manga'):
                self.assertEqual(pipeline.classify({'materias': [subject]}, data)[0], 'comic-y-novela-grafica', subject)
        self.assertFalse([c['id'] for c in data['categorias'] if 'manga' in c['id']])

    def test_published_catalogue_has_no_redundant_topics(self):
        import json
        data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        ids = {c['id'] for c in data['categorias']}
        for duplicate in ('tema-narrativa', 'tema-novela-literaria', 'tema-tematicas', 'tema-salud', 'tema-manga'):
            self.assertNotIn(duplicate, ids)
        edad = sorted((c for c in data['categorias'] if c['id'].startswith('edad-')), key=lambda c: c['orden'])
        ages = [int(next(iter(re.findall(r'\d+', c['id'])), 0)) for c in edad]
        self.assertEqual(ages, sorted(ages))


if __name__ == '__main__':
    unittest.main()
