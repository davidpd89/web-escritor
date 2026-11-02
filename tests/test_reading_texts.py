"""Orientación propia por ficha: el validador bloquea copia, valoraciones e invenciones y la ficha la pinta.

Usa datos y plantillas reales. No abre el navegador ni consulta ChatGPT.
"""
import copy
import os
import importlib.util
import json
import unittest
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
                self.assertIn(p['familia'], texts.MODULES[m['modulo']][0])

    def test_every_published_book_gets_at_least_two_modules(self):
        for b in texts.published(self.data):
            mods = {m['modulo'] for m in texts.payload(self.data, b)['modulos_permitidos']}
            self.assertGreaterEqual(len(mods), 2, b['id'])
            self.assertIn('para_quien', mods)

    def test_valid_blocks_pass_and_affines_are_linked(self):
        blocks, errors = self.check()
        self.assertEqual(errors, [])
        self.assertEqual([x['modulo'] for x in blocks], ['encaje_documentado', 'para_quien', 'que_formato_elegir', 'lecturas_afines'])
        self.assertEqual(blocks[-1]['enlaces'], [self.payload['afines_ids'][self.affine]])

    def test_git_output_is_read_as_utf8_whatever_the_console_codepage(self):
        data = json.loads(texts.git('show', 'HEAD:data/reading-catalogue.json', capture=True))
        self.assertTrue(any('ñ' in json.dumps(b, ensure_ascii=False) or 'á' in json.dumps(b, ensure_ascii=False) for b in data['libros']))

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
            with mock.patch.object(texts, 'consult', side_effect=exc), mock.patch.object(texts.time, 'sleep', waits.append),                     mock.patch.dict('sys.modules', {'quiet_hours': SimpleNamespace(seconds_until_active=lambda: 3600)}):
                self.assertIsNone(texts.consult_batch([self.payload], state, args))
            self.assertEqual(waits[-1], expected)
        self.assertEqual(state, {})

    def test_web_texts_run_through_the_night_unlike_social_networks(self):
        from types import SimpleNamespace
        from unittest import mock
        seen = {}
        fake = SimpleNamespace(consult=lambda *a, **k: (seen.setdefault('night', os.environ.get('RRSS_NIGHT_OK')), '')[1:] + (None,))
        with mock.patch.dict('sys.modules', {'chatgpt_consult': fake}), mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('RRSS_NIGHT_OK', None)
            texts.consult('pregunta', ['a'], 9240, 1)
        self.assertEqual(seen['night'], '1')

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
                self.assertNotIn('comparte:', line)
                self.assertRegex(line, r'^«.+», de .+: \S')
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


if __name__ == '__main__':
    unittest.main()
