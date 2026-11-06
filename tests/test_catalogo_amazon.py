"""Pipeline local del catálogo desde Amazon: transformación y recorrido de nodos con datos de prueba, sin red."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import catalogo_amazon as ca  # noqa: E402


def isbn(prefix):
    """Completa un ISBN-13 de 12 dígitos con su dígito de control."""
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(prefix))
    return prefix + str((10 - total % 10) % 10)


def item(asin='B000000001', ean=None, title='La casa del faro', lang='Español', binding='Tapa blanda',
         authors=(('Pérez Galdós, Benito', 'Autor'),), publisher='Ediciones del Faro', date='2026-11-06',
         nodes=None):
    info = {'title': {'displayValue': title},
            'externalIds': {'eans': {'displayValues': [ean or isbn('978841234567')]}},
            'byLineInfo': {'contributors': [{'name': n, 'role': r} for n, r in authors],
                           'manufacturer': {'displayValue': publisher}},
            'classifications': {'binding': {'displayValue': binding}},
            'contentInfo': {'publicationDate': {'displayValue': date}, 'pagesCount': {'displayValue': 320}}}
    if lang:
        info['contentInfo']['languages'] = {'displayValues': [{'displayValue': lang, 'type': 'Publicado'}]}
    return {'asin': asin, 'itemInfo': info,
            'browseNodeInfo': {'browseNodes': nodes if nodes is not None else [{'displayName': 'Novela negra',
                                                         'ancestor': {'displayName': 'Literatura y ficción',
                                                                      'ancestor': {'displayName': 'Libros'}}}]}}


class ToRecord(unittest.TestCase):
    def test_latin_spanish_and_bunko_paperback_are_accepted(self):
        rec = ca.to_record({'item': item(lang='Español latino', binding='Tapa blanda (Bunko)')}, '2026-11-06')
        self.assertEqual(rec['formato_edicion'], 'tapa-blanda')
        with self.assertRaises(ca.Rejected):
            ca.to_record({'item': item(lang='Catalán')}, '2026-11-06')

    def test_maps_amazon_item_to_book_record(self):
        r = ca.to_record({'nodo': '1', 'ruta': ['Libros', 'Thriller'], 'item': item()}, '2026-11-06')
        self.assertEqual(r['autores'], ['Benito Pérez Galdós'])
        self.assertEqual(r['formato_edicion'], 'tapa-blanda')
        self.assertEqual(r['editorial'], 'Ediciones del Faro')
        self.assertEqual(r['fecha_publicacion_edicion'], '2026-11-06')
        self.assertEqual(r['numero_paginas'], 320)
        self.assertEqual((r['materias'], r['palabras_clave']), (['Misterio'], ['Novela negra', 'Thriller']))
        self.assertTrue(r['fuente_bibliografica_url'].endswith('/dp/B000000001'))

    def test_each_rejection_names_its_reason(self):
        cases = {
            'idioma: catalan': item(lang='Catalán'),
            'sin idioma y con ISBN extranjero': item(lang=None, ean=isbn('978012345678')),
            'sin autoría': item(authors=()),
            'sin editorial': item(publisher=''),
            'encuadernación: Calendario': item(binding='Calendario'),
            'sin fecha de publicación': item(date=''),
            'sin ISBN-13': item(ean='123'),
        }
        for reason, it in cases.items():
            with self.subTest(reason), self.assertRaises(ca.Rejected) as ctx:
                ca.to_record({'item': it}, '2026-11-06')
            self.assertEqual(str(ctx.exception), reason)

    def test_isbn_as_manufacturer_is_not_a_publisher(self):
        with self.assertRaises(ca.Rejected) as ctx:
            ca.to_record({'item': item(publisher='978-628-01-9180-5')}, '2026-11-06')
        self.assertEqual(str(ctx.exception), 'sin editorial')
        self.assertEqual(ca.publisher_name({'displayValue': 'Ediciones 2001'}), 'Ediciones 2001')

    def test_spanish_isbn_without_language_is_accepted(self):
        self.assertEqual(ca.to_record({'item': item(lang=None)}, '2026-11-06')['isbn13'][:5], '97884')

    def test_store_nodes_are_not_subjects(self):
        nodes = [{'displayName': 'Libros en castellano'}, {'displayName': 'Tienda PRH'},
                 {'displayName': 'Literaria', 'ancestor': {'displayName': 'Ficción por género'}},
                 {'displayName': 'Libros físicos'}, {'displayName': 'Promoción Día del Libro'},
                 {'displayName': 'Botiga de Llibres en català'}, {'displayName': 'Español'},
                 {'displayName': 'Regular Stores', 'ancestor': {'displayName': '119a1e62-9e25-4871-8781-461cca5d6bb4_9601'}},
                 {'displayName': 'Novela negra'}]
        record = ca.to_record({'item': item(nodes=nodes)}, '2026-11-06')
        self.assertEqual(record['materias'], ['Misterio', 'Narrativa contemporánea'])  # mismo nivel: orden fijo
        self.assertEqual(record['palabras_clave'], ['Ficción literaria', 'Novela negra'])

    def test_ambiguous_node_is_resolved_by_its_branch_and_release_date_fills_the_gap(self):
        nodes = [{'displayName': 'Paranormal', 'contextFreeName': 'Novelas románticas y paranormales para jóvenes',
                  'ancestor': {'displayName': 'Novelas románticas',
                               'ancestor': {'displayName': 'Juvenil', 'contextFreeName': 'Libros juveniles',
                                            'ancestor': {'displayName': 'Categorías'}}}}]
        entry = {'item': item(nodes=nodes)}
        info = entry['item']['itemInfo']
        del info['contentInfo']['publicationDate']
        info['productInfo'] = {'releaseDate': {'displayValue': '2027-08-31T00:00:01Z'}}
        record = ca.to_record(entry, '2026-11-06')
        self.assertEqual(record['materias'], ['Romance', 'Novela juvenil'])
        self.assertEqual(record['fecha_publicacion_edicion'], '2027-08-31')

    def test_all_caps_title_and_author_get_spanish_casing(self):
        proper = ca.proper_words({'libros': [{'titulo': 'Poemas de Federico García Lorca', 'autores': ['Ana Dios']},
                                             {'titulo': 'Cien años de soledad', 'autores': []}]})
        self.assertEqual(ca.tidy_title('AGUSTÍN PENÓN Y FEDERICO GARCÍA LORCA', proper),
                         'Agustín penón y Federico García Lorca')
        self.assertEqual(ca.tidy_title('MUNDO EN MI MALETA, EL'), 'El mundo en mi maleta')
        self.assertEqual(ca.tidy_title('IA Y TEOLOGÍA: UNA RELACIÓN. TOMO II'), 'IA y teología: Una relación. Tomo II')
        self.assertEqual(ca.tidy_title('Cien años de soledad'), 'Cien años de soledad')
        record = ca.to_record({'item': item(title='LA CASA, EL FARO', authors=(('CYMET, ELI', 'Autor'),))}, '2026-11-06')
        self.assertEqual((record['titulo'], record['autores']), ('La casa, el faro', ['Eli Cymet']))

    def test_person_flips_surname_first_but_not_pairs(self):
        self.assertEqual(ca.person('García Márquez, Gabriel'), 'Gabriel García Márquez')
        self.assertEqual(ca.person('Ana y Luis, varios'), 'Ana y Luis, varios')
        self.assertEqual(ca.person('Juan Pérez, Jr.'), 'Juan Pérez, Jr.')
        self.assertEqual([ca.person(n) for n in ('AA.VV.', 'VVAA', 'ANONIMO')], ['Varios autores'] * 2 + ['Anónimo'])
        self.assertEqual(ca.person('ROSA Mª MUÑOZ GÓMEZ'), 'Rosa Mª Muñoz Gómez')

    def test_review_fixes_subjects_acronyms_variants_audiobooks(self):
        nodes = [{'displayName': 'Novela histórica'}, {'displayName': 'Novela Historica'},
                 {'displayName': 'Libros en la escuela'}, {'displayName': 'Libros en inglés'}]
        record = ca.to_record({'item': item(nodes=nodes)}, '2026-11-06')
        self.assertEqual(record['materias'], ['Novela histórica'])  # taxonomía cerrada
        self.assertEqual(record['palabras_clave'], ['Novela histórica', 'Libros en la escuela'])
        proper = ca.proper_words({'libros': [{'titulo': 'Informe de la ONU sobre el clima', 'autores': []}]})
        self.assertEqual(ca.tidy_title('LA ONU Y EL MUNDO', proper), 'La ONU y el mundo')
        self.assertEqual(ca.spelling_variants('Editorial Planeta'), ['Planeta'])
        self.assertEqual(ca.spelling_variants('Plaza & Janés'), ['Plaza & Janes', 'Editorial Plaza & Janés'])
        with self.assertRaises(ca.Rejected):
            ca.to_record({'item': item(binding='Audiolibro')}, '2026-11-06')
        self.assertEqual(ca.to_record({'item': item(binding='Libro de cartón')}, '2026-11-06')['formato_edicion'],
                         'tapa-dura')


class Transformar(unittest.TestCase):
    def test_one_card_per_work_prefers_spanish_paperback_and_logs_known(self):
        known = isbn('978849999999')
        rows = [item('A1', isbn('978841111111'), binding='Versión Kindle'),
                item('A2', isbn('978841111112'), binding='Tapa blanda'),
                item('A2', isbn('978841111112')),  # repetido en otro nodo
                item('A3', known, title='Otra obra'),
                item('A4', isbn('978841111113'), lang='Inglés', title='English')]
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            (Path(tmp) / 'raw').mkdir()
            (Path(tmp) / 'raw' / 'd.jsonl').write_text(
                ''.join(json.dumps({'nodo': '1', 'ruta': [], 'item': r}) + '\n' for r in rows), encoding='utf-8')
            out = ca.transformar('d', {'libros': [{'isbn13': known, 'titulo': 'Nada', 'autores': ['X']}]})
        self.assertEqual(out['leidos'], 4)
        self.assertEqual(out['candidatos'], 1)
        motives = sorted(f['motivo'] for f in out['fallos'])
        self.assertEqual(motives, ['idioma: ingles', 'ya en el catálogo'])

    def test_internal_amazon_roots_and_regional_literatures_are_not_subjects(self):
        internal = {'displayName': 'Self Service', 'ancestor': {'displayName': 'Special Features Stores',
                                                                'ancestor': {'displayName': 'Arborist Merchandising Root'}}}
        # Mitología e informática siguen sin materia propia (revisión p12): las decide un nodo hermano.
        cases = {'Lingüística': ['Ensayo'], 'Literatura europea': [],
                 'Mitos, leyendas y sagas': [], 'Programación y desarrollo de software': []}
        for node, subjects in cases.items():
            with self.subTest(node):
                record = ca.to_record({'item': item(nodes=[internal, {'displayName': node}])}, '2026-11-06')
                self.assertEqual(record['materias'], subjects)

    def test_stapled_and_cloth_books_are_print_editions(self):
        for binding, fmt in (('Grapado', 'tapa-blanda'), ('Libro de tela', 'tapa-dura')):
            with self.subTest(binding):
                self.assertEqual(ca.to_record({'item': item(binding=binding)}, '2026-11-06')['formato_edicion'], fmt)

    def test_unmapped_node_goes_to_review_and_missing_node_is_retried(self):
        rows = [item('B1', isbn('978841111121'), title='Uno', nodes=[{'displayName': 'Nodo raro'}]),
                item('B2', isbn('978841111122'), title='Dos', nodes=[])]
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            (Path(tmp) / 'raw').mkdir()
            (Path(tmp) / 'raw' / '2026-11-06.jsonl').write_text(
                ''.join(json.dumps({'nodo': '1', 'ruta': [], 'item': r}) + '\n' for r in rows), encoding='utf-8')
            out = ca.transformar('2026-11-06', {'libros': []})
        motives = sorted(f['motivo'] for f in out['fallos'])
        self.assertEqual(motives, ['materia sin mapear', 'sin materia'])
        self.assertEqual(ca.summarize(out['fallos'])['nodos_sin_mapear'], {'Nodo raro': 1})
        self.assertTrue('sin materia'.startswith(ca.RETRYABLE))
        self.assertFalse(motives[0].startswith(ca.RETRYABLE))

    def test_same_asin_keeps_the_appearance_with_subjects(self):
        bare = item('B1', isbn('978841111121'), title='Uno', nodes=[])
        full = item('B1', isbn('978841111121'), title='Uno')
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            (Path(tmp) / 'raw').mkdir()
            (Path(tmp) / 'raw' / '2026-11-06.jsonl').write_text(
                ''.join(json.dumps({'nodo': '1', 'ruta': [], 'item': r}) + '\n' for r in (bare, full)), encoding='utf-8')
            out = ca.transformar('2026-11-06', {'libros': []})
        self.assertEqual([f['motivo'] for f in out['fallos']], [])
        self.assertEqual(out['leidos'], 1)


class FakeProvider:
    """Nodo raíz lleno (10 páginas de 10) que se parte en dos hijos con pocos resultados."""

    def __init__(self):
        self.calls = []

    def headers(self):
        return {}

    def post(self, url, body, headers):
        self.calls.append(url)
        if url == ca.NODES:
            return {'browseNodesResult': {'browseNodes': [{'children': [
                {'id': '11', 'displayName': 'Thriller'}, {'id': '12', 'displayName': 'Romántica'}]}]}}
        node, page = body['browseNodeId'], body['itemPage']
        n = 10 if node == ca.BOOKS_NODE else 3
        return {'searchResult': {'items': [{'asin': f'{node}-{page}-{i}'} for i in range(n)]}}


class Sellos(unittest.TestCase):
    def test_walks_publishers_until_old_books_and_learns_new_imprints(self):
        class Brands:
            def __init__(self):
                self.calls = []

            def headers(self):
                return {}

            def post(self, url, body, headers):
                self.calls.append((body['brand'], body['itemPage']))
                if body['brand'] == 'Faro':  # página 1 nueva, página 2 ya vieja: no hay página 3
                    day = '2026-11-01' if body['itemPage'] == 1 else '2025-01-01'
                    rows = [item(f'F{body["itemPage"]}{i}', isbn(f'97884{body["itemPage"]}{i:06d}'), date=day,
                                 publisher='Faro Infantil' if i else 'Sello Nuevo') for i in range(10)]
                else:
                    rows = [item('E1', isbn('978014000001'), lang='Inglés', publisher='Penguin UK')]
                return {'searchResult': {'items': rows}}

        prov = Brands()
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            out = ca.por_sellos(prov, 'tag-21', '2026-11-06', names=['Editorial Faro', 'Otra'])
            learned = json.loads((Path(tmp) / 'sellos.json').read_text(encoding='utf-8'))
        # Los estériles prueban una vez la escritura con «Editorial» antes de reposar.
        self.assertEqual(prov.calls, [('Faro', 1), ('Faro', 2), ('Otra', 1), ('Sello Nuevo', 1), ('Editorial Otra', 1),
                                      ('Editorial Sello Nuevo', 1)])
        self.assertEqual(learned, {'sello nuevo': 'Sello Nuevo'})  # «Faro Infantil» ya lo cubre «Faro»
        self.assertEqual((out['sellos_leidos'], out['sellos_nuevos'], out['sellos_pendientes']), (5, 1, 0))

    def test_page_without_spanish_books_stops_the_publisher_and_errors_requeue_once(self):
        class Mixed:
            def __init__(self):
                self.calls = []

            def headers(self):
                return {}

            def post(self, url, body, headers):
                self.calls.append((body['brand'], body['itemPage']))
                if body['brand'] == 'Roto':
                    raise RuntimeError('Amazon Creators HTTP 500')
                return {'searchResult': {'items': [item(f'E{i}', isbn(f'97802{i:07d}'), lang='Inglés', date='2027-08-01')
                                                   for i in range(10)]}}

        prov = Mixed()
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            out = ca.por_sellos(prov, 'tag-21', '2026-11-06', names=['Minotauro', 'Roto'])
        self.assertEqual(prov.calls, [('Minotauro', 1), ('Roto', 1), ('Editorial Minotauro', 1), ('Roto', 1)])
        self.assertEqual((out['sellos_leidos'], out['errores']), (4, 2))

    def test_sterile_publisher_rests_and_is_asked_again_after_the_rest(self):
        class English(FakeProvider):
            def __init__(self):
                self.calls = []

            def post(self, url, body, headers):
                self.calls.append(body['brand'])
                return {'searchResult': {'items': [item('E1', isbn('9780200000001'), lang='Inglés', date='2026-11-01')]}}

        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            prov = English()
            ca.por_sellos(prov, 'tag-21', '2026-11-06', names=['Minotauro'])
            out = ca.por_sellos(prov, 'tag-21', '2026-11-07', names=['Minotauro'])
            self.assertEqual((prov.calls, out['sellos_saltados']), (['Minotauro', 'Editorial Minotauro'], 1))
            ca.por_sellos(prov, 'tag-21', '2026-11-28', names=['Minotauro'])
            self.assertEqual(prov.calls[2:], ['Minotauro', 'Editorial Minotauro'])

    def test_sterile_spelling_tries_the_unaccented_one_and_remembers_it(self):
        class Accent(FakeProvider):
            def __init__(self):
                self.calls = []

            def post(self, url, body, headers):
                self.calls.append(body['brand'])
                if body['brand'] == 'Plaza & Janes':
                    return {'searchResult': {'items': [item('P1', isbn('978840100000'), date='2026-11-01', publisher='PLAZA & JANES')]}}
                return {'searchResult': {'items': [item('K1', '0000000000000', date='2026-11-01', publisher='Plaza & Janés')]}}  # solo Kindle

        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            prov = Accent()
            out = ca.por_sellos(prov, 'tag-21', '2026-11-06', names=['Plaza & Janés'])
            self.assertEqual(prov.calls, ['Plaza & Janés', 'Plaza & Janes'])
            self.assertEqual(out['libros_es'], 2)
            memory = json.loads((Path(tmp) / 'rendimiento-sellos.json').read_text(encoding='utf-8'))
            self.assertEqual(memory['plaza janes']['consulta'], 'Plaza & Janes')
            ca.por_sellos(prov, 'tag-21', '2026-11-07', names=['Plaza & Janés'])
            self.assertEqual(prov.calls[2:], ['Plaza & Janes'])  # al día siguiente, directo a la buena


class Priorizar(unittest.TestCase):
    def test_publisher_legal_form_and_prefix_are_stripped_before_matching(self):
        clean = lambda n: ca.PREFIX.sub('', ca.LEGAL_FORM.sub('', n).strip(' ,'))
        self.assertEqual(clean('Norma Editorial, S.a.'), 'Norma Editorial')
        self.assertEqual(clean('Tusquets Editores S.a.'), 'Tusquets Editores')
        self.assertEqual(clean('Editorial Minuscula, S.l.u.'), 'Minuscula')
        self.assertEqual(clean('Ediciones B, SA'), 'Ediciones B')
        self.assertEqual(clean('La Galera, SAU'), 'La Galera')
        self.assertEqual(clean('Penguin Random House Grupo Editorial S.a.s'), 'Penguin Random House Grupo Editorial')
        self.assertEqual(clean('Salamandra'), 'Salamandra')
        self.assertEqual(clean('Ediciones SM'), 'Ediciones SM')

    def test_composite_directory_names_are_asked_one_imprint_at_a_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK, root = Path(tmp), ca.ROOT
            ca.ROOT = Path(tmp)
            (Path(tmp) / 'data').mkdir()
            (Path(tmp) / 'data' / 'editoriales.json').write_text(json.dumps({'publishers': [
                {'name': 'Grupo Almuzara — Almuzara/Berenice'}, {'name': 'Pie de Mosca / MilMadres'},
                {'name': 'Sexto Piso'}, {'name': 'almuzara'}, {'name': 'Sexto Piso / Berenice'}]}), encoding='utf-8')
            try:
                names = ca.seller_names()
            finally:
                ca.ROOT = root
        self.assertEqual(names, ['Grupo Almuzara', 'Almuzara', 'Berenice', 'Pie de Mosca', 'MilMadres', 'Sexto Piso'])

    def test_sales_rank_ignores_booleans_and_reads_digit_strings(self):
        rank = lambda r: ca.sales_rank({'item': {'browseNodeInfo': {'websiteSalesRank': {'salesRank': r}}}})
        self.assertEqual([rank(True), rank('12'), rank(0), rank(-3), rank(None), rank(7)],
                         [float('inf'), 12, float('inf'), float('inf'), float('inf'), 7])

    def test_branch_order_does_not_change_subjects(self):
        juvenil = {'displayName': 'Juvenil', 'contextFreeName': 'Libros juveniles'}
        branches = [{'displayName': 'Thriller', 'ancestor': {'displayName': 'Novela negra'}},
                    {'displayName': 'Paranormal', 'contextFreeName': 'Novelas románticas y paranormales para jóvenes',
                     'ancestor': juvenil}, {'displayName': 'Sin ancestro'}]
        first = ca.node_subjects({'browseNodeInfo': {'browseNodes': branches}})
        self.assertEqual(first, ca.node_subjects({'browseNodeInfo': {'browseNodes': branches[::-1]}}))
        self.assertEqual(len(first), len(set(first)))

    def test_new_and_upcoming_first_then_backlist(self):
        rows = [{'isbn13': d, 'fecha_publicacion_edicion': d} for d in
                ('2019-05-01', '2026-10-01', '2027-02-01', '2028-06-01', '2026-11-20')]
        chosen, deferred = ca.priorizar(rows, '2026-11-06', 4)
        self.assertEqual([r['isbn13'] for r in chosen], ['2027-02-01', '2026-11-20', '2026-10-01', '2028-06-01'])
        self.assertEqual(deferred, 1)

    def test_backlist_goes_by_amazon_sales_rank_after_new_releases(self):
        ranked = lambda d, r: {'isbn13': d, 'fecha_publicacion_edicion': d,
                               'item': {'browseNodeInfo': {'websiteSalesRank': {'salesRank': r}}} if r else {}}
        rows = [ranked('2019-05-01', 900), ranked('2015-01-01', 12), ranked('2020-01-01', None), ranked('2026-11-01', 50000)]
        chosen, _ = ca.priorizar(rows, '2026-11-06', 4)
        self.assertEqual([r['isbn13'] for r in chosen], ['2026-11-01', '2015-01-01', '2019-05-01', '2020-01-01'])


class Semillas(unittest.TestCase):
    def test_sitemap_seeds_only_new_entries_and_are_asked_ten_per_search(self):
        from reading_ttl_source import SITEMAP_INDEX
        books = [isbn('978841111%03d' % n) for n in range(12)]
        pages = {SITEMAP_INDEX: '<sitemapindex><loc>https://www.todostuslibros.com/sitemap/1.xml</loc></sitemapindex>',
                 'https://www.todostuslibros.com/sitemap/1.xml': ''.join(
                     f'<loc>https://www.todostuslibros.com/libros/x_{b}</loc>' for b in books[:11])}

        class Prov(FakeProvider):
            def post(self, url, body, headers):
                self.calls.append(body['keywords'])
                return {'searchResult': {'items': [item('A' + b[-9:], b) for b in body['keywords'].split('|')[:3]]}}

        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            self.assertEqual(ca.semillas_ttl(pages.get, '2026-11-06', {books[0]}), 10)  # el del catálogo no
            prov = Prov()
            with (Path(tmp) / 'raw.jsonl').open('w', encoding='utf-8') as out:
                res = ca.por_isbn(prov, 'tag', '2026-11-06', out, 5)
            self.assertEqual(res, {'peticiones': 1, 'debidas': 10, 'encontradas': 3, 'ajenos': 0,
                                   'lotes_fallidos': 0, 'en_cola': 7})
            self.assertEqual(len(prov.calls[0].split('|')), 10)
            state = json.loads(ca.seeds_path().read_text(encoding='utf-8'))
            self.assertTrue(all(r['siguiente'] == '2026-11-07' for r in state['cola'].values()))
            # Al día siguiente el sitemap trae una ficha más: solo entra esa.
            pages['https://www.todostuslibros.com/sitemap/1.xml'] += f'<loc>https://www.todostuslibros.com/libros/x_{books[11]}</loc>'
            self.assertEqual(ca.semillas_ttl(pages.get, '2026-11-07', set()), 1)


    SITEMAP = 'https://www.todostuslibros.com/sitemap/1.xml'

    def pages(self, books):
        from reading_ttl_source import SITEMAP_INDEX
        return {SITEMAP_INDEX: f'<sitemapindex><loc>{self.SITEMAP}</loc></sitemapindex>',
                self.SITEMAP: ''.join(f'<loc>https://www.todostuslibros.com/libros/x_{b}</loc>' for b in books)}

    def test_reordered_or_rewritten_sitemap_only_adds_unseen_and_never_discarded(self):
        books = [isbn('978841111%03d' % n) for n in range(6)]
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            self.assertEqual(ca.semillas_ttl(self.pages(books[:3]).get, '2026-11-06', set()), 3)
            state = json.loads(ca.seeds_path().read_text(encoding='utf-8'))
            state['cola'].pop(books[0])  # encontrado: ya no está en la cola
            ca.write_json(ca.seeds_path(), state)
            ca.discarded_path().write_text(json.dumps({'isbn13': books[4], 'motivo': 'x'}) + '\n', encoding='utf-8')
            # Misma longitud, otro orden y una ficha sustituida: entra solo la nueva.
            rewritten = [books[3], books[2], books[1], books[0], books[4]]
            self.assertEqual(ca.semillas_ttl(self.pages(rewritten).get, '2026-11-07', set()), 1)
            self.assertIn(books[3], json.loads(ca.seeds_path().read_text(encoding='utf-8'))['cola'])

    def test_other_editions_do_not_count_as_found(self):
        wanted, other = isbn('978841111200'), isbn('978841111201')

        class Prov(FakeProvider):
            def post(self, url, body, headers):
                return {'searchResult': {'items': [item('B9', other)]}}

        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            ca.semillas_ttl(self.pages([wanted]).get, '2026-11-06', set())
            raw = Path(tmp) / 'raw.jsonl'
            with raw.open('w', encoding='utf-8') as out:
                res = ca.por_isbn(Prov(), 'tag', '2026-11-06', out, 5)
            self.assertEqual((res['encontradas'], res['ajenos'], res['en_cola']), (0, 1, 1))
            self.assertEqual(raw.read_text(encoding='utf-8'), '')

    def test_failing_batch_is_split_and_the_bad_isbn_finally_discarded(self):
        good, bad = [isbn('978841111300'), isbn('978841111301')], isbn('978841111302')

        class Prov(FakeProvider):
            def post(self, url, body, headers):
                self.calls.append(body['keywords'])
                if bad in body['keywords']:
                    raise RuntimeError('HTTP 500')
                return {'searchResult': {'items': [item('A' + b[-9:], b) for b in body['keywords'].split('|')]}}

        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            ca.semillas_ttl(self.pages(good + [bad]).get, '2026-11-01', set())
            prov = Prov()
            with (Path(tmp) / 'raw.jsonl').open('w', encoding='utf-8') as out:
                for day in ('2026-11-01', '2026-11-02', '2026-11-03', '2026-11-04'):
                    res = ca.por_isbn(prov, 'tag', day, out, 10)
            self.assertEqual(len(prov.calls[0].split('|')), 3)  # dos fallos juntos, después sueltos
            self.assertEqual(len(prov.calls), 6)
            self.assertTrue(all('|' not in call for call in prov.calls[2:]))
            self.assertEqual(res['en_cola'], 0)
            log = [json.loads(line) for line in ca.discarded_path().read_text(encoding='utf-8').splitlines()]
            self.assertEqual([(r['isbn13'], r['motivo'][:15]) for r in log], [(bad, 'error de Amazon')])


class Enlaces(unittest.TestCase):
    def test_linkless_catalogue_book_is_queued_by_isbn10_and_its_item_kept_for_aplicar(self):
        linkless, linked = '9788408326861', isbn('978849999999')
        catalogue = {'libros': [
            {'id': 'a', 'estado': 'publicado', 'isbn13': linkless, 'titulo': 'Sin enlace', 'autores': ['X']},
            {'id': 'b', 'estado': 'publicado', 'isbn13': linked, 'titulo': 'Con enlace', 'autores': ['Y'],
             'formatos_compra': [{'formato': 'tapa-blanda'}]},
            {'id': 'c', 'estado': 'publicado', 'isbn13': '9791388042324', 'titulo': 'Sin ISBN-10', 'autores': ['Z']}]}
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            report = ca.revisar('d', catalogue)
            self.assertEqual(report['enlaces_pedidos'], 1)
            self.assertEqual(list(json.loads((Path(tmp) / 'pendientes.json').read_text(encoding='utf-8'))), ['8408326864'])
            (Path(tmp) / 'raw').mkdir()
            (Path(tmp) / 'raw' / 'd.jsonl').write_text(json.dumps(
                {'nodo': 'pendiente', 'ruta': [], 'item': item('8408326864', linkless)}) + chr(10), encoding='utf-8')
            out = ca.transformar('d', catalogue)
            kept = json.loads(ca.enlaces_path('d').read_text(encoding='utf-8'))
            pending = json.loads((Path(tmp) / 'pendientes.json').read_text(encoding='utf-8'))
        self.assertEqual(out['enlaces'], 1)
        self.assertEqual(list(kept), [linkless])
        self.assertEqual(pending, {})  # llegó: sale de la cola


class Descargar(unittest.TestCase):
    def test_full_node_is_split_into_children_and_checkpointed(self):
        prov = FakeProvider()
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            out = ca.descargar(prov, 'tag-21', 'd', max_requests=100, max_depth=1)
            lines = (Path(tmp) / 'raw' / 'd.jsonl').read_text(encoding='utf-8').splitlines()
            state = json.loads((Path(tmp) / 'raw' / 'd.estado.json').read_text(encoding='utf-8'))
        self.assertEqual(out['peticiones'], 10 + 1 + 1 + 1)  # raíz, hijos, un pase por hijo
        self.assertEqual(len(lines), 100 + 3 + 3)
        self.assertEqual(json.loads(lines[-1])['ruta'], ['Libros', 'Romántica'])
        self.assertEqual(state['pendientes'], [])

    def test_budget_cut_resumes_without_losing_the_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            first = ca.descargar(FakeProvider(), 'tag-21', 'd', max_requests=5, max_depth=1)
            self.assertEqual(first['nodos_pendientes'], 1)
            second = ca.descargar(FakeProvider(), 'tag-21', 'd', max_requests=100, max_depth=1)
            self.assertEqual(second['nodos_pendientes'], 0)


class Pendientes(unittest.TestCase):
    def test_retryable_gap_is_rescheduled_with_backoff_and_cleared_when_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            gap = [{'asin': 'A1', 'motivo': 'sin editorial'}, {'asin': 'A2', 'motivo': 'idioma: ingles'}]
            first = ca.update_pending('2026-11-06', gap, set())
            self.assertEqual(list(first), ['A1'])  # el idioma no se arregla esperando
            self.assertEqual(first['A1']['siguiente'], '2026-11-07')
            again = ca.update_pending('2026-11-07', gap[:1], set())
            self.assertEqual(again['A1']['intentos'], 2)
            self.assertEqual(again['A1']['siguiente'], '2026-11-09')
            self.assertEqual(ca.update_pending('2026-11-09', [], {'A1'}), {})

    def test_download_asks_due_pending_items_first_in_batches_of_ten(self):
        class Items(FakeProvider):
            def post(self, url, body, headers):
                if url == ca.ITEMS:
                    self.calls.append(url)
                    return {'itemsResult': {'items': [{'asin': a} for a in body['itemIds']]}}
                return super().post(url, body, headers)

        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            due = {f'P{i:02}': {'siguiente': '2026-11-06'} for i in range(12)} | {'LATER': {'siguiente': '2026-12-01'}}
            ca.write_json(ca.pending_path(), due)
            prov = Items()
            out = ca.descargar(prov, 'tag-21', '2026-11-06', max_requests=100, max_depth=0)
            lines = [json.loads(x) for x in (Path(tmp) / 'raw' / '2026-11-06.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual(prov.calls[:2], [ca.ITEMS, ca.ITEMS])
        self.assertEqual(out['reintentos'], 12)
        self.assertEqual(sum(1 for x in lines if x['nodo'] == 'pendiente'), 12)


    def test_missing_items_advance_their_schedule_and_are_discarded_after_the_last_try(self):
        class Gone(FakeProvider):
            def post(self, url, body, headers):
                self.calls.append(url)
                return {'itemsResult': {'items': []}}

        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            ca.write_json(ca.pending_path(), {'X1': {'primera': '2026-10-01', 'intentos': 6, 'siguiente': '2026-11-06'},
                                              'X2': {'primera': '2026-11-05', 'intentos': 1, 'siguiente': '2026-11-06'}})
            ca.descargar(Gone(), 'tag-21', '2026-11-06', max_requests=100, max_depth=0, root_node='R')
            pending = ca.read_json(ca.pending_path())
            gone = [json.loads(x) for x in ca.discarded_path().read_text(encoding='utf-8').splitlines()]
        self.assertEqual(pending['X2']['siguiente'], '2026-11-08')
        self.assertNotIn('X1', pending)
        self.assertEqual([g['asin'] for g in gone], ['X1'])


class Revisar(unittest.TestCase):
    def test_emptied_or_missing_books_are_a_regression_and_gaps_are_listed(self):
        def book(i, **extra):
            return {'id': i, 'estado': 'publicado', 'titulo': 'T' + i, 'autores': ['A'], 'editorial': 'E',
                    'isbn13': i, 'formatos_compra': [{'formato': 'tapa-blanda'}]} | extra
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            first = ca.revisar('2026-11-05', {'libros': [book('1'), book('2'), book('3')]})
            self.assertFalse(first['regresion'])
            self.assertIsNone(first['comparado_con'])
            again = ca.revisar('2026-11-06', {'libros': [book('1', formatos_compra=[]), book('2', titulo='Otro')]})
        self.assertEqual(again['comparado_con'], '2026-11-05')
        self.assertEqual(again['vaciados'], [{'id': '1', 'campo': 'formatos_compra'}])
        self.assertEqual(again['cambiados'], [{'id': '2', 'campo': 'titulo'}])
        self.assertEqual(again['desaparecidos'], ['3'])
        self.assertEqual(again['sin_enlace'], ['1'])
        self.assertTrue(again['regresion'])


class Client(unittest.TestCase):
    """Reintentos y token como en python-amazon-paapi, sin red."""

    def setUp(self):
        from unittest.mock import patch
        import reading_amazon_market as market
        self.market = market
        self.sleep = patch.object(market.time, 'sleep').start()
        self.addCleanup(patch.stopall)
        self.patch = patch

    def error(self, code, body=b'{}'):
        import io
        from urllib.error import HTTPError
        return HTTPError('https://creatorsapi.amazon/x', code, 'x', {}, io.BytesIO(body))

    def ok(self, data):
        import io
        return io.BytesIO(json.dumps(data).encode())

    def test_expired_token_is_renewed_once_and_the_request_repeated(self):
        client = self.market.CreatorsPrices('id', 'secret', 'tag-21')
        answers = [self.ok({'access_token': 'T1', 'expires_in': 3600}), self.error(401),
                   self.ok({'access_token': 'T2', 'expires_in': 3600}), self.ok({'searchResult': {}})]
        seen = []

        def fake(request, timeout):
            seen.append(request.get_header('Authorization'))
            answer = answers.pop(0)
            if isinstance(answer, Exception):
                raise answer
            return answer

        with self.patch.object(self.market, 'urlopen', side_effect=fake):
            self.assertEqual(client.post(ca.SEARCH, {}, client.headers()), {'searchResult': {}})
        self.assertEqual(seen, [None, 'Bearer T1', None, 'Bearer T2'])

    def test_token_is_renewed_before_it_expires(self):
        client = self.market.CreatorsPrices('id', 'secret', 'tag-21')
        tokens = [self.ok({'access_token': 'T1', 'expires_in': 3600}), self.ok({'access_token': 'T2', 'expires_in': 3600})]
        with self.patch.object(self.market, 'urlopen', side_effect=tokens):
            self.assertEqual(client.headers()['Authorization'], 'Bearer T1')
            self.assertEqual(client.headers()['Authorization'], 'Bearer T1')
            client.expires = 0
            self.assertEqual(client.headers()['Authorization'], 'Bearer T2')

    def test_server_errors_and_dropped_connections_are_retried(self):
        from urllib.error import URLError
        client = self.market.CreatorsPrices('id', 'secret', 'tag-21')
        with self.patch.object(self.market, 'urlopen',
                               side_effect=[self.error(503), URLError('reset'), self.ok({'searchResult': {}})]):
            self.assertEqual(client.post(ca.SEARCH, {}), {'searchResult': {}})
        with self.patch.object(self.market, 'urlopen', side_effect=[self.error(500)] * 4):
            with self.assertRaisesRegex(RuntimeError, '^Amazon Creators HTTP 500$'):
                client.post(ca.SEARCH, {})

    def test_not_found_is_an_empty_page_for_the_walk(self):
        client = self.market.CreatorsPrices('id', 'secret', 'tag-21')
        with self.patch.object(self.market, 'urlopen', side_effect=self.error(404)):
            with self.assertRaises(self.market.NotFound):
                client.post(ca.SEARCH, {})

        class Empty(FakeProvider):
            def post(self, url, body, headers):
                self.calls.append(url)
                raise self_market.NotFound('Amazon Creators HTTP 404')

        self_market = self.market
        with tempfile.TemporaryDirectory() as tmp:
            ca.WORK = Path(tmp)
            out = ca.descargar(Empty(), 'tag-21', 'd', max_requests=100, max_depth=1)
        self.assertEqual((out['peticiones'], out['nodos_leidos'], out['errores']), (1, 1, 0))


if __name__ == '__main__':
    unittest.main()
