"""Las palabras con «�» se rehacen con el vocabulario del catálogo; si la letra es dudosa, no se adivina.

Origen (28/11/2026): Amazon trajo «Fi�dor M. Dostoievski», «Emily Bront�» y «Plat�n» y la cuarentena los
apartaba en cada carga, sin fin."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reading_normalizar as n  # noqa: E402

R = '�'


def libro(i, autor, descripcion=''):
    return {'id': f'isbn-{i}', 'titulo': f'Libro {i}', 'autores': [autor], 'descripcion_breve': descripcion}


class SustitucionTest(unittest.TestCase):
    def catalogo(self):
        return [libro(1, 'Fiódor M. Dostoievski'), libro(2, 'Fiódor Dostoievski'), libro(3, 'Fiodor Sologub'),
                libro(4, 'Emily Brontë'), libro(5, 'Platón')]

    def test_casos_reales_de_amazon(self):
        for roto, bueno in ((f'Fi{R}dor M. Dostoievski', 'Fiódor M. Dostoievski'), (f'Emily Bront{R}', 'Emily Brontë'),
                            (f'Plat{R}n', 'Platón')):
            nuevo = libro(9, roto, f'La república, de {roto}. Edición de Penguin Clásicos.')
            libros = self.catalogo() + [nuevo]
            self.assertGreater(n.normalizar(libros), 0)
            self.assertEqual(nuevo['autores'], [bueno])
            self.assertEqual(nuevo['descripcion_breve'], f'La república, de {bueno}. Edición de Penguin Clásicos.')
            self.assertEqual(n.normalizar(libros), 0, 'idempotente')

    def test_la_letra_ascii_no_cuenta(self):
        # «Fiodor» encaja letra a letra, pero la «�» nunca sustituye una letra ASCII: queda «Fiódor».
        nuevo = libro(9, f'Fi{R}dor Sologub')
        n.reparar_sustitucion(self.catalogo() + [nuevo])
        self.assertEqual(nuevo['autores'], ['Fiódor Sologub'])

    def test_sin_candidata_o_empate_no_se_adivina(self):
        for catalogo in ([], [libro(1, 'Ramón'), libro(2, 'Ramòn')]):
            nuevo = libro(9, f'Ram{R}n')
            self.assertEqual(n.reparar_sustitucion(catalogo + [nuevo]), 0)
            self.assertEqual(nuevo['autores'], [f'Ram{R}n'])

    def test_sustitucion_suelta_no_se_toca(self):
        nuevo = libro(9, 'Ana Gil', f'Precio {R} 20')
        self.assertEqual(n.reparar_sustitucion(self.catalogo() + [nuevo]), 0)

    def test_sin_roturas_no_cambia_nada(self):
        libros = self.catalogo()
        self.assertEqual(n.reparar_sustitucion(libros), 0)
        self.assertEqual(libros, self.catalogo())


if __name__ == '__main__':
    unittest.main()
