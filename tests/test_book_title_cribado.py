"""Cribado de títulos: el generador de títulos SEO nunca devuelve algo que el contrato rechace (≤75, con autor).

23/11: una ficha con título de 206 caracteres salió con la carga y la puerta de la PR la rechazó 2,5 h después.
Aquí se pasan por `book_title` los libros reales y variantes hostiles (título larguísimo, firma institucional,
muchos autores, gemelos de título casi idéntico, mayúsculas, caracteres raros) y se exige lo mismo que el contrato.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rcb', ROOT / 'scripts/build-reading-catalogue.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
DATA = json.loads((ROOT / 'data/reading-catalogue.json').read_text(encoding='utf-8'))
PUBLICADOS = [b for b in DATA['libros'] if b.get('estado') == 'publicado']

LARGO = 'Manual completo y definitivo ' + 'de la historia universal del pensamiento y de las ideas ' * 4
FIRMAS = ['Grupo Andaluz de Trabajo en Endometriosis de la SAGO', 'Ana', 'Mª del Carmen Fernández-Gómez de la Torre y Álvarez',
          'J. R. R. Tolkien']


def comprobar(case, b, libros):
    t = build.book_title(b, libros)
    case.assertLessEqual(len(t), 75, f'{b["id"]}: {len(t)} caracteres: {t}')
    case.assertTrue(build.author_in_title(b, t), f'{b["id"]}: sin autor en «{t}»')


class CribadoTitulos(unittest.TestCase):
    def test_libros_reales(self):
        for b in PUBLICADOS:
            with self.subTest(b['id']):
                comprobar(self, b, PUBLICADOS)

    def test_variantes_hostiles_de_libros_reales(self):
        muestra = PUBLICADOS[::25]
        for b in muestra:
            for titulo in (LARGO, b['titulo'].upper(), b['titulo'] + ' ' + LARGO, 'ñ' * 120, b['titulo'] + ': ' + 'x' * 150):
                for firma in FIRMAS:
                    for extra in ([], ['Otro Autor Largo Apellido', 'Tercero']):
                        v = {**b, 'titulo': titulo, 'autores': [firma, *extra]}
                        with self.subTest(b['id'], titulo=titulo[:20], firma=firma[:12], n=len(extra)):
                            comprobar(self, v, PUBLICADOS)

    def test_gemelos_con_titulo_casi_identico(self):
        b = PUBLICADOS[0]
        gemelos = [{**b, 'id': f'g{i}', 'isbn13': f'97800000000{i:02d}', 'titulo': LARGO + ('!' * i)} for i in range(4)]
        for g in gemelos:
            for firma in FIRMAS:
                v = {**g, 'autores': [firma]}
                comprobar(self, v, [{**x, 'autores': [firma]} for x in gemelos])


if __name__ == '__main__':
    unittest.main()
