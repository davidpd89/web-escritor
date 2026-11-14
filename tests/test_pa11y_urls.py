"""Pa11y completo: cabe en el límite de los jobs aunque el catálogo crezca, sin dejar páginas fuera para siempre."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('pa11y_urls', Path(__file__).resolve().parents[1] / 'scripts/pa11y_urls.py')
pa11y = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pa11y)

LIBROS = [f'/recomendaciones/libros/libro-{i}/' for i in range(3949)]
SUELTAS = ['/', '/cuaderno/', '/recomendaciones/', '/atlas-literario/praga/', '/autor.html']
RUTAS = SUELTAS + LIBROS + [f'/recomendaciones/autores/a-{i}/' for i in range(799)]


class Pa11yUrls(unittest.TestCase):
    def test_el_catalogo_grande_cabe_en_los_shards(self):
        elegidas = pa11y.elegir(RUTAS, 0)
        self.assertLessEqual(len(elegidas), 300)
        # 14/11: 1.290 URL por shard tardaban 30 min (~1,4 s cada una); por debajo de 150 sobra margen.
        self.assertLessEqual(max(len(pa11y.shard(elegidas, i, 4)) for i in range(4)), 150)

    def test_las_paginas_sueltas_entran_siempre(self):
        for dia in range(5):
            self.assertTrue(set(SUELTAS) <= set(pa11y.elegir(RUTAS, dia)))

    def test_la_rotacion_recorre_todas_las_fichas(self):
        vistas = set()
        for dia in range(40):
            vistas.update(pa11y.elegir(RUTAS, dia))
        self.assertEqual(vistas, set(RUTAS))

    def test_los_shards_reparten_sin_huecos_ni_repetidos(self):
        elegidas = pa11y.elegir(RUTAS, 3)
        partes = [pa11y.shard(elegidas, i, 4) for i in range(4)]
        self.assertEqual(sorted(sum(partes, [])), sorted(elegidas))

    def test_familia_agrupa_por_plantilla(self):
        self.assertEqual(pa11y.familia('/recomendaciones/libros/x/'), '/recomendaciones/libros/*/')
        self.assertEqual(pa11y.familia('/cuaderno/'), '/cuaderno/')
        self.assertEqual(pa11y.familia('/'), '/')


if __name__ == '__main__':
    unittest.main()
