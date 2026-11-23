"""Carga hipotética en CI: ninguna mutación de un campo puede dejar un fallo sin dueño, y lo reparable se repara.

La semilla cambia cada día (más libros distintos con el tiempo) y se imprime para reproducir un fallo.
"""
import datetime
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import ensayo_carga  # noqa: E402

# Lo que el normalizador sabe arreglar nunca debe acabar apartando el libro.
REPARABLES = ('titulo largo 206', 'titulo mayusculas', 'titulo mojibake', 'titulo inicial caida', 'titulo espacios y saltos',
              'titulo con html', 'titulo ligaduras', 'autor mayusculas', 'autor mojibake', 'sinopsis gritando',
              'sinopsis 5000', 'sinopsis mojibake', 'sinopsis html', 'isbn con guiones', 'fecha formato', 'portada fuente http',
              'autores string')


class EnsayoCargaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semilla = datetime.date.today().toordinal()
        cls.casos = ensayo_carga.ensayo(muestra=30, semilla=cls.semilla, por_mutacion=3)

    def test_ningun_fallo_sin_dueno(self):
        sin = [(m, i, c) for m, i, k, c in self.casos if k == 'SIN DUEÑO']
        self.assertEqual(sin, [], f'semilla {self.semilla}')

    def test_lo_reparable_no_se_aparta(self):
        mal = [(m, i, c) for m, i, k, c in self.casos if m in REPARABLES and k == 'aparta']
        self.assertEqual(mal, [], f'semilla {self.semilla}')

    def test_se_ejecutan_todas_las_mutaciones(self):
        self.assertEqual({m for m, *_ in self.casos}, set(ensayo_carga.MUTACIONES), f'semilla {self.semilla}')


if __name__ == '__main__':
    unittest.main()
