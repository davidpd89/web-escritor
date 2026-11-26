"""Caso 7 de la ronda 2 GPT (25/11): la huella que bloquea «mismo fallo con lo mismo» cubre todo lo que la carga lee.

Con solo scripts/tests/qa/.github, un arreglo de datos o de configuración en main no cambiaba la huella y la noche
seguía bloqueada por un fallo que ya no se daría. El ruido nocturno (métricas de redes, informes) no la cambia."""
import os
import subprocess
import sys
import tempfile
import unittest.mock  # también enlaza `unittest`
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import noche  # noqa: E402


class Huella(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.git('init', '-q')
        for ruta in ('scripts/a.py', 'data/libros.json', 'schemas/s.json', '.ci/informe.md',
                     'redes-sociales/social-metrics.json'):
            self.escribe(ruta, 'v1')
        self.commit()
        cwd = os.getcwd()
        os.chdir(self.raiz)
        self.addCleanup(os.chdir, cwd)

    def git(self, *args):
        subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', *args], cwd=self.raiz, check=True,
                       capture_output=True)

    def escribe(self, ruta, texto):
        (self.raiz / ruta).parent.mkdir(parents=True, exist_ok=True)
        (self.raiz / ruta).write_text(texto, encoding='utf-8')

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '-qm', 'x')

    def cambia(self, ruta):
        antes = noche._codigo()
        self.escribe(ruta, 'v2')
        self.commit()
        return antes != noche._codigo()

    def test_un_arreglo_de_datos_desbloquea(self):
        self.assertTrue(self.cambia('data/libros.json'))
        self.assertTrue(self.cambia('schemas/s.json'))
        self.assertTrue(self.cambia('scripts/a.py'))

    def test_el_ruido_de_la_noche_no(self):
        self.assertFalse(self.cambia('redes-sociales/social-metrics.json'))
        self.assertFalse(self.cambia('.ci/informe.md'))

    def test_sin_git_no_bloquea(self):
        with unittest.mock.patch.object(noche.subprocess, 'run', side_effect=OSError):
            self.assertIsNone(noche._codigo())


if __name__ == '__main__':
    unittest.main()
