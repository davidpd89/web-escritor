"""Offline edition identity, fail-closed parsing, covers and catalogue contracts."""
import copy
import html
import io
import json
import re
import sys
import tempfile
import unittest
import shutil
from unittest.mock import patch
from urllib.request import Request
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reading_editorial_sources import SourceError, CachedHTTP, _Redirects, allowed_url, penguin_edition, product_links
from reading_intake_pipeline import make_book, cover_bytes, update_authors, classify, work_key, builder
import reading_intake_pipeline as pipeline

URL = 'https://www.penguinlibros.com/es/fantasia/123-libro-prueba-9780140328721'


def document(**changes):
    product = {'reference': '9780140328721', 'name': 'Obra de prueba', 'category_name': 'Fantasía',
               'description': '<p>Una viajera encuentra una carta olvidada y sigue sus pistas hasta una ciudad abandonada, donde descubre los secretos de una familia separada por la guerra.</p>',
               'features': [{'name': k, 'value': v} for k, v in {
                   'Autor': 'Autora de prueba', 'Editorial': 'Salamandra', 'Idioma': 'ES',
                   'Region': 'ES', 'cod_tipo_material': 'ZLIB', 'Fecha de publicación': '2026-10-10',
                   'Tipo de encuadernación': 'Tapa dura', 'Páginas': '240', 'Target de edad': 'Adultos'}.items()],
               'cover': {'large': {'url': 'https://www.penguinlibros.com/es/123-cover/prueba.jpg'}}}
    product.update(changes)
    return '<link rel="canonical" href="' + URL + '"><div data-product="' + html.escape(json.dumps(product), quote=True) + '"></div>'


