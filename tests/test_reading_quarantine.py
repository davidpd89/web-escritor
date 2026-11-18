"""Cuarentena por libro: un dato malo aparta su libro y el resto del lote sigue validando."""
import copy
import json
import re
import shutil
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_quarantine as q  # noqa: E402

DATA = json.loads((ROOT / q.CATALOGUE).read_text(encoding='utf-8'))


def without(n):
    """Catálogo sin el libro n y ese libro con sus categorías: así el libro llega como nuevo en la carga."""
    data = copy.deepcopy(DATA)
    book = data['libros'].pop(n)
    cats = sorted(r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == book['id'])
    data['libro_categorias'] = [r for r in data['libro_categorias'] if r['libro_id'] != book['id']]
    return data, book, cats


class QuarantineTest(unittest.TestCase):
    def test_bad_new_book_leaves_the_batch(self):
        before, book, cats = without(0)
        data = copy.deepcopy(DATA)
        data['libros'][0]['autores'] = []
        clean, out = q.isolate(data, ROOT, before, today='2026-11-03')
        self.assertEqual([h['libro']['id'] for h in out], [book['id']])
        self.assertTrue(out[0]['motivo'].startswith(book['id']))
        self.assertEqual(out[0]['categorias'], cats)
        self.assertEqual(clean, before)

    def test_bad_update_keeps_the_published_version(self):
        data = copy.deepcopy(DATA)
        data['libros'][3]['descripcion_breve'] = 'corta'
        clean, out = q.isolate(data, ROOT, DATA)
        self.assertEqual(out[0]['libro']['descripcion_breve'], 'corta')
        self.assertEqual(clean, DATA)

    def test_good_books_are_untouched_and_retried(self):
        data, book, cats = without(1)
        held = [{'libro': book, 'categorias': cats, 'motivo': 'x', 'desde': '2026-10-01'}]
        clean, out = q.isolate(data, ROOT, data, held)
        self.assertEqual(out, [])
        self.assertIn(book, clean['libros'])
        self.assertEqual(q.isolate(DATA, ROOT, DATA), (DATA, []))

    def test_still_bad_held_book_keeps_its_date(self):
        data, book, cats = without(2)
        book['autores'] = []
        held = [{'libro': book, 'categorias': cats, 'motivo': 'x', 'desde': '2026-10-01'}]
        clean, out = q.isolate(data, ROOT, data, held, today='2026-11-03')
        self.assertEqual(clean, data)
        self.assertEqual(out[0]['desde'], '2026-10-01')

    def test_rule_errors_still_stop_the_batch(self):
        data = copy.deepcopy(DATA)
        data['categorias'][0]['tipo'] = 'inventado'
        with self.assertRaises(q.build.ValidationError):
            q.isolate(data, ROOT, DATA)
        broken = copy.deepcopy(DATA)
        broken['libros'][0]['descripcion_breve'] = 'corta'
        with self.assertRaises(q.build.ValidationError):  # publicado y sin cambios: no se despublica en silencio
            q.isolate(broken, ROOT, broken)

    def test_too_many_books_is_a_rule_problem(self):
        data = copy.deepcopy(DATA)
        for b in data['libros'][:q.MAX_BOOKS + 1]:
            b['descripcion_breve'] = 'corta'
        with self.assertRaises(q.build.ValidationError):
            q.isolate(data, ROOT, DATA)

    def test_duplicate_cover_blames_the_changed_book(self):
        # Ingesta 42588397174: el tomo que cambió tomó la portada de otro ya publicado; se apartaba al publicado
        # (sin cambios) y la carga entera fallaba.
        data = copy.deepcopy(DATA)
        for key in ('portada_local', 'portada_ancho', 'portada_alto'):
            data['libros'][0][key] = data['libros'][5][key]
        clean, out = q.isolate(data, ROOT, DATA)
        self.assertEqual([h['libro']['id'] for h in out], [DATA['libros'][0]['id']])
        self.assertIn('igual que', out[0]['motivo'])
        self.assertEqual(clean, DATA)

    def test_book_flagged_by_a_data_contract_leaves_the_batch(self):
        # 10/11: una sinopsis gritada falló en check-reading-data, fuera de la validación, y tumbó la carga entera.
        before, book, cats = without(0)
        clean, out = q.isolate(copy.deepcopy(DATA), ROOT, before, flagged={book['id']: 'contrato de datos x: sinopsis gritada'})
        self.assertEqual([h['libro']['id'] for h in out], [book['id']])
        self.assertIn('sinopsis gritada', out[0]['motivo'])
        self.assertEqual(clean, before)

    def test_flagged_published_book_without_changes_is_retired_not_a_rule_problem(self):
        # 16/11: isbn-9791388205675 llevaba semanas publicado con un solo módulo (su afinidad con "Historia" ronda
        # el umbral y cruza de un día para otro según crece el catálogo) y, al añadirse ese contrato a la QA de la
        # PR (#1387), la cuarentena no tenía a qué revertirlo (ya era su versión buena) y paraba el lote entero
        # cada noche. Revertir sería un no-op: el libro sale de publicación hasta que se corrija el dato.
        book_id = DATA['libros'][0]['id']
        clean, out = q.isolate(copy.deepcopy(DATA), ROOT, DATA, flagged={book_id: 'contrato de datos x: un solo módulo'})
        self.assertEqual([h['libro']['id'] for h in out], [book_id])
        retired = next(b for b in clean['libros'] if b['id'] == book_id)
        self.assertEqual(retired['estado'], 'borrador')
        self.assertNotIn(book_id, {b['id'] for b in clean['libros'] if b['estado'] == 'publicado'})

    def test_flagged_published_book_without_changes_keeps_its_price_history_in_quarantine(self):
        data = copy.deepcopy(DATA)
        book_id = next(b['id'] for b in data['libros'] if b.get('formatos_compra'))
        clean, out = q.isolate(data, ROOT, DATA, flagged={book_id: 'x'})
        priced = next(b for b in DATA['libros'] if b['id'] == book_id)
        self.assertEqual(out[0]['libro']['formatos_compra'], priced['formatos_compra'])
        retired = next(b for b in clean['libros'] if b['id'] == book_id)
        self.assertFalse(any('precio_centimos' in o for o in retired['formatos_compra']))

    def test_flagged_books_only_when_every_failure_names_a_book(self):
        book_id = DATA['libros'][0]['id']
        failures = [{'test': 'test_reading_editorial_shouting.PublishedCatalogueTests.test_no_meta',
                     'texto': f"Traceback...\nAssertionError: <re.Match> is not None : ('{book_id}', 'FILOSOFÍA&CO ESPECIAL')"}]
        named = q.flagged_books(failures, DATA)
        self.assertEqual(list(named), [book_id])
        self.assertIn('test_no_meta', named[book_id])
        self.assertIsNone(q.flagged_books(failures + [{'test': 't.x', 'texto': 'ImportError: no module'}], DATA))

    def test_flagged_books_also_by_isbn(self):
        """El 16/11 el contrato de títulos anónimos citaba «Título · ISBN13» sin id y la carga paró entera."""
        book = [b for b in DATA['libros'] if b.get('isbn13')][0]
        failures = [{'test': 't.test_titles', 'texto': f"AssertionError: 3 not less than or equal to 2 : ['Algo · {book['isbn13']}']"}]
        self.assertEqual(list(q.flagged_books(failures, DATA)), [book['id']])

    def test_each_named_book_gets_its_own_line_as_reason(self):
        """Un contrato que nombra varios libros (uno por línea) no da a todos el motivo del último (16/11, O4.1)."""
        a, b = DATA['libros'][0]['id'], DATA['libros'][1]['id']
        failures = [{'test': 't.test_schema', 'texto': f"AssertionError: ...\n{a}: slug: no cumple\n{b}: autores: lista vacía"}]
        named = q.flagged_books(failures, DATA)
        self.assertIn('slug', named[a])
        self.assertIn('autores', named[b])

    def test_count_contract_blames_the_changed_books_not_the_published_ones(self):
        """Un contrato de recuento nombra publicados intactos y un alta: sale el alta, los publicados siguen."""
        data = copy.deepcopy(DATA)
        new = copy.deepcopy(data['libros'][0])
        new['id'] = 'alta-de-prueba-cuenta'
        data['libros'].append(new)
        stale = [b['id'] for b in DATA['libros'][1:3]]
        clean, out = q.isolate(data, ROOT, DATA, flagged={i: 'recuento' for i in stale + [new['id']]})
        self.assertEqual([h['libro']['id'] for h in out], [new['id']])
        self.assertEqual(clean['libros'], DATA['libros'])

    def test_data_check_writes_its_failures_for_the_intake(self):
        """check-reading-data --fallos deja cada fallo con su texto: de ahí la carga saca los libros a apartar."""
        import importlib.util
        from unittest import mock
        spec = importlib.util.spec_from_file_location('check_reading_data', ROOT / 'scripts/check-reading-data.py')
        check = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(check)
        book_id = DATA['libros'][0]['id']
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'contrato_falso.py').write_text('\n'.join([
                'import unittest',
                'class T(unittest.TestCase):',
                '    def test_x(self):',
                f'        self.fail("({book_id!r}, TEXTO GRITADO)")',
                '']), encoding='utf-8')
            out = Path(tmp) / 'fallos.json'
            sys.path.insert(0, tmp)
            try:
                with mock.patch.object(check, 'contracts', lambda: ['contrato_falso']), \
                        mock.patch.object(sys, 'argv', ['check', '--fallos', str(out)]):
                    self.assertEqual(check.main(), 1)
            finally:
                sys.path.remove(tmp)
            failures = json.loads(out.read_text(encoding='utf-8'))
        self.assertEqual(list(q.flagged_books(failures, DATA)), [book_id])

    def test_restore_cover_brings_back_the_published_file(self):
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cover = root / 'assets/reading-covers/isbn-1.webp'
            cover.parent.mkdir(parents=True)
            cover.write_bytes(b'publicada')
            for cmd in (['init', '-q'], ['add', '.'], ['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'x']):
                subprocess.run(['git', *cmd], cwd=root, check=True)
            cover.write_bytes(b'nueva de amazon')
            q.restore_cover(root, {'portada_local': '/assets/reading-covers/isbn-1.webp'})
            self.assertEqual(cover.read_bytes(), b'publicada')

    def test_owner_is_a_known_book_id(self):
        first = DATA['libros'][0]['id']
        self.assertEqual(q.owner(q.build.ValidationError('x', libro=first), DATA), first)
        self.assertIsNone(q.owner(q.build.ValidationError('x', libro='no-existe'), DATA))
        self.assertIsNone(q.owner(q.build.ValidationError(f'{first}: texto con id pero sin dueño'), DATA))


    def test_100_books_20_bad_the_80_good_continue(self):
        """Llegan 100 libros, 20 traen datos rotos: los 80 válidos siguen y los 20 quedan trazados."""
        incoming = DATA['libros'][:100]
        ids = {b['id'] for b in incoming}
        before = copy.deepcopy(DATA)
        before['libros'] = [b for b in before['libros'] if b['id'] not in ids]
        before['libro_categorias'] = [r for r in before['libro_categorias'] if r['libro_id'] not in ids]
        data = copy.deepcopy(DATA)
        bad = {b['id'] for b in data['libros'][:100:5]}
        for b in data['libros'][:100:5]:
            b['autores'] = []
        clean, out = q.isolate(data, ROOT, before, today='2026-11-04')
        self.assertEqual({h['libro']['id'] for h in out}, bad)
        self.assertEqual(len(out), 20)
        published = {b['id'] for b in clean['libros']}
        self.assertEqual(len(ids & published), 80)
        self.assertFalse(bad & published)
        for h in out:
            self.assertEqual(h['isbn'], h['libro'].get('isbn13', ''))
            self.assertEqual(h['intentos'], 1)
            self.assertTrue(h['causa'] and h['libro']['id'] not in h['causa'])
        self.assertEqual(len({h['causa'] for h in out}), 1, 'los 20 comparten causa y se agrupan')

    def test_more_than_half_the_batch_is_global(self):
        incoming = DATA['libros'][:30]
        ids = {b['id'] for b in incoming}
        before = copy.deepcopy(DATA)
        before['libros'] = [b for b in before['libros'] if b['id'] not in ids]
        before['libro_categorias'] = [r for r in before['libro_categorias'] if r['libro_id'] not in ids]
        data = copy.deepcopy(DATA)
        for b in data['libros'][:16]:
            b['autores'] = []
        with self.assertRaisesRegex(q.build.ValidationError, 'Error global'):
            q.isolate(data, ROOT, before)

    def test_attempts_accumulate_and_pending_recover_after_fix(self):
        data, book, cats = without(4)
        broken = copy.deepcopy(book)
        broken['autores'] = []
        held = [{'libro': broken, 'categorias': cats, 'motivo': 'x', 'desde': '2026-10-01', 'intentos': 2}]
        _, out = q.isolate(data, ROOT, data, held, today='2026-11-04')
        self.assertEqual((out[0]['intentos'], out[0]['desde']), (3, '2026-10-01'))
        # La regla (o el dato de origen) se corrige: el pendiente vuelve al catálogo sin tocarlo a mano.
        held[0]['libro'] = book
        clean, out = q.isolate(data, ROOT, data, held)
        self.assertEqual(out, [])
        self.assertIn(book, clean['libros'])

    def test_cause_is_groupable(self):
        self.assertEqual(q.cause('isbn-9788410427709: sello del catálogo inexistente'), 'sello del catálogo inexistente')
        self.assertEqual(q.cause('lib-0042.mes: fecha inválida 13'), 'mes: fecha inválida N')
        self.assertEqual(q.cause('AttributeError: x'), 'AttributeError: x')

    def test_missing_catalogue_publisher_is_repaired_for_every_book(self):
        """Regresión #1152: el sello perdido se registra desde la ficha oficial y el libro deja de estar apartado."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            for name in ('reading-publishers.json', 'editoriales.json', 'reading-intake-config.json'):
                shutil.copy(ROOT / 'data' / name, root / 'data' / name)
            store = json.loads((root / q.PUBLISHERS).read_text(encoding='utf-8'))
            store['editoriales'] = [p for p in store['editoriales'] if p['slug'] != 'neko-books']
            (root / q.PUBLISHERS).write_text(json.dumps(store, ensure_ascii=False), encoding='utf-8')
            books = [{'id': f'isbn-97884104277{i:02d}', 'editorial': 'Neko Books', 'editorial_catalogo_slug': 'neko-books',
                      'fuente_publicacion_url': f'https://www.planetadelibros.com/libro-x/{i}'} for i in range(3)]
            self.assertEqual(q.repair_catalogue_publishers(books, root, '2026-11-04'), 3)
            slugs = {p['slug'] for p in json.loads((root / q.PUBLISHERS).read_text(encoding='utf-8'))['editoriales']}
            self.assertIn('neko-books', slugs)
            self.assertEqual(q.repair_catalogue_publishers(books, root, '2026-11-04'), 0, 'idempotente')

    def test_carry_moves_every_file_the_intake_writes(self):
        """Regresión #1152: todo lo que la ingesta escribe en data/ viaja con el carry de una PR obsoleta."""
        intake = (ROOT / 'scripts/reading_intake_pipeline.py').read_text(encoding='utf-8')
        refresh = (ROOT / 'scripts/refresh-reading-catalogue.py').read_text(encoding='utf-8')
        written = set(re.findall(r"write_if_changed\(root / '(data/[^']+)'", intake))
        carried = set(re.findall(r"'([^']+)'", re.search(r'SOURCE_PATHS = \(([^)]*)\)', refresh)[1]))
        self.assertTrue(written)
        self.assertLessEqual(written, carried)


    def test_book_with_only_inactive_categories_is_named(self):
        data = copy.deepcopy(DATA)
        book = next(b for b in data['libros'] if b['estado'] == 'publicado')
        own = {r['categoria_id'] for r in data['libro_categorias'] if r['libro_id'] == book['id']}
        for c in data['categorias']:
            if c['id'] in own:
                c['activa'] = False
        with self.assertRaisesRegex(q.build.ValidationError, re.escape(book['id'] + ': sin categoría activa')):
            q.build.validate(data, ROOT)

    def test_source_text_without_accents_is_repaired_for_every_book(self):
        # sync 42444782344 / #1228: 38 avisos de check-copy-tildes en content-index-check por tres títulos.
        books = [{'titulo': 'Matteo. Edicion integral: 1', 'descripcion_breve': 'Matteo. Edicion integral: 1, de Gibrat.'},
                 {'titulo': 'La balada del norte 03 (nueva edicion)', 'sinopsis_breve': 'Novela historica y EDICION nueva.'},
                 {'titulo': "En mi Era Pistacho: Juliette's version"},
                 {'titulo': 'Las versiones de Frances Burney', 'fuente_publicacion_url': 'https://x.es/edicion-especial'}]
        self.assertEqual(q.repair_title_accents(books, ROOT, '2026-11-08'), 4)  # campos reparados
        self.assertEqual(books[0]['titulo'], 'Matteo. Edición integral: 1')
        self.assertEqual(books[0]['descripcion_breve'], 'Matteo. Edición integral: 1, de Gibrat.')
        self.assertEqual(books[1]['titulo'], 'La balada del norte 03 (nueva edición)')
        self.assertEqual(books[1]['sinopsis_breve'], 'Novela histórica y EDICIÓN nueva.')
        self.assertEqual(books[2]['titulo'], "En mi Era Pistacho: Juliette's version")  # inglés tras posesivo
        self.assertEqual(books[3]['titulo'], 'Las versiones de Frances Burney')  # plural y nombre propio
        self.assertEqual(q.repair_title_accents(books, ROOT, '2026-11-08'), 0)  # idempotente

    def test_checker_reads_entities_as_the_reader_does(self):
        page = '<p>En mi Era Pistacho: Juliette&#x27;s version</p><p>Nueva edicion</p>'
        pieces = [text for _, text, _ in q.tildes.html_visible_text(page)]
        self.assertEqual(pieces[0], "En mi Era Pistacho: Juliette's version")
        flagged = [w for t in pieces for w in q.tildes.WORD_RE.findall(t) if not q.tildes.is_technical_use(t, w.lower())]
        self.assertEqual(flagged, ['edicion'])


# Mutaciones que rompen un libro concreto (índice en DATA): cada una sale por una regla distinta del validador.
MUTACIONES = {
    'autores vacíos': (0, lambda b: b.update(autores=[])),
    'descripción corta': (1, lambda b: b.update(descripcion_breve='corta')),
    'título vacío': (2, lambda b: b.update(titulo='')),
    'fecha rota': (3, lambda b: b.update(fecha_publicacion='2026-13-45')),
    'campo desconocido': (4, lambda b: b.update(campo_inventado=1)),
}


def mutado(n, cambio):
    data, book, _ = without(n)
    roto = copy.deepcopy(DATA)
    cambio(roto['libros'][n])
    return data, roto, book


class FallosEstructuradosTest(unittest.TestCase):
    """R4-2 (D3/F5): la cuarentena aparta por el libro que trae el fallo como dato, nunca leyendo su texto."""

    def test_validate_nombra_el_libro_y_la_regla(self):
        for nombre, (n, cambio) in MUTACIONES.items():
            with self.subTest(nombre):
                _, roto, book = mutado(n, cambio)
                with self.assertRaises(q.build.ValidationError) as ctx:
                    q.build.validate(roto, ROOT)
                self.assertEqual(ctx.exception.libro, book['id'])
                self.assertTrue(ctx.exception.regla)
                self.assertNotIn(book['id'], ctx.exception.regla, 'la regla no lleva el libro: agrupa incidencias')

    def test_renombrar_el_mensaje_no_cambia_a_quien_se_aparta(self):
        """Propiedad: el texto del fallo puede citar otro libro (un título con el id de otro, un mensaje reescrito)
        o ninguno; el apartado es siempre el que trae el fallo."""
        real = q.build.validate
        otro = DATA['libros'][7]['id']
        for texto in (f'{otro}: mensaje reescrito', 'mensaje reescrito sin libro', f'Error en {otro}.campo: x'):
            for nombre, (n, cambio) in MUTACIONES.items():
                with self.subTest(texto=texto, regla=nombre):
                    antes, roto, book = mutado(n, cambio)

                    def reescrito(data, root, texto=texto):
                        try:
                            return real(data, root)
                        except q.build.ValidationError as exc:
                            exc.args = (texto,)
                            raise

                    with unittest.mock.patch.object(q.build, 'validate', reescrito):
                        clean, out = q.isolate(roto, ROOT, antes, today='2026-11-17')
                    self.assertEqual([h['libro']['id'] for h in out], [book['id']])
                    self.assertEqual(clean, antes)

    def test_portada_duplicada_trae_la_gemela_como_dato(self):
        data = copy.deepcopy(DATA)
        for key in ('portada_local', 'portada_ancho', 'portada_alto'):
            data['libros'][0][key] = data['libros'][5][key]
        with self.assertRaises(q.build.ValidationError) as ctx:
            q.build.validate(data, ROOT)
        self.assertEqual({ctx.exception.libro, ctx.exception.otro}, {DATA['libros'][0]['id'], DATA['libros'][5]['id']})

    def test_un_fichero_comun_roto_es_un_fallo_general_y_no_aparta_al_libro_en_curso(self):
        """Un `reading-publishers.json` inválido que salta al validar una ficha con `editorial_catalogo_slug` no se
        atribuye a esa ficha: apartarla ocultaría el error y el lote seguiría con el fichero roto."""
        with tempfile.TemporaryDirectory() as tmp:
            roto = Path(tmp) / 'reading-publishers.json'
            roto.write_text(json.dumps({'schema_version': 1, 'editoriales': [], 'extra': 1}), encoding='utf-8')
            with self.assertRaises(q.build.ValidationError) as ctx:
                q.build.load_publisher_records(roto)
            self.assertTrue(ctx.exception.general)
            with unittest.mock.patch.object(q.build, 'publisher_records', lambda root=None: q.build.load_publisher_records(roto)):
                with self.assertRaises(q.build.ValidationError) as ctx:
                    q.build.validate(copy.deepcopy(DATA), ROOT)
                self.assertIsNone(ctx.exception.libro)
                self.assertTrue(ctx.exception.general)
                with self.assertRaises(q.build.ValidationError):
                    q.isolate(copy.deepcopy(DATA), ROOT, DATA, today='2026-11-17')

    def test_la_cuarentena_no_lee_mensajes_con_regex(self):
        """Guarda: dentro de isolate no hay `re.` ni se busca el culpable en el texto del fallo."""
        import ast
        import inspect
        import textwrap
        arbol = ast.parse(textwrap.dedent(inspect.getsource(q.isolate)))
        usos = [n for n in ast.walk(arbol) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                and n.value.id == 're']
        llamadas = [n.func.id for n in ast.walk(arbol) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        self.assertEqual(usos, [])
        self.assertNotIn('culprit', llamadas)


class DuenoSiempreTest(unittest.TestCase):
    """R5-10 (hallazgos 15, 17, 18): todo fallo de una ficha o relación sale con dueño; solo el esquema global no."""

    def test_un_libro_con_id_invalido_se_aparta_sin_tumbar_el_lote(self):
        before, book, _ = without(0)
        data = copy.deepcopy(before)
        malo = copy.deepcopy(book)
        malo['id'] = 'Id Malo'
        data['libros'].append(malo)
        clean, out = q.isolate(data, ROOT, before, today='2026-11-16')
        self.assertEqual([h['libro']['id'] for h in out], ['Id Malo'])
        self.assertEqual(clean, before)

    def test_un_id_repetido_aparta_la_segunda_ficha(self):
        before, book, _ = without(0)
        data = copy.deepcopy(DATA)
        copia = copy.deepcopy(data['libros'][1])
        copia['slug'] = copia['slug'] + '-bis'
        data['libros'].append(copia)
        clean, out = q.isolate(data, ROOT, DATA, today='2026-11-16')
        self.assertEqual(clean, DATA)
        self.assertEqual(len(out), 1)

    def test_una_relacion_rota_se_quita_sin_tumbar_el_lote(self):
        data = copy.deepcopy(DATA)
        data['libro_categorias'].append({'libro_id': 'libro-que-no-existe', 'categoria_id': DATA['categorias'][0]['id']})
        clean, out = q.isolate(data, ROOT, DATA, today='2026-11-16')
        self.assertEqual((clean, out), (DATA, []))

    def test_una_relacion_a_una_categoria_inexistente_aparta_su_libro(self):
        before, book, _ = without(0)
        data = copy.deepcopy(DATA)
        data['libro_categorias'].append({'libro_id': book['id'], 'categoria_id': 'categoria-que-no-existe'})
        clean, out = q.isolate(data, ROOT, before, today='2026-11-16')
        self.assertEqual([h['libro']['id'] for h in out], [book['id']])
        self.assertEqual(clean, before)

    def test_mismo_isbn_aparta_el_que_cambio_aunque_sea_el_primero(self):
        # El fallo salta en la segunda ficha (sin cambios); la culpable es la primera, que tomó su ISBN.
        data = copy.deepcopy(DATA)
        for libro in data['libros'][:2]:
            libro.pop('amazon_busqueda_isbn', None)  # la búsqueda Amazon repite el ISBN y fallaría antes
        data['libros'][0]['isbn13'] = DATA['libros'][1]['isbn13']
        with self.assertRaises(q.build.ValidationError) as ctx:
            q.build.validate(copy.deepcopy(data), ROOT)
        self.assertEqual({ctx.exception.libro, ctx.exception.otro}, {DATA['libros'][0]['id'], DATA['libros'][1]['id']})
        antes = copy.deepcopy(DATA)
        antes['libros'][1].pop('amazon_busqueda_isbn', None)
        clean, out = q.isolate(data, ROOT, antes, today='2026-11-16')
        self.assertEqual([h['libro']['id'] for h in out], [DATA['libros'][0]['id']])
        self.assertEqual(clean['libros'][0], DATA['libros'][0])

    def test_unicidades_entre_dos_fichas_traen_la_otra(self):
        cambios = {
            'slug': lambda a, b: a.update(slug=b['slug']),
            'descripción': lambda a, b: a.update(descripcion_breve=b['descripcion_breve']),
            'obra': lambda a, b: a.update(titulo=b['titulo'], autores=list(b['autores'])),
        }
        for nombre, cambio in cambios.items():
            with self.subTest(nombre):
                data = copy.deepcopy(DATA)
                cambio(data['libros'][0], data['libros'][1])
                with self.assertRaises(q.build.ValidationError) as ctx:
                    q.build.validate(data, ROOT)
                self.assertEqual({ctx.exception.libro, ctx.exception.otro}, {DATA['libros'][0]['id'], DATA['libros'][1]['id']})

    def test_si_cambiaron_los_dos_se_apartan_los_dos(self):
        before = copy.deepcopy(DATA)
        ids = {DATA['libros'][0]['id'], DATA['libros'][1]['id']}
        before['libros'] = [b for b in before['libros'] if b['id'] not in ids]
        before['libro_categorias'] = [r for r in before['libro_categorias'] if r['libro_id'] not in ids]
        data = copy.deepcopy(DATA)
        data['libros'][0].pop('amazon_busqueda_isbn', None)
        data['libros'][0]['isbn13'] = DATA['libros'][1]['isbn13']
        clean, out = q.isolate(data, ROOT, before, today='2026-11-16')
        self.assertEqual({h['libro']['id'] for h in out}, ids)
        self.assertEqual(clean, before)

    def test_una_excepcion_al_recorrer_una_ficha_es_de_esa_ficha(self):
        before, book, _ = without(0)
        data = copy.deepcopy(DATA)
        data['libros'][0]['amazon_busqueda_isbn'] = 123  # urlparse revienta con un entero
        with self.assertRaises(q.build.ValidationError) as ctx:
            q.build.validate(copy.deepcopy(data), ROOT)
        self.assertEqual((ctx.exception.libro, ctx.exception.regla), (book['id'], 'excepcion'))
        clean, out = q.isolate(data, ROOT, before, today='2026-11-16')
        self.assertEqual([h['libro']['id'] for h in out], [book['id']])
        self.assertEqual(clean, before)

    def test_el_esquema_global_sigue_sin_dueno(self):
        data = copy.deepcopy(DATA)
        data['extra'] = 1
        with self.assertRaises(q.build.ValidationError) as ctx:
            q.build.validate(data, ROOT)
        self.assertEqual((ctx.exception.libro, ctx.exception.posicion, ctx.exception.relacion), (None, None, None))


if __name__ == '__main__':
    unittest.main()
