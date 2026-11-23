"""El canal de libros de los contratos funciona también para los contratos en script y para el slug de la ficha."""
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
import reading_quarantine  # noqa: E402

spec = importlib.util.spec_from_file_location('check_reading_data', ROOT / 'scripts/check-reading-data.py')
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

SCRIPT = '''from contrato_libros import incumplen
incumplen("regla de prueba", {"isbn-1": "mal"})
'''


class CanalLibrosTest(unittest.TestCase):
    def test_un_contrato_en_script_nombra_sus_libros_a_la_puerta(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            (raiz / 'tests').mkdir()
            shutil.copy(ROOT / 'tests/contrato_libros.py', raiz / 'tests/contrato_libros.py')
            (raiz / 'tests/test-falso.py').write_text(SCRIPT, encoding='utf-8')
            (raiz / 'tests/test-bien.py').write_text('print("ok")\n', encoding='utf-8')
            fallos = check.run_scripts(raiz, names=['test-falso.py', 'test-bien.py'], workers=1)
        self.assertEqual(len(fallos), 1)
        self.assertEqual(fallos[0]['libros'], {'isbn-1': 'mal'})
        self.assertEqual(fallos[0]['regla'], 'regla de prueba')

    def test_la_cuarentena_aparta_por_declaracion_de_un_script(self):
        data = {'libros': [{'id': 'isbn-1', 'slug': 's-1', 'isbn13': '9780000000001'}]}
        fallo = {'test': 'tests/test-falso.py', 'texto': '', 'regla': 'r', 'libros': {'isbn-1': 'mal'}}
        self.assertEqual(list(reading_quarantine.flagged_books([fallo], data)), ['isbn-1'])

    def test_un_fallo_que_cita_la_ruta_de_la_ficha_aparta_el_libro_con_slug_distinto(self):
        data = {'libros': [{'id': 'isbn-9780000000001', 'slug': 'titulo-raro-9780000000001', 'isbn13': '9780000000001'},
                           {'id': 'isbn-9780000000002', 'slug': 'otro-libro', 'isbn13': '9780000000002'}]}
        texto = 'AssertionError: recomendaciones\\libros\\titulo-raro-9780000000001\\index.html: editorial esperada'
        out = reading_quarantine.flagged_books([{'test': 'tests/test-x.py', 'texto': texto}], data)
        self.assertEqual(list(out), ['isbn-9780000000001'])


if __name__ == '__main__':
    unittest.main()