class SourceTests(unittest.TestCase):
    def test_redirects_consume_physical_budget_and_cannot_leave_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            http = CachedHTTP(Path(tmp), ['www.penguinlibros.com'], budget=2, delay=0)
            handler = _Redirects(http.hosts, http._before_request)
            http._before_request()
            result = handler.redirect_request(Request(URL), None, 302, 'Found', {}, URL + '/')
            self.assertEqual(http.requests, 2)
            self.assertEqual(result.full_url, URL + '/')
            with self.assertRaises(SourceError):
                handler.redirect_request(Request(URL), None, 302, 'Found', {}, URL + '/')
            self.assertEqual(http.requests, 2)
            with self.assertRaises(SourceError):
                handler.redirect_request(Request(URL), None, 302, 'Found', {}, 'https://example.com/other')
            self.assertEqual(http.requests, 2)

    def test_selected_edition_not_recommendations(self):
        value = penguin_edition(document() + document(reference='9780140449136'), URL)
        self.assertEqual(value['isbn13'], '9780140328721')
        self.assertEqual(value['fecha_publicacion_edicion'], '2026-10-10')
        self.assertEqual(value['formato_edicion'], 'tapa-dura')
        self.assertNotIn('precio', value)
        self.assertNotIn('descripcion', value)

    def test_ambiguous_or_wrong_edition_is_pending(self):
        for source in (document() * 2, document(reference='9780140449136'), document().replace('rel="canonical" href="' + URL, 'rel="canonical" href="https://example.com/other')):
            with self.assertRaises(SourceError):
                penguin_edition(source, URL)

    def test_repeated_author_features_preserve_coauthors(self):
        source = document().replace('{&quot;name&quot;: &quot;Autor&quot;,', '{&quot;name&quot;: &quot;Autor&quot;,')
        source = source.replace('], &quot;cover&quot;', ', {&quot;name&quot;: &quot;Autor&quot;, &quot;value&quot;: &quot;Coautor real&quot;}], &quot;cover&quot;')
        self.assertEqual(penguin_edition(source, URL)['autores'], ['Autora de prueba', 'Coautor real'])

    def test_month_remains_month_and_missing_date_rejected(self):
        value = penguin_edition(document().replace('2026-10-10', '2026-10'), URL)
        self.assertEqual((value['fecha_publicacion_edicion'], value['precision_fecha']), ('2026-10', 'mes'))
        with self.assertRaises(SourceError):
            penguin_edition(document().replace('2026-10-10', ''), URL)

    def test_non_spanish_or_missing_cover_rejected(self):
        for source in (document().replace('&quot;ES&quot;', '&quot;FR&quot;'), document(cover={})):
            with self.assertRaises(SourceError):
                penguin_edition(source, URL)

    def test_source_hosts_queries_and_isbn_checksums(self):
        source = ''.join('<a href="' + u + '">x</a>' for u in [URL, URL, URL + '?variant=1', URL.replace('penguinlibros.com', 'example.com'), URL[:-1] + '2'])
        self.assertEqual(product_links(source, URL), [URL])
        for bad in ('http://www.penguinlibros.com/a', 'https://user@www.penguinlibros.com/a', 'https://www.penguinlibros.com.evil.com/a', 'https://www.penguinlibros.com:444/a'):
            with self.assertRaises(SourceError):
                allowed_url(bad, ['www.penguinlibros.com'])

    def test_covers_are_real_optimized_images(self):
        out = io.BytesIO()
        Image.new('RGB', (600, 900), '#123456').save(out, 'PNG')
        cover, small, dimensions = cover_bytes(out.getvalue())
        self.assertEqual(dimensions, (600, 900))
        self.assertEqual(Image.open(io.BytesIO(small)).width, 320)
        self.assertEqual(Image.open(io.BytesIO(cover)).format, 'WEBP')
        with self.assertRaises((SourceError, OSError)):
            cover_bytes(b'<html>no cover</html>')


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.record = penguin_edition(document(), URL)
        self.record['cover_use_basis'] = 'Cubierta editorial para identificación bibliográfica.'
        self.book = make_book(self.record, {'name': 'Salamandra', 'slug': 'salamandra'}, 'davidporto-21', '2026-10-20', '/assets/reading-covers/test.png', (600, 900))

    def test_nightly_quota_fits_the_run_ceilings(self):
        config = json.loads((ROOT / 'data/reading-intake-config.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(config['max_new_books'], 60)
        self.assertLessEqual(config['max_new_books'], pipeline.MAX_NEW_CEILING)
        self.assertLessEqual(config['max_requests'], pipeline.MAX_REQUESTS_CEILING)
        with self.assertRaisesRegex(ValueError, 'techos'):
            pipeline.ingest({**config, 'max_requests': pipeline.MAX_REQUESTS_CEILING + 1}, ROOT, Path(tempfile.mkdtemp()))

    def test_affiliate_search_is_not_fake_product(self):
        self.assertIn('/s?k=9780140328721&tag=davidporto-21', self.book['amazon_busqueda_isbn'])
        self.assertNotIn('url_amazon_afiliada', self.book)
        self.assertNotIn('formatos_compra', self.book)
        self.assertNotIn('aggregateRating', self.book)

    def test_long_seo_titles_remain_bounded_and_distinct(self):
        self.book['titulo'] = 'Un título muy largo ' * 12
        title = builder.book_title(self.book)
        self.assertLessEqual(len(title), 75)
        self.assertIn(self.book['isbn13'], title)
        other = {**self.book, 'isbn13': '9780140449136'}
        self.assertNotEqual(title, builder.book_title(other))

    def test_partial_publication_never_gets_fake_day(self):
        self.record.update(precision_fecha='mes', fecha_publicacion_edicion='2026-10')
        b = make_book(self.record, {'name': 'Salamandra', 'slug': 'salamandra'}, 'davidporto-21', '2026-10-20', '/cover.webp', (600, 900))
        self.assertEqual(b['fecha_publicacion_parcial'], '2026-10')
        self.assertNotIn('fecha_publicacion', b)

    def test_author_biography_pinned_bibliography_updates(self):
        manual = {'nombre': 'Autora de prueba', 'slug': 'autora', 'nacimiento': '1980-01-01', 'descripcion': 'Manual'}
        payload = {'autores': [copy.deepcopy(manual)]}
        catalogue = {'libros': [self.book]}
        update_authors(payload, catalogue, [self.book], '2026-10-20')
        self.assertEqual(payload['autores'], [manual])
        payload = {'autores': []}
        update_authors(payload, catalogue, [self.book], '2026-10-20')
        profile = copy.deepcopy(payload['autores'][0])
        self.assertEqual(profile['tipo'], 'bibliografico')
        self.assertNotIn('nacimiento', profile)
        update_authors(payload, catalogue, [self.book], '2026-10-20')
        self.assertEqual(payload['autores'], [profile])

    def test_category_and_format_enter_existing_builder(self):
        original = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        data = {'schema_version': 1, 'categorias': original['categorias'], 'libros': [self.book], 'libro_categorias': []}
        cats = classify(self.record, data)
        data['libro_categorias'] = [{'libro_id': self.book['id'], 'categoria_id': c} for c in cats]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cover = root / self.book['portada_local'].lstrip('/')
            cover.parent.mkdir(parents=True)
            Image.new('RGB', (600, 900), 'blue').save(cover)
            publisher = root / 'editoriales/salamandra/index.html'
            publisher.parent.mkdir(parents=True); publisher.touch()
            self.assertEqual(builder.validate(data, root), [self.book])
            self.book['amazon_busqueda_isbn'] = self.book['amazon_busqueda_isbn'].replace('9780140328721', '9780140449136')
            with self.assertRaises(builder.ValidationError):
                builder.validate(data, root)

    def test_planeta_sheet_reveals_isbn_and_is_not_republished(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            source = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
            source['libros'], source['libro_categorias'] = [], []
            (root / 'data/reading-catalogue.json').write_text(json.dumps(source), encoding='utf-8')
            (root / 'data/reading-authors.json').write_text(json.dumps({'schema_version': 1, 'autores': []}), encoding='utf-8')
            shutil.copy(ROOT / 'data/editoriales.json', root / 'data/editoriales.json')
            (root / 'editoriales/seix-barral').mkdir(parents=True); (root / 'editoriales/seix-barral/index.html').touch()
            page_url = 'https://www.planetadelibros.com/libro-cosamala/458658'
            index = 'https://www.planetadelibros.com/libros-novedades/p/1'
            page = (ROOT / 'tests/fixtures/planeta-ficha-cosamala.html').read_text(encoding='utf-8')
            cover_url = re.search(r'href="(https://proassetspdlcom[^"]+)"', page).group(1)
            image = io.BytesIO(); Image.new('RGB', (600, 900), 'blue').save(image, 'PNG')
            responses = {index: ('<a href="/libro-cosamala/458658">libro</a><a href="/libro-roto/1">roto</a>').encode(),
                         page_url: page.encode(), cover_url: image.getvalue()}
            class FakeHTTP:
                def __init__(self, *args, **kwargs):
                    self.requests = self.hits = 0; self.budget = 80
                    FakeHTTP.hosts = args[1]
                def get(self, url, **kwargs):
                    self.requests += 1
                    if url not in responses:
                        raise OSError('sin respuesta')
                    return responses[url]
            config = json.loads((ROOT / 'data/reading-intake-config.json').read_text(encoding='utf-8'))
            planeta = next(src for src in config['sources'] if src['provider'] == 'planeta')
            config['sources'] = [planeta]
            config['author_wikipedia']['enabled'] = False
            with patch.object(pipeline, 'CachedHTTP', FakeHTTP):
                today = '2026-10-20'
                first = pipeline.ingest(config, root, root / '.cache', apply=True, today=today)
                second = pipeline.ingest(config, root, root / '.cache', apply=True, today=today)
            self.assertEqual(first['stats']['accepted'], 1, first['state'])
            self.assertIn('proassetspdlcom.cdnstatics2.com', FakeHTTP.hosts)
            saved = json.loads((root / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
            book = saved['libros'][0]
            self.assertEqual((book['isbn13'], book['pvp_centimos'], book['editorial']), ('9788432251436', 2090, 'Seix Barral'))
            self.assertEqual(book['fuente_bibliografica_url'], page_url)
            self.assertEqual(book['editorial_slug'], 'seix-barral')
            from reading_catalogue_publishers import catalogue_publisher
            store = {'schema_version': 1, 'editoriales': []}
            self.assertEqual(catalogue_publisher('PAIDÓS CÓMIC', store, page_url, today, directory_names=set(), directory_slugs=set())['grupo'], 'Grupo Planeta')
            self.assertEqual(second['stats']['accepted'], 0)
            self.assertEqual(second['stats']['already_published'], 1)

    def test_work_dedupe_preserves_series_volume(self):
        self.assertEqual(work_key('Obra (edición especial)', ['Autora']), work_key('Obra', ['Autora']))
        self.assertNotEqual(work_key('Obra 2', ['Autora']), work_key('Obra 3', ['Autora']))

    def test_bad_candidate_isolated_manual_book_pinned_and_repeated_run_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            source = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
            manual = copy.deepcopy(next(b for b in source['libros'] if b['slug'] == 'coraline'))
            source['libros'] = [manual]
            source['libro_categorias'] = [r for r in source['libro_categorias'] if r['libro_id'] == manual['id']]
            (root / 'data/reading-catalogue.json').write_text(json.dumps(source), encoding='utf-8')
            (root / 'data/reading-authors.json').write_text(json.dumps({'schema_version': 1, 'autores': []}), encoding='utf-8')
            shutil.copy(ROOT / 'data/editoriales.json', root / 'data/editoriales.json')
            for key in ('portada_local', 'audio_descripcion'):
                target = root / manual[key].lstrip('/')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / manual[key].lstrip('/'), target)
            publisher = root / 'editoriales/salamandra/index.html'
            publisher.parent.mkdir(parents=True); publisher.touch()
            url2 = URL.replace('9780140328721', '9780140449136')
            bad = URL.replace('9780140328721', '9780141187761')
            index = 'https://www.penguinlibros.com/es/'
            responses = {index: ''.join('<a href="' + u + '">book</a>' for u in [bad, URL, url2]).encode(), bad: document(reference='9780141187761', description='').replace(URL, bad).encode(),
                         URL: document().encode(),
                         url2: document(reference='9780140449136', name='Segunda obra de prueba').replace(URL, url2).replace('prueba.jpg', 'prueba2.jpg').encode()}
            for suffix, color in [('prueba.jpg', 'green'), ('prueba2.jpg', 'red')]:
                image = io.BytesIO(); Image.new('RGB', (600, 900), color).save(image, 'PNG')
                responses['https://www.penguinlibros.com/es/123-cover/' + suffix] = image.getvalue()
            class FakeHTTP:
                def __init__(self, *args, **kwargs):
                    self.requests = self.hits = 0; self.budget = 80
                def get(self, url, **kwargs):
                    self.requests += 1
                    return responses[url]
            config = json.loads((ROOT / 'data/reading-intake-config.json').read_text(encoding='utf-8'))
            config['sources'][0]['index_urls'] = [index]
            config['sources'] = config['sources'][:1]  # este contrato es solo de Penguin; Planeta tiene su propia prueba
            config['generate_audio'] = False
            with patch.object(pipeline, 'CachedHTTP', FakeHTTP):
                first = pipeline.ingest(config, root, root / '.cache', apply=True, today='2026-10-20')
                saved = (root / 'data/reading-catalogue.json').read_bytes()
                second = pipeline.ingest(config, root, root / '.cache', apply=True, today='2026-10-20')
            self.assertEqual((first['stats']['accepted'], first['stats']['pending']), (2, 1))
            self.assertIn('Sinopsis editorial ausente',first['state']['items']['isbn13:9780141187761']['motivo'])
            self.assertEqual(second['stats']['accepted'], 0)
            self.assertEqual((root / 'data/reading-catalogue.json').read_bytes(), saved)
            result = json.loads(saved)
            self.assertEqual(result['libros'][0], manual)
            self.assertEqual(len(result['libros']), 3)
            # Editorial enrichment must survive the weekly metadata refresh.
            result['libro_categorias'].append({'libro_id': result['libros'][1]['id'], 'categoria_id': 'halloween'})
            (root / 'data/reading-catalogue.json').write_text(json.dumps(result), encoding='utf-8')
            responses[URL] = responses[URL].replace(b'240', b'244')
            with patch.object(pipeline, 'CachedHTTP', FakeHTTP):
                third = pipeline.ingest(config, root, root / '.cache', apply=True, today='2026-10-28')
            refreshed = json.loads((root / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
            self.assertEqual(third['stats']['updated'], 2)
            self.assertEqual(third['stats']['accepted'], 0)
            self.assertEqual(refreshed['libros'][0], manual)
            self.assertEqual(refreshed['libros'][1]['numero_paginas'], 244)
            self.assertEqual(refreshed['libros'][1]['slug'], result['libros'][1]['slug'])
            self.assertEqual(refreshed['libros'][1]['fecha_publicacion'], '2026-10-10')
            self.assertIn({'libro_id': result['libros'][1]['id'], 'categoria_id': 'halloween'}, refreshed['libro_categorias'])
            # A partial source response must never replace a real synopsis with
            # the generated bibliographic fallback on the next weekly refresh.
            complete = responses[URL]
            responses[URL] = document(description='').encode()
            with patch.object(pipeline, 'CachedHTTP', FakeHTTP):
                missing = pipeline.ingest(config, root, root / '.cache', apply=True, today='2026-11-05')
            preserved = json.loads((root / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
            self.assertEqual(preserved['libros'][1],refreshed['libros'][1])
            self.assertIn('Sinopsis editorial ausente',missing['state']['items']['isbn13:9780140328721']['ultima_revision_error'])
            responses[URL] = complete
            # A changed source identity is quarantined while its public entry survives.
            responses[URL] = responses[URL].replace(b'Autora de prueba', b'Otra autora')
            with patch.object(pipeline, 'CachedHTTP', FakeHTTP):
                fourth = pipeline.ingest(config, root, root / '.cache', apply=True, today='2026-11-13')
            evidence = fourth['state']['items']['isbn13:9780140328721']
            self.assertEqual(evidence['estado_ingesta'], 'publicado')
            self.assertIn('ultima_revision_error', evidence)
            final = json.loads((root / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
            self.assertEqual(final['libros'][1], refreshed['libros'][1])


if __name__ == '__main__':
    unittest.main()
