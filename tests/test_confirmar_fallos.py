"""Caso 12 de la revisión GPT (25/11): un fallo suelto se marcaba `FALLA: tests/...` y la carga paraba sin reintento.

Solo es FALLA (determinista) lo que falla dos veces seguidas sobre la misma revisión; lo demás sale INESTABLE.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import confirmar_fallos as cf  # noqa: E402


def determinista(salida):
    """La misma expresión que lee publish-radar-refresh.py para no reintentar."""
    texto = (ROOT / 'scripts/publish-radar-refresh.py').read_text(encoding='utf-8')
    patron = re.search(r"DETERMINISTA = re\.compile\(r'(.+?)', re\.M\)", texto).group(1)
    return [linea[linea.index('tests/'):] for linea in re.findall(patron, salida, re.M)]  # como firmas_deterministas


class ConfirmarFallosTest(unittest.TestCase):
    def correr(self, modo, ficheros, rcs):
        llamadas, salida = [], []

        def ejecutar(cmd):
            llamadas.append(cmd)
            return rcs[cmd[-1].replace('\\', '/').split('/')[-1]], 'traza'
        fallan, inestables = cf.confirmar(modo, ficheros, ejecutar, salida.append)
        return fallan, inestables, '\n'.join(salida), llamadas

    def test_el_plazo_vencido_mata_tambien_a_los_nietos(self):
        """R3-10 GPT: un contrato colgado no deja vivo a lo que lanzó (servidor, navegador) para los siguientes."""
        import os
        import subprocess
        import tempfile
        import time
        from unittest.mock import patch

        def vivo(pid):
            if os.name == 'nt':
                fuera = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/NH'], capture_output=True, text=True).stdout
                return str(pid) in fuera
            try:
                os.kill(pid, 0)
            except OSError:
                return False
            return True

        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / 'nieto.pid'
            nieto = f'import os,time; open({str(pidfile)!r},"w").write(str(os.getpid())); time.sleep(60)'
            hijo = f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",{nieto!r}]); time.sleep(60)'
            with patch.object(cf, 'TIEMPO_S', 3):
                rc, salida = cf.ejecutar([sys.executable, '-c', hijo])
            self.assertEqual(rc, 124, salida)
            pid = int(pidfile.read_text())
            for _ in range(20):
                if not vivo(pid):
                    break
                time.sleep(0.25)
            self.assertFalse(vivo(pid), 'el nieto sobrevivió al plazo vencido')

    def test_un_fallo_que_no_se_repite_no_es_determinista(self):
        fallan, inestables, salida, _ = self.correr('script', ['tests/test-red.py', 'tests/test-roto.py'],
                                                    {'test-red.py': 0, 'test-roto.py': 1})
        self.assertEqual((fallan, inestables), (['tests/test-roto.py'], ['tests/test-red.py']))
        self.assertEqual(determinista(salida), ['tests/test-roto.py'])
        self.assertIn('INESTABLE: tests/test-red.py', salida)

    def test_modos_y_rc5(self):
        fallan, inestables, _, llamadas = self.correr('unittest', ['tests/test_x.py', 'tests/test_x.py', ''],
                                                      {'test_x.py': 5})
        self.assertEqual((fallan, inestables), ([], ['tests/test_x.py']), 'rc 5 pasa y no se repite dos veces')
        self.assertEqual(llamadas[0][1:], ['-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_x.py'])
        self.assertEqual(cf.orden('node', 'tests/a.mjs'), ['node', 'tests/a.mjs'])
        self.assertEqual(self.correr('script', ['tests/test-y.py'], {'test-y.py': 5})[0], ['tests/test-y.py'])

    def test_sin_lista_sale_bien(self):
        self.assertEqual(cf.main(['--modo', 'node', str(ROOT / 'no-existe.txt')]), 0)

    def test_la_puerta_no_marca_falla_sin_repetir(self):
        """Ningún paso de la puerta ni el runner compartido (que también usa main-contratos.yml) imprime `FALLA:`
        por su cuenta: todos pasan por confirmar_fallos."""
        gate = '\n'.join((ROOT / r).read_text(encoding='utf-8') for r in (
            '.github/workflows/required-merge-gate.yml', 'scripts/run-python-contracts.sh', 'scripts/run-node-contracts.sh'))
        self.assertNotIn("sed 's/^/FALLA: /'", gate)
        self.assertNotIn('echo "FALLA: ', gate)
        for trozo in ('tipo=script', 'tipo=unittest', 'confirmar_fallos.py --modo "$tipo"', 'confirmar_fallos.py --modo node'):
            self.assertIn(trozo, gate)


if __name__ == '__main__':
    unittest.main()
