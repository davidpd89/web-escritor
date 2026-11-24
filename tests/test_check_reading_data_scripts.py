"""La puerta de datos de la carga también corre los contratos en script (tests/test-*.py) que leen lo generado.

23/11: un título de ficha de 206 caracteres solo lo rechazaba tests/test-page-order.py, que vivía únicamente en la
puerta de la PR; la carga lo descubrió 2,5 h después de consultar las fuentes. Aquí se vigila que la selección es
automática (entra todo script que lea el catálogo o lo generado) y que su lista de excepciones no se pudre.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_reading_data', ROOT / 'scripts/check-reading-data.py')
puerta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(puerta)


class ScriptsDeDatosTest(unittest.TestCase):
    def test_el_orden_de_paginas_entra_y_el_codigo_pesado_no(self):
        elegidos = puerta.script_contracts()
        self.assertIn('test-page-order.py', elegidos)
        self.assertNotIn('test-reading-publication.py', elegidos)

    def test_las_excepciones_existen_y_leerian_datos(self):
        """Una excepción que ya no existe, o que ya no lee datos, sobra: se quita de la lista."""
        for nombre in puerta.SCRIPTS_CODIGO:
            ruta = ROOT / 'tests' / nombre
            self.assertTrue(ruta.is_file(), nombre)
            texto = ruta.read_text(encoding='utf-8', errors='ignore')
            self.assertTrue(any(r in texto for r in puerta.SCRIPT_RASTROS), f'{nombre} ya no lee datos: quitarlo')

    def test_un_script_que_falla_o_se_cuelga_se_informa(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / 'tests').mkdir()
            (raiz / 'tests' / 'test-bien.py').write_text('print("ok")\n# page-order\n', encoding='utf-8')
            (raiz / 'tests' / 'test-mal.py').write_text('# page-order\nassert False, "titulo de 206"\n', encoding='utf-8')
            (raiz / 'tests' / 'test-otro.py').write_text('assert False\n', encoding='utf-8')  # no lee datos: no entra
            self.assertEqual(puerta.script_contracts(raiz), ['test-bien.py', 'test-mal.py'])
            fallos = puerta.run_scripts(raiz)
            self.assertEqual([f['test'] for f in fallos], ['tests/test-mal.py'])
            self.assertIn('titulo de 206', fallos[0]['texto'])


if __name__ == '__main__':
    unittest.main()
