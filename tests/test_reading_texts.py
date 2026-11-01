"""Orientación propia por ficha: el validador bloquea copia, valoraciones e invenciones y la ficha la pinta.

Usa datos y plantillas reales. No abre el navegador ni consulta ChatGPT.
"""
import copy
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
                        if 'encaje_documentado' in {m['modulo'] for m in texts.payload(cls.data, b)['modulos_permitidos']})
        cls.payload = texts.payload(cls.data, cls.book)
        cls.block = {'modulo': 'encaje_documentado', 'evidencias': ['categorias', 'sinopsis_editorial'], 'necesidad': 'tipo de lectura',
                     'texto': 'Propone una historia con un conflicto central claro y personajes obligados a elegir qué están dispuestos a arriesgar.'}
        cls.good = {'id': cls.book['id'], 'bloques': [cls.block], 'abstencion': None}

    def check(self, **changes):
        block = copy.deepcopy(self.block)
        block.update(changes)
        return texts.validate_text(self.payload, {**self.good, 'bloques': [block]})

    def test_families_and_modules_follow_the_evidence(self):
        self.assertEqual(texts.family({'cocina', 'narrativa'}, 'x' * 300), 'practico')
        self.assertEqual(texts.family({'infantil', 'cocina'}, 'x' * 300), 'infantil')
        self.assertEqual(texts.family({'fantasia'}, 'x' * 300), 'narrativa')
        self.assertEqual(texts.family({'fantasia'}, 'breve'), 'residual')
        for b in texts.published(self.data):
            p = texts.payload(self.data, b)
            for m in p['modulos_permitidos']:
                self.assertIn(p['familia'], texts.MODULES[m['modulo']][0])

    def test_valid_block_passes(self):
        blocks, errors = self.check()
        self.assertEqual(errors, [])
        self.assertEqual([x['modulo'] for x in blocks], ['encaje_documentado'])

    def test_rejects_copy_opinion_and_unsupported_facts(self):
        copied = ' '.join(texts.words(self.payload['evidencias']['sinopsis_editorial'])[:texts.COPY_WORDS])
        self.assertTrue(any('copia' in e for e in self.check(texto='En resumen, la sinopsis dice esto: ' + copied + ', y nada más.')[1]))
        self.assertTrue(any('valoración' in e for e in self.check(texto='Una novela apasionante con un conflicto central claro y personajes que arriesgan.')[1]))
        self.assertTrue(any('cifras' in e for e in self.check(texto='Propone una historia ambientada en 1987 con un conflicto central claro y secretos.')[1]))
        self.assertTrue(any('nombres' in e for e in self.check(texto='Propone una historia como las de Zarathustrovski, con un conflicto central claro.')[1]))
        self.assertTrue(any('afirmaciones' in e for e in self.check(texto='Propone la historia ganadora del premio más reciente, con un conflicto central claro.')[1]))
        self.assertEqual(self.check(modulo='como_se_utiliza')[1], ['como_se_utiliza: módulo no permitido'])
        self.assertEqual(self.check(evidencias=['traductor'])[1], ['encaje_documentado: evidencias inexistentes'])

    def test_threshold_and_abstention(self):
        blocks, errors = self.check(evidencias=['titulo'])
        self.assertEqual(blocks, [])
        self.assertIn('por debajo del umbral: solo datos básicos', errors)
        self.assertEqual(texts.validate_text(self.payload, {'id': self.book['id'], 'bloques': [], 'abstencion': 'SIN_APORTE_INCREMENTAL'}), ([], []))
        self.assertEqual(texts.validate_text(self.payload, {'id': self.book['id'], 'bloques': [self.block], 'abstencion': 'SIN_APORTE_INCREMENTAL'})[1], ['abstención inválida'])
        self.assertEqual(texts.validate_text(self.payload, {'id': self.book['id'], 'bloques': [], 'abstencion': None})[1], ['sin bloques ni abstención'])

    def test_answer_parsing_requires_every_id(self):
        answer = 'Aquí está:\n```json\n' + json.dumps({'fichas': [self.good]}, ensure_ascii=False) + '\n```'
        self.assertEqual(texts.answer_label([self.book['id']])(answer), 'JSON_VALIDO')
        self.assertEqual(texts.answer_label([self.book['id'], 'otro'])(answer), 'IDS_INCORRECTOS')
        self.assertEqual(texts.answer_label([self.book['id']])('```json\n{"fichas": ['), 'JSON_TRUNCADO')

    def test_book_page_renders_modules_before_editorial_synopsis(self):
        builder.OWN_TEXTS.clear()
        builder.OWN_TEXTS[self.book['id']] = {'id': self.book['id'], 'bloques': self.check()[0]}
        try:
            template = (ROOT / 'scripts/templates/reading-catalogue.html.tmpl').read_text(encoding='utf-8')
            page = builder.render_book(self.data, self.book, template)
        finally:
            builder.OWN_TEXTS.clear()
        self.assertLess(page.index('Antes de elegir este libro'), page.index('Sinopsis de la editorial'))
        self.assertIn('<h3>Qué tipo de lectura propone</h3>', page)
        self.assertIn('Antes de elegirlo: qué tipo de lectura propone.', page)
        self.assertNotIn('Preguntas frecuentes', page)


if __name__ == '__main__':
    unittest.main()
