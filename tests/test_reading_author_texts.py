"""Textos propios de autor (scripts/reading-author-texts.py): validador, carga en el constructor y secciones de la ficha."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("reading_author_texts_test", ROOT / "scripts/reading-author-texts.py")
rat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rat)
builder = rat.catalogue

PAYLOAD = {'slug': 'ana-perez', 'nombre': 'Ana Pérez', 'candidatos_parecidos': ['Luis Gómez', 'Marta Ruiz']}
INTRO = ('Ana Pérez es una novelista española nacida en Valladolid que escribe novela negra ambientada en Castilla. '
         'Se dio a conocer con la serie de la inspectora Lara Sanz, que ha tenido varias reediciones y una adaptación '
         'televisiva, y desde entonces publica una novela cada dos años con la editorial Destino y otros sellos.')
BIO = ' '.join(['Ana Pérez estudió Periodismo en Madrid y trabajó en la sección de sucesos de un diario regional.'] * 9)


def answer(**over):
    t = {'slug': 'ana-perez', 'identificado': True, 'intro': INTRO, 'biografia': BIO,
         'por_donde_empezar': [{'titulo': 'La niebla', 'motivo': 'Es la primera novela de la serie de la inspectora Sanz.'}],
         'obras': [{'titulo': 'El río', 'anio': 2015, 'saga': 'Inspectora Sanz'}, {'titulo': 'La niebla', 'titulo_original': 'La niebla', 'anio': 2012, 'saga': 'Inspectora Sanz'},
                   {'titulo': 'Mal año', 'anio': 3020}],
         'sagas': [{'nombre': 'Inspectora Sanz', 'libros': ['La niebla', 'El río']}, {'nombre': 'Suelta', 'libros': ['Una']}],
         'parecidos': [{'nombre': 'Luis Gómez', 'motivo': 'También escribe novela negra en ciudades de provincia.'},
                       {'nombre': 'Inventado Total', 'motivo': 'No está entre los candidatos dados.'}],
         'faq': [{'pregunta': '¿En qué orden se lee la serie de Lara Sanz?', 'respuesta': 'Empieza con La niebla, de 2012, y sigue con El río.'},
                 {'pregunta': '¿Tiene adaptaciones?', 'respuesta': 'La serie se adaptó a televisión en 2020.'},
                 {'pregunta': '¿Dónde comprar sus libros?', 'respuesta': 'En cualquier librería del país.'}],
         'fuentes': [{'titulo': 'Wikipedia', 'url': 'https://es.wikipedia.org/wiki/Ana_P%C3%A9rez'}, {'titulo': 'Editorial', 'url': 'https://www.destino.es/ana'},
                     {'titulo': 'Insegura', 'url': 'http://ejemplo.es'}, {'titulo': 'Chat', 'url': 'https://chatgpt.com/c/1'}]}
    t.update(over)
    return t


class ValidateTest(unittest.TestCase):
    def test_valid_answer_is_cleaned(self):
        text, errors = rat.validate(PAYLOAD, answer(), year=2026)
        self.assertEqual(errors, [])
        self.assertEqual([w['titulo'] for w in text['obras']], ['La niebla', 'El río'])  # orden por año, sin el año imposible
        self.assertNotIn('titulo_original', text['obras'][0])  # igual al título: sobra
        self.assertEqual([s['nombre'] for s in text['sagas']], ['Inspectora Sanz'])
        self.assertEqual([x['nombre'] for x in text['parecidos']], ['Luis Gómez'])
        self.assertEqual(len(text['faq']), 2)  # fuera la de comprar
        self.assertEqual([f['url'] for f in text['fuentes']], ['https://es.wikipedia.org/wiki/Ana_P%C3%A9rez', 'https://www.destino.es/ana'])

    def test_promotion_links_and_short_bio_are_errors(self):
        _, errors = rat.validate(PAYLOAD, answer(intro=INTRO + ' Una autora imprescindible.', biografia='Corta en https://x.es'), year=2026)
        self.assertTrue(any(e.startswith('intro: valoración') for e in errors))
        self.assertTrue(any(e.startswith('biografia:') and 'palabras' in e for e in errors))
        self.assertTrue(any('sin enlaces' in e for e in errors))

    def test_unidentified_author_is_kept_without_content(self):
        text, errors = rat.validate(PAYLOAD, {'slug': 'ana-perez', 'identificado': False})
        self.assertEqual((text, errors), ({'slug': 'ana-perez', 'identificado': False}, []))
        self.assertIsNone(rat.publishable(PAYLOAD, text))

    def test_wrong_slug_is_rejected(self):
        self.assertEqual(rat.validate(PAYLOAD, answer(slug='otra'))[0], None)

    def test_extract_takes_the_fenced_json(self):
        self.assertEqual(rat.extract('Aquí va:\n```json\n{"slug": "ana-perez", "x": 1}\n```')['x'], 1)


class BuilderTest(unittest.TestCase):
    def test_broken_or_incomplete_files_are_ignored(self):
        text, _ = rat.validate(PAYLOAD, answer(), year=2026)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / builder.AUTHOR_TEXTS_DIR
            folder.mkdir(parents=True)
            (folder / 'ana-perez.json').write_text(json.dumps(text, ensure_ascii=False), encoding='utf-8')
            (folder / 'otro.json').write_text(json.dumps({**text, 'slug': 'otro', 'fuentes': [{'url': 'http://x.es'}]}), encoding='utf-8')
            (folder / 'roto.json').write_text('{', encoding='utf-8')
            self.assertEqual(list(builder.load_author_texts(Path(tmp))), ['ana-perez'])

    def test_sections_link_catalogue_books_and_amazon_with_tag(self):
        text, _ = rat.validate(PAYLOAD, answer(), year=2026)
        text['fecha_revision'] = '2026-11-23'
        a = {'nombre': 'Ana Pérez', 'slug': 'ana-perez'}
        book = {'id': 'isbn-9788400000001', 'titulo': 'La niebla (Edición especial)', 'slug': 'la-niebla'}
        nav, before, after = builder.author_text_sections(a, text, [book], {'Luis Gómez': {'nombre': 'Luis Gómez', 'slug': 'luis-gomez'}})
        self.assertIn('href="#sagas"', nav)
        self.assertIn('href="' + builder.url(book) + '"', before)  # obra del catálogo: a su ficha
        self.assertIn('tag=davidporto-21', before)  # «El río» no está: búsqueda de Amazon con el tag
        self.assertIn('rel="sponsored nofollow noopener noreferrer"', before)
        self.assertIn('/autores/luis-gomez/', after)
        self.assertIn('Revisado el 23 de noviembre de 2026', after)


if __name__ == '__main__':
    unittest.main()
