"""Orientación propia por ficha: el validador bloquea copia, valoraciones e invenciones y la ficha la pinta.

Usa datos y plantillas reales. No abre el navegador ni consulta ChatGPT.
"""
import copy
import os
import importlib.util
import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


texts = load('reading_texts_test', 'scripts/reading-texts.py')
builder = texts.catalogue


class ReadingTextsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
        texts.catalogue.index_categories(cls.data)  # recorren todo el catálogo real: sin índice, el coste es cúbico
        cls.book = next(b for b in texts.published(cls.data)
                        if {'encaje_documentado', 'lecturas_afines'} <= {m['modulo'] for m in texts.payload(cls.data, b)['modulos_permitidos']})
        cls.payload = texts.payload(cls.data, cls.book)
        cls.affine = next(iter(cls.payload['afines_ids']))
        cls.block = {'modulo': 'encaje_documentado', 'evidencias': ['categorias', 'sinopsis_editorial'],
                     'texto': 'Propone una historia con un conflicto central claro y personajes obligados a elegir qué están dispuestos a arriesgar.'}
        cls.others = [
            {'modulo': 'para_quien', 'evidencias': ['categorias'],
             'texto': 'Encaja con lectores adultos que buscan un relato de género con conflicto claro; quien prefiera lecturas tranquilas tiene opciones más serenas en el catálogo.'},
            {'modulo': 'que_formato_elegir', 'evidencias': ['formatos_disponibles'],
             'texto': 'La edición impresa sirve para regalar y releer con calma, mientras que la versión digital cabe en el móvil y pesa menos en un viaje largo.'},
            {'modulo': 'lecturas_afines', 'evidencias': ['afines_catalogo'],
             'texto': f'Comparte terreno con {cls.affine}, aunque cada uno plantea su conflicto central desde un punto de partida distinto y con otra atmósfera.'},
        ]
        cls.good = {'id': cls.book['id'], 'bloques': [cls.block, *cls.others]}

    def check(self, **changes):
        block = copy.deepcopy(self.block)
        block.update(changes)
        return texts.validate_text(self.payload, {**self.good, 'bloques': [block, *self.others]})

    def test_families_and_modules_follow_the_evidence(self):
        self.assertEqual(texts.family({'cocina', 'narrativa'}, 'x' * 300), 'practico')
        self.assertEqual(texts.family({'infantil', 'cocina'}, 'x' * 300), 'infantil')
        self.assertEqual(texts.family({'fantasia'}, 'x' * 300), 'narrativa')
        self.assertEqual(texts.family({'fantasia'}, 'breve'), 'residual')
        for b in texts.published(self.data):
            p = texts.payload(self.data, b)
            for m in p['modulos_permitidos']:
                self.assertIn(p['familia'], texts.MODULES[m['modulo']][0], b['id'])

    def test_every_published_book_gets_its_own_reader_module(self):
        # Solo lo que depende del libro: «lecturas_afines» sale del resto del catálogo y aparece o desaparece cuando
        # crece (una etiqueta deja de ser rara). Exigir 2 módulos contándolo paraba cargas enteras por un libro que no
        # había cambiado; el generador ya escribe min(MIN_BLOCKS, módulos) bloques.
        for b in texts.published(self.data):
            mods = {m['modulo'] for m in texts.payload(self.data, b)['modulos_permitidos']}
            self.assertIn('para_quien', mods, b['id'])

    def test_a_book_left_with_only_its_own_module_keeps_its_published_text(self):
        # Al crecer el catálogo un libro puede perder «lecturas_afines»: su texto de «para_quien» se sigue publicando.
        p = {**self.payload, 'modulos_permitidos': [m for m in self.payload['modulos_permitidos'] if m['modulo'] == 'para_quien']}
        block = {**self.others[0], 'evidencias': ['categorias', 'sinopsis_editorial']}
        record = {'id': self.book['id'], 'bloques': [block]}
        self.assertEqual([x['modulo'] for x in texts.publishable_blocks(p, record)], ['para_quien'])

    def test_publishing_keeps_a_single_own_module_and_drops_a_text_under_the_threshold(self):
        # La decisión real de _publish_once: se sustituyen solo GitHub, el árbol limpio y los builds.
        only_own = {**self.payload, 'modulos_permitidos': [m for m in self.payload['modulos_permitidos'] if m['modulo'] == 'para_quien']}
        block = {**self.others[0], 'evidencias': ['categorias', 'sinopsis_editorial']}
        record = {'id': self.book['id'], 'bloques': [block]}

        class Stop(Exception):
            pass

        def publish(p):
            with tempfile.TemporaryDirectory() as tmp:
                out, tree = Path(tmp, 'out'), Path(tmp, 'tree')
                (tree / 'data').mkdir(parents=True)
                out.mkdir()
                texts.write_json(tree / 'data/reading-catalogue.json', self.data)
                texts.write_json(out / (self.book['id'] + '.json'), record)
                publisher = mock.Mock()
                publisher.publication.gh.return_value = '[]'
                publisher.clean_main_tree.return_value = tree
                with mock.patch.object(texts, 'payload', return_value=p),                         mock.patch.object(texts.subprocess, 'run', side_effect=Stop):
                    with self.assertRaises(Stop):
                        texts._publish_once(out, publisher)
                written = tree / 'data/reading-texts' / (self.book['id'] + '.json')
                return texts.read_json(written)['bloques'] if written.exists() else None

        self.assertEqual([x['modulo'] for x in publish(only_own)], ['para_quien'])
        two = {**self.payload, 'modulos_permitidos': [m for m in self.payload['modulos_permitidos'] if m['modulo'] == 'para_quien'] + [{'modulo': 'encaje_documentado'}]}
        self.assertIsNone(publish(two))

    def test_claim_words_inside_a_named_title_are_the_title_not_a_claim(self):
        # 28/11: el primer afín del catálogo real pasó a ser «… (Best Seller | Ficción)» y todo bloque que lo nombraba
        # caía por «afirmaciones sin respaldo: best seller». Es el nombre de la colección de Debolsillo.
        title = 'Corsarios de Levante (Pirates of the Levant 6) (Best Seller | Ficción)'
        p = {**self.payload, 'afines_ids': {title: 'corsarios'},
             'evidencias': {**self.payload['evidencias'], 'afines_catalogo': [f'«{title}», de Arturo Pérez-Reverte.']}}
        block = {'modulo': 'lecturas_afines', 'evidencias': ['afines_catalogo'],
                 'texto': f'Comparte terreno con {title}, aunque cada uno plantea su conflicto central desde un punto de partida distinto.'}
        self.assertNotIn('afirmaciones sin respaldo: best seller', texts.validate_block(p, block))
        boast = {**block, 'texto': block['texto'] + ' Es un best seller que ya ha conquistado a medio país.'}
        self.assertIn('afirmaciones sin respaldo: best seller', texts.validate_block(p, boast))

    def test_a_short_title_form_does_not_hide_a_claim_around_it(self):
        # Revisión de #1628 (Codex/CodeRabbit): la forma corta «Televisión» no puede tapar «serie de televisión».
        title = 'Televisión: Tecnología y forma cultural'
        p = {**self.payload, 'afines_ids': {title: 'tv'},
             'evidencias': {**self.payload['evidencias'], 'afines_catalogo': [f'«{title}», de Raymond Williams.']}}
        block = {'modulo': 'lecturas_afines', 'evidencias': ['afines_catalogo'],
                 'texto': 'Cuenta con una serie de televisión y se lee junto a Televisión, que mira el mismo medio desde otro punto de partida.'}
        self.assertIn('afirmaciones sin respaldo: serie de televisi', texts.validate_block(p, block))

    def test_valid_blocks_pass_and_affines_are_linked(self):
        blocks, errors = self.check()
        self.assertEqual(errors, [])
        self.assertEqual([x['modulo'] for x in blocks], ['encaje_documentado', 'para_quien', 'que_formato_elegir', 'lecturas_afines'])
        self.assertEqual(blocks[-1]['enlaces'], [self.payload['afines_ids'][self.affine]])

    def test_absorb_keeps_the_second_opinion_across_repair_turns(self):
        opinion = {'genero': 'Fantasía', 'publico': 'juvenil', 'motivo': ''}
        by_id, fichas = {self.book['id']: self.payload}, {}
        texts.absorb(by_id, fichas, [{'id': self.book['id'], 'clasificacion': opinion, 'bloques': [self.block]}])
        texts.absorb(by_id, fichas, [{'id': self.book['id'], 'bloques': [self.block]}])
        self.assertEqual(fichas[self.book['id']]['clasificacion'], opinion)

    def test_the_block_cap_follows_the_modules_not_a_fixed_number(self):
        """Una novela con todos sus módulos permitidos llegó a rechazarse entera por un tope fijo de 5 bloques."""
        fake = [{'modulo': name, 'texto': 'x', 'evidencias': []} for name in texts.MODULES]
        _, errors = texts.validate_text(self.payload, {'id': self.book['id'], 'bloques': fake})
        self.assertNotIn('bloques: lista inválida', errors)
        _, errors = texts.validate_text(self.payload, {'id': self.book['id'], 'bloques': fake + fake[:1]})
        self.assertEqual(errors, ['bloques: lista inválida'])

    def test_affines_are_recognised_by_short_title_and_bring_their_names_and_numbers(self):
        p = {**self.payload, 'afines_ids': {'Diario de Greg 21 - Montando un pollo': 'greg', 'Alchemised (edición coleccionista limitada)': 'alc', 'Amor': 'amor'},
             'evidencias': {**self.payload['evidencias'], 'afines_catalogo': ['«Diario de Greg 21 - Montando un pollo», de Jeff Kinney: Greg vuelve al instituto.']}}
        self.assertEqual(texts.linked(p, 'Quien disfrutó de Diario de Greg 21 o de Alchemised encontrará aquí otro diario.'), ['greg', 'alc'])
        self.assertEqual(texts.linked(p, 'Un libro de humor.'), [])
        block = {'modulo': 'lecturas_afines', 'evidencias': ['categorias'],
                 'texto': 'Quien haya seguido Diario de Greg 21, de Jeff Kinney, encontrará aquí otro diario escolar con humor y torpezas cotidianas.'}
        self.assertEqual(texts.validate_block(p, block), [])

    def test_git_output_is_read_as_utf8_whatever_the_console_codepage(self):
        data = json.loads(texts.git('show', 'HEAD:data/reading-catalogue.json', capture=True))
        self.assertTrue(any('ñ' in json.dumps(b, ensure_ascii=False) or 'á' in json.dumps(b, ensure_ascii=False) for b in data['libros']))

    def test_publish_stages_thousands_of_long_paths_without_hitting_the_command_line_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            texts.git('init', '-q', cwd=repo)
            paths = [f'recomendaciones/libros/{"una-ficha-con-un-titulo-muy-largo-" * 2}{i:04d}/index.html' for i in range(500)]
            for rel in paths:
                (repo / rel).parent.mkdir(parents=True)
                (repo / rel).write_text('x', encoding='utf-8')
            self.assertGreater(sum(len(p) + 1 for p in paths), 32767)
            texts.git_add(paths, cwd=repo)
            self.assertEqual(len(texts.git('diff', '--cached', '--name-only', cwd=repo, capture=True).splitlines()), len(paths))

    def test_generic_format_names_are_not_unbacked_entities(self):
        errors = self.check(texto='Propone una historia con un conflicto central claro; el ISBN identifica esta edición y existe versión Kindle aparte.')[1]
        self.assertFalse(any('nombres sin respaldo' in e for e in errors), errors)
        errors = self.check(texto='Propone una historia con un conflicto central claro que recuerda a Tolkien en su forma de construir el mundo.')[1]
        self.assertIn('encaje_documentado: nombres sin respaldo: Tolkien', errors)

    def test_rejects_meta_doubts_template_phrases_and_unlinked_comparisons(self):
        self.assertTrue(any('fuentes' in e for e in self.check(texto='Propone una historia de conflicto central, aunque la sinopsis no aclara del todo cómo termina el planteamiento.')[1]))
        self.assertTrue(any('fuentes' in e for e in self.check(texto='Propone una historia de conflicto central claro; la información disponible no detalla la edad exacta del protagonista.')[1]))
        self.assertTrue(any('muletilla' in e for e in self.check(texto='Propone, sin duda, una historia con un conflicto central claro y personajes obligados a arriesgar mucho.')[1]))
        unlinked = {**self.others[2], 'texto': 'Comparte terreno con otras historias del catálogo, aunque cada una plantea su conflicto desde un punto de partida distinto.'}
        blocks, errors = texts.validate_text(self.payload, {**self.good, 'bloques': [self.block, *self.others[:2], unlinked]})
        self.assertIn('lecturas_afines: no nombra ningún título de afines_catalogo', errors)
        self.assertIn('faltan módulos: lecturas_afines', errors)
        self.assertEqual(len(blocks), 3)

    def test_rejects_copy_opinion_and_unsupported_facts(self):
        copied = ' '.join(texts.words(self.payload['evidencias']['sinopsis_editorial'])[:texts.COPY_WORDS])
        self.assertTrue(any('copia' in e for e in self.check(texto='En resumen, la sinopsis dice esto: ' + copied + ', y nada más.')[1]))
        self.assertTrue(any('valoración' in e for e in self.check(texto='Una novela apasionante con un conflicto central claro y personajes que arriesgan.')[1]))
        self.assertTrue(any('cifras' in e for e in self.check(texto='Propone una historia ambientada en 1987 con un conflicto central claro y secretos.')[1]))
        self.assertTrue(any('nombres' in e for e in self.check(texto='Propone una historia como las de Zarathustrovski, con un conflicto central claro.')[1]))
        self.assertTrue(any('afirmaciones' in e for e in self.check(texto='Propone la historia ganadora del premio más reciente, con un conflicto central claro.')[1]))
        self.assertEqual(self.check(modulo='como_se_utiliza')[1], ['como_se_utiliza: módulo no permitido', 'faltan módulos: encaje_documentado'])
        self.assertEqual(self.check(evidencias=['traductor'])[1], ['encaje_documentado: evidencias inexistentes', 'faltan módulos: encaje_documentado'])

    def test_citing_a_long_title_or_author_is_not_copying(self):
        title = 'La ciencia del horneado (La ciencia de la cocina)'
        source = f'En {title}, Matt Adlard explica la química del horno paso a paso para cocineros caseros.'
        names = [title, 'Matt Adlard']
        cited = f'{title}, de Matt Adlard, interesa a quien quiere entender por qué falla un bizcocho.'
        self.assertFalse(texts.ngrams(cited, names=names) & texts.ngrams(source, names=names))
        self.assertTrue(texts.ngrams(cited) & texts.ngrams(source))
        copied = 'Aquí Matt Adlard explica la química del horno paso a paso para todos.'
        self.assertTrue(texts.ngrams(copied, names=names) & texts.ngrams(source, names=names))

    def test_threshold_and_no_abstention(self):
        only = {**self.block, 'evidencias': ['titulo']}
        blocks, errors = texts.validate_text(self.payload, {'id': self.book['id'], 'bloques': [only]})
        self.assertEqual(blocks, [])
        self.assertIn('por debajo del umbral: solo datos básicos', errors)
        blocks, errors = texts.validate_text(self.payload, {'id': self.book['id'], 'bloques': [self.block]})
        self.assertEqual((blocks, errors[-1]), ([], 'menos de 2 bloques válidos'))
        blocks, errors = texts.validate_text(self.payload, {'id': self.book['id'], 'bloques': [], 'abstencion': 'SIN_APORTE_INCREMENTAL'})
        self.assertEqual(blocks, [])
        self.assertIn('no se admite abstenerse', errors[0])

    def test_consult_failures_wait_and_never_spend_attempts(self):
        from types import SimpleNamespace
        from unittest import mock
        QuietHoursError = type('QuietHoursError', (RuntimeError,), {})
        state, waits = {}, []
        args = SimpleNamespace(port=0, wait_min=1)
        for exc, expected in ((QuietHoursError('descanso'), 3600), (OSError('cdp'), 60)):
            with mock.patch.object(texts, 'converse', side_effect=exc), mock.patch.object(texts.time, 'sleep', waits.append),                     mock.patch.dict('sys.modules', {'quiet_hours': SimpleNamespace(seconds_until_active=lambda: 3600)}):
                self.assertIsNone(texts.consult_batch([self.payload], state, args))
            self.assertEqual(waits[-1], expected)
        self.assertEqual(state, {})

    def test_web_texts_run_through_the_night_unlike_social_networks(self):
        from types import SimpleNamespace
        from unittest import mock
        seen = {}
        with mock.patch.dict('sys.modules', {'chatgpt_consult': SimpleNamespace()}), mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('RRSS_NIGHT_OK', None)
            texts.rrss()
            seen['night'] = os.environ.get('RRSS_NIGHT_OK')
        self.assertEqual(seen['night'], '1')

    def test_publication_runs_once_at_its_hour_without_stopping_the_loop(self):
        from datetime import datetime
        from types import SimpleNamespace
        args = SimpleNamespace(publish_at=[21], publish_every=25)
        at = datetime(2026, 11, 3, 21, 5)
        self.assertTrue(texts.publish_due(args, at, ''))
        self.assertFalse(texts.publish_due(args, at, '2026-11-03 21'))
        self.assertFalse(texts.publish_due(args, datetime(2026, 11, 3, 10), ''))

    def test_publication_deferred_by_a_catalogue_load_retries_within_the_hour_and_keeps_its_texts(self):
        """27/11: aplazada a las 21 h por una carga en CI esperaba al día siguiente (#1562 roja desde el 24/11)."""
        from datetime import datetime
        from types import SimpleNamespace
        args = SimpleNamespace(publish_at=[21], publish_every=25)
        back, retry_at = texts.after_publish(texts.PUBLISH_DEFERRED, 7, 1000)
        self.assertEqual((back, retry_at), (7, 1000 + texts.PUBLISH_RETRY))
        at = datetime(2026, 11, 26, 21, 40)
        self.assertFalse(texts.publish_now(args, at, '2026-11-26 21', back, retry_at, 1000 + 60))
        self.assertTrue(texts.publish_now(args, datetime(2026, 11, 26, 23, 0), '2026-11-26 21', back, retry_at, retry_at))
        self.assertEqual(texts.after_publish(1, 7, 1000), (7, 0))  # fallida: los textos siguen pendientes
        self.assertEqual(texts.after_publish(0, 7, 1000), (0, 0))
        self.assertFalse(texts.publish_now(args, at, '', 0, 0, 0))
        self.assertTrue(texts.publish_now(args, datetime(2026, 11, 27, 21, 1), '2026-11-26 21', 7, 0, 0))

    def test_publish_command_exits_75_when_a_catalogue_load_is_in_ci(self):
        from types import SimpleNamespace
        publisher = SimpleNamespace(publication=SimpleNamespace(gh=lambda *a: '[]'))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'out'
            out.mkdir()
            (out / 'x.json').write_text('{}', encoding='utf-8')
            with mock.patch.object(texts.gh_listas, 'lista', return_value=[{'headRefName': 'automation/reading-catalogue-2026-11-26-1',
                                                                          'createdAt': '2099-01-01T00:00:00Z'}]), \
                    mock.patch.object(texts, 'catalogue_in_ci', return_value='automation/reading-catalogue-2026-11-26-1'):
                self.assertEqual(texts._publish_once(out, publisher), texts.DEFERRED)

    def test_same_chat_repairs_failing_blocks_then_improves_short_ones(self):
        wrong = {**self.others[2], 'texto': self.others[2]['texto'] + ' Se publicó en 1987.'}
        first = {'id': self.book['id'], 'bloques': [self.block, self.others[0], self.others[1], wrong]}
        fixed = {'id': self.book['id'], 'bloques': [self.others[2]]}
        longer = {**self.others[1], 'texto': self.others[1]['texto'] + ' En tapa blanda pesa menos y se lleva mejor de viaje; en Kindle se ajusta la letra.'}
        answers = iter([first, fixed, {'id': self.book['id'], 'bloques': [longer]}])
        sent = []

        def send(question, port, wait_min, follow_up):
            n, message = 0, question
            while message:
                sent.append(message)
                n += 1
                message = follow_up('```json\n' + json.dumps({'fichas': [next(answers)]}, ensure_ascii=False) + '\n```', n)

        with mock.patch.object(texts, 'SHORT_BLOCK', len(self.others[1]['texto']) + 1):
            fichas = texts.converse([self.payload], {}, 0, 1, send=send)
        self.assertIn('cifras sin respaldo: 1987', sent[1])
        self.assertIn('cada cifra', sent[1])
        self.assertIn('escuetos', sent[2])
        blocks, errors = texts.validate_text(self.payload, fichas[0])
        self.assertEqual(errors, [])
        self.assertEqual(next(x for x in blocks if x['modulo'] == 'que_formato_elegir')['texto'], longer['texto'])
        self.assertNotIn('1987', ' '.join(x['texto'] for x in blocks))

    def test_second_opinion_is_recorded_and_never_changes_the_text_or_its_hash(self):
        import tempfile
        mine = self.payload['clasificacion_actual']
        before = texts.source_hash(self.payload)
        self.assertEqual(before, texts.source_hash({**self.payload, 'clasificacion_actual': {'generos': ['Otro'], 'publico': 'infantil'}}))
        prompt = texts.build_prompt([self.payload])
        self.assertIn('clasificacion_actual', prompt)
        self.assertNotIn('{{GENEROS}}', prompt)
        agree = {'genero': mine['generos'][0] if mine['generos'] else 'Otro', 'publico': mine['publico'], 'motivo': ''}
        record, why = texts.compare_classification(self.payload, agree)
        self.assertIsNone(why)
        self.assertEqual(record['coincide'], bool(mine['generos']) and mine['publico'] in texts.PUBLICOS)
        other_public = next(x for x in texts.PUBLICOS if x != mine['publico'])
        record, why = texts.compare_classification(self.payload, {**agree, 'publico': other_public})
        self.assertEqual(why, 'no coincide y falta el motivo')
        record, why = texts.compare_classification(
            self.payload, {**agree, 'publico': other_public, 'motivo': 'La sinopsis habla de escenas explícitas y de adultos.'})
        self.assertFalse(record['coincide'])
        self.assertEqual(texts.compare_classification(self.payload, {'genero': 'Inventado', 'publico': 'adultos'})[1], 'género fuera de la lista')
        self.assertEqual(texts.compare_classification(self.payload, {'genero': 'Fantasía', 'publico': 'veteranos'})[1], 'público fuera de la lista')
        with tempfile.TemporaryDirectory() as tmp:
            out, state = Path(tmp), {}
            row = {**self.good, 'clasificacion': {**agree, 'publico': other_public, 'motivo': 'La sinopsis habla de escenas explícitas y de adultos.'}}
            self.assertEqual(texts.save_results([self.payload], [row], state, out), (1, 0))
            opinions = texts.read_json(out / 'clasificacion.opiniones')
            self.assertFalse(opinions[self.book['id']]['coincide'])
            self.assertEqual([f.name for f in out.glob('*.json')], [self.book['id'] + '.json'])
            # Sin el campo, el texto se guarda igual y no se inventa una opinión.
            self.assertEqual(texts.save_results([self.payload], [self.good], {}, Path(tmp) / 'otro') if (Path(tmp) / 'otro').mkdir() is None else None, (1, 0))
            self.assertFalse((Path(tmp) / 'otro' / 'clasificacion.opiniones').exists())

    def test_rejection_reasons_go_back_into_the_next_prompt_and_worse_repairs_never_replace(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out, state = Path(tmp), {}
            weak = {**self.good, 'bloques': [self.block, *self.others[:2]]}
            self.assertEqual(texts.save_results([self.payload], [weak], state, out), (1, 0))
            self.assertIn(self.book['id'], [b['id'] for b in texts.pending(self.data, out, state)])
            prompt = texts.build_prompt([self.payload], state)
            self.assertIn('faltan módulos: lecturas_afines', prompt)
            self.assertNotIn('afines_ids', prompt)
            self.assertEqual(texts.save_results([self.payload], [{**self.good, 'bloques': [self.block, self.others[0]]}], state, out), (0, 1))
            self.assertEqual(len(texts.read_json(out / (self.book['id'] + '.json'))['bloques']), 3)
            self.assertEqual(texts.save_results([self.payload], [self.good], state, out), (1, 0))
            self.assertNotIn(self.book['id'], [b['id'] for b in texts.pending(self.data, out, state)])
            state[self.book['id']]['intentos'] = texts.MAX_ATTEMPTS
            (out / (self.book['id'] + '.json')).unlink()
            self.assertNotIn(self.book['id'], [b['id'] for b in texts.pending(self.data, out, state)])

    def test_catalogue_taxonomy_is_rejected_and_stale_saved_blocks_are_repaired(self):
        """«Comparte las categorías X» describe el menú de la web: el validador lo rechaza, también en lo ya guardado."""
        import tempfile
        taxonomy = {**self.others[2], 'texto': f'{self.affine} comparte las categorías Aventuras e Infancia con este volumen, aunque cambia de tono.'}
        errors = texts.validate_block(self.payload, taxonomy)
        self.assertTrue(any('categorías del catálogo' in e for e in errors), errors)
        with tempfile.TemporaryDirectory() as tmp:
            out, state = Path(tmp), {}
            old = {'id': self.book['id'], 'familia': self.payload['familia'], 'bloques': [self.block, *self.others[:2], taxonomy],
                   'descartados': [], 'version': texts.VERSION, 'fuente_hash': texts.source_hash(self.payload)}
            texts.write_json(out / (self.book['id'] + '.json'), old)
            self.assertIn(self.book['id'], [b['id'] for b in texts.pending(self.data, out, state)])
            self.assertIn('lecturas_afines: nombra las categorías', texts.build_prompt([self.payload], state))
            # La reparación trae solo el módulo afectado y se combina con los bloques válidos ya guardados.
            repair = {'id': self.book['id'], 'bloques': [self.block, self.others[2]]}
            self.assertEqual(texts.save_results([self.payload], [repair], state, out), (1, 0))
            saved = texts.read_json(out / (self.book['id'] + '.json'))
            self.assertEqual(sorted(x['modulo'] for x in saved['bloques']),
                             ['encaje_documentado', 'lecturas_afines', 'para_quien', 'que_formato_elegir'])
            self.assertNotIn('categorías', json.dumps(saved, ensure_ascii=False))

    def test_affines_survive_catalogue_growth(self):
        """Un libro con afines no los pierde porque su tema se vuelva común: llevado al límite (ningún afín pasa el
        umbral de rareza), sigue teniendo afines y su segundo módulo. Así una carga no tumba a un libro ya publicado."""
        con_afines = [b for b in texts.published(self.data)
                      if texts.affine_books(self.data, b, {c['id'] for c in builder.categories(self.data, b)})][:40]
        self.assertTrue(con_afines)
        with mock.patch.object(texts, 'MIN_AFFINITY', float('inf')):
            for b in con_afines:
                self.assertTrue(texts.affine_books(self.data, b, {c['id'] for c in builder.categories(self.data, b)}), b['id'])

    def test_affines_share_audience_and_are_described_by_content_not_labels(self):
        """Afines del mismo público y descritos por su sinopsis: así el texto compara libros, no etiquetas del menú."""
        compared = 0
        for b in texts.published(self.data):
            cats = {c['id'] for c in builder.categories(self.data, b)}
            for x, _ in texts.affine_books(self.data, b, cats):
                if set(x['autores']) & set(b['autores']):
                    continue
                compared += 1
                other = {c['id'] for c in builder.categories(self.data, x)}
                self.assertFalse(texts.audience(cats) and texts.audience(other) and texts.audience(cats) != texts.audience(other), (b['id'], x['id']))
                ages = texts.min_age(b), texts.min_age(x)
                self.assertFalse(None not in ages and abs(ages[0] - ages[1]) > 4, (b['id'], x['id']))
            for line in texts.payload(self.data, b)['evidencias'].get('afines_catalogo', []):
                self.assertNotIn('comparte:', line, b['id'])
                self.assertRegex(line, r'^«.+», de .+: \S', b['id'])
        self.assertGreater(compared, 100)
        self.assertEqual(texts.min_age({'edad_recomendada': 'Adultos'}), 18)
        self.assertEqual(texts.min_age({'edad_recomendada': 'De 9 a 12 años'}), 9)
        self.assertEqual(texts.gist({'sinopsis_breve': 'Una frase. Otra frase.'}), 'Una frase.')

    def test_answer_parsing_requires_every_id(self):
        answer = 'Aquí está:\n```json\n' + json.dumps({'fichas': [self.good]}, ensure_ascii=False) + '\n```'
        self.assertEqual(texts.answer_label([self.book['id']])(answer), 'JSON_VALIDO')
        self.assertEqual(texts.answer_label([self.book['id'], 'otro'])(answer), 'IDS_INCORRECTOS')
        self.assertEqual(texts.answer_label([self.book['id']])('```json\n{"fichas": ['), 'JSON_TRUNCADO')

    def test_book_page_renders_modules_before_editorial_synopsis(self):
        builder.OWN_TEXTS.clear()
        builder.OWN_TEXTS[self.book['id']] = {'id': self.book['id'], 'bloques': self.check()[0]}
        template = (ROOT / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
        affine = next(b for b in self.data['libros'] if b['id'] == self.payload['afines_ids'][self.affine])
        try:
            page = builder.render_book(self.data, self.book, template)
            gone = copy.deepcopy(self.data)
            next(b for b in gone['libros'] if b['id'] == affine['id'])['estado'] = 'retirado'
            without = builder.render_book(gone, self.book, template)
        finally:
            builder.OWN_TEXTS.clear()
        self.assertLess(page.index('Antes de elegir este libro'), page.index('Sinopsis de la editorial'))
        self.assertIn('<h3>Qué tipo de lectura propone</h3>', page)
        self.assertIn('Antes de elegirlo: qué tipo de lectura propone y para quién es.', page)
        self.assertIn('href="' + builder.url(affine) + '"', page.split('Sinopsis de la editorial')[0])
        self.assertNotIn('Con qué otros libros compararlo', without)
        self.assertIn('<h3>Para quién es</h3>', without)
        self.assertNotIn('Preguntas frecuentes', page)

    def test_instant_power_moves_selector_to_minimum_and_closes_menu(self):
        class Locator:
            def __init__(self, page, found=True):
                self.page, self.found = page, found
            first = property(lambda self: self)
            def count(self): return int(self.found)
            def wait_for(self, **_):
                if not self.found:
                    raise TimeoutError
            def click(self): self.page.keys.append('click')
            def focus(self): self.page.keys.append('focus')

        class Page:
            def __init__(self, found=True):
                self.keys, self.found = [], found
                self.keyboard = self
            def locator(self, _selector): return Locator(self, self.found)
            def press(self, key): self.keys.append(key)
            def wait_for_timeout(self, _ms): pass

        page = Page()
        self.assertTrue(texts.instant_power(page, 'Alta'))
        self.assertEqual(page.keys, ['click', 'focus'] + ['ArrowLeft'] * 4 + ['Escape'])
        self.assertFalse(texts.instant_power(Page(found=False)))


if __name__ == '__main__':
    unittest.main()
