import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('carga_en_curso', ROOT / 'scripts/carga_en_curso.py')
carga = importlib.util.module_from_spec(spec)
spec.loader.exec_module(carga)


class CargaEnCursoTest(unittest.TestCase):
    def test_libre_si_todo_termino_y_no_hay_pr_de_datos(self):
        self.assertEqual(carga.motivos([{'databaseId': 1, 'status': 'completed', 'createdAt': 'x'}],
                                       [{'number': 9, 'headRefName': 'fix/algo'}]), [])

    def test_ejecucion_sin_terminar_o_pr_de_datos_abierta_cuentan(self):
        r = carga.motivos([{'databaseId': 2, 'status': 'in_progress', 'createdAt': 'x'},
                           {'databaseId': 3, 'status': 'queued', 'createdAt': 'y'}],
                          [{'number': 7, 'headRefName': 'automation/reading-catalogue-2026-11-23-5-r2'}])
        self.assertEqual(len(r), 3)

    def test_la_pr_de_textos_propios_no_es_una_carga(self):
        self.assertEqual(carga.motivos([], [{'number': 5, 'headRefName': 'automation/reading-catalogue-textos-2026-11-18-005202'}]), [])


if __name__ == '__main__':
    unittest.main()
