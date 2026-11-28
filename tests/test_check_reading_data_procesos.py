"""La puerta de datos reparte sus contratos unittest en procesos, un módulo por proceso, y no pierde nada al juntar.

28/11: en un solo proceso tardaba 17-18 min por pasada (119 contratos) y la carga la repite en cada vuelta de la
cuarentena. Aquí se prueba con módulos sintéticos en un repo temporal que el reparto conserva los libros que declara
cada contrato, que un módulo que no carga o se cuelga cuenta como fallo sin libros (la carga no lo da por bueno) y
que `--solo` limita la pasada a lo que se pide.
"""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_reading_data', ROOT / 'scripts/check-reading-data.py')
puerta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(puerta)

BIEN = '''import unittest
class T(unittest.TestCase):
    def test_a(self): pass
    def test_b(self): pass
'''
LIBROS = '''import unittest
from contrato_libros import incumplen
class T(unittest.TestCase):
    def test_libros(self):
        incumplen("regla sintética", {"isbn-9780000000001": "mal"})
    def test_sin_libros(self):
        self.assertEqual(1, 2)
'''
COLGADO = '''import time, unittest
class T(unittest.TestCase):
    def test_eterno(self): time.sleep(60)
'''


class ProcesosTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / 'scripts').mkdir()
        (self.root / 'tests').mkdir()
        shutil.copy(ROOT / 'scripts/check-reading-data.py', self.root / 'scripts/check-reading-data.py')
        shutil.copy(ROOT / 'tests/contrato_libros.py', self.root / 'tests/contrato_libros.py')
        for name, body in (('test_bien', BIEN), ('test_libros', LIBROS), ('test_colgado', COLGADO)):
            (self.root / 'tests' / f'{name}.py').write_text(body, encoding='utf-8')

    def test_un_modulo_por_proceso_en_el_orden_de_la_lista(self):
        self.assertEqual(puerta.grupos(['m.A.test_1', 'n', 'm.A.test_2', 'o.B']),
                         [['m.A.test_1', 'm.A.test_2'], ['n'], ['o.B']])

    def test_los_procesos_conservan_los_libros_declarados_y_cuentan_todo(self):
        corridos, fallos = puerta.run_units(['test_bien', 'test_libros'], workers=2, root=self.root)
        self.assertEqual(corridos, 4)
        por_test = {f['test'].rsplit('.', 1)[-1]: f for f in fallos}
        self.assertEqual(sorted(por_test), ['test_libros', 'test_sin_libros'])
        self.assertEqual(por_test['test_libros']['libros'], {'isbn-9780000000001': 'mal'})
        self.assertEqual(por_test['test_libros']['regla'], 'regla sintética')
        self.assertNotIn('libros', por_test['test_sin_libros'])

    def test_un_modulo_que_no_carga_es_un_fallo_sin_libros(self):
        corridos, fallos = puerta.run_units(['test_no_existe', 'test_bien'], workers=2, root=self.root)
        self.assertEqual(corridos, 3)  # unittest cuenta el import fallido como un test con error
        self.assertEqual(len(fallos), 1)
        self.assertIn('test_no_existe', fallos[0]['test'])
        self.assertNotIn('libros', fallos[0])

    def test_un_modulo_colgado_no_se_come_la_carga(self):
        with mock.patch.object(puerta, 'GRUPO_LIMITE', 3):
            corridos, fallos = puerta.run_units(['test_colgado', 'test_bien'], workers=2, root=self.root)
        self.assertEqual(corridos, 2)
        self.assertEqual(fallos, [{'test': 'test_colgado', 'texto': 'sin terminar en 3 s'}])

    def test_solo_separa_unittest_de_scripts_y_sin_solo_va_todo(self):
        self.assertEqual(puerta.elegidos(['--solo', 'a.B.test_c,tests/test-x.py', '--fallos', 'f']),
                         (['a.B.test_c'], ['test-x.py']))
        todos, scripts = puerta.elegidos(['--fallos', 'f'])
        self.assertEqual(todos, puerta.contracts())
        self.assertIsNone(scripts)

    def test_main_deja_el_json_de_fallos_que_lee_la_carga(self):
        out = self.root / 'f.json'
        with mock.patch.object(puerta, 'ROOT', self.root):
            code = puerta.main(['--solo', 'test_bien,test_libros', '--fallos', str(out)])
        self.assertEqual(code, 1)
        fallos = json.loads(out.read_text(encoding='utf-8'))
        self.assertEqual(sum(1 for f in fallos if f.get('libros')), 1)


if __name__ == '__main__':
    unittest.main()
