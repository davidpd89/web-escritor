"""La segunda opinión de las altas elige entre los géneros activos del catálogo, no entre una lista fija.

Origen (27/11): la lista fija tenía 17 géneros; historia, derecho, psicología, teatro o manuales acababan en «Otro»
y la segunda opinión no podía corregir esos libros nuevos.
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_taxonomy as tax  # noqa: E402

spec = importlib.util.spec_from_file_location('reading_texts', ROOT / 'scripts' / 'reading-texts.py')
texts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(texts)


class SecondOpinionGenres(unittest.TestCase):
    def test_every_active_genre_can_be_chosen(self):
        cats = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))['categorias']
        active = {c['id'] for c in cats if c['tipo'] == 'genero' and c['activa']} - tax.NOT_ASKED
        chosen = {tax.gpt_genre_id(name) for name in texts.GENEROS} - {None}
        self.assertEqual(chosen, active)
        self.assertIn('Otro', texts.GENEROS)

    def test_saved_opinions_keep_their_meaning(self):
        for name, ident in tax.LEGACY_GPT_NAMES.items():
            self.assertEqual(tax.gpt_genre_id(name), ident, name)
        self.assertIsNone(tax.gpt_genre_id('Otro'))

    def test_new_genre_reaches_the_prompt(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'c.json'
            path.write_text(json.dumps({'categorias': [
                {'id': 'teatro', 'nombre': 'Teatro', 'tipo': 'genero', 'activa': True, 'orden': 1},
                {'id': 'romantasy', 'nombre': 'Romantasy', 'tipo': 'genero', 'activa': True, 'orden': 2},
                {'id': 'viejo', 'nombre': 'Viejo', 'tipo': 'genero', 'activa': False, 'orden': 3}]}), encoding='utf-8')
            self.assertEqual(tax.asked_genres(path), (('teatro', 'Teatro'),))


if __name__ == '__main__':
    unittest.main()
