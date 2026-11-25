"""Caso 2 de la revisión GPT (25/11): con main en rojo, la carga gastaba ~2 h para caer en la puerta con el mismo test.

scripts/main_verde.py espera a main-contratos.yml si está en curso y, si está rojo y el fallo se repite sobre el HEAD
de la carga, para antes de consultar las fuentes con la firma anotada para el libro de la noche.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import main_verde as mv  # noqa: E402
import noche  # noqa: E402


def run(i, status='completed', conclusion='success', creado=None):
    return {'databaseId': i, 'status': status, 'conclusion': conclusion, 'headSha': f'{i:040d}',
            'createdAt': creado or f'2026-11-25T0{i}:00:00Z'}


class Reloj:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def dormir(self, s):
        self.t += s


class MainVerdeTest(unittest.TestCase):
    def comprobar(self, secuencia, firmas=(), rcs=None, entorno=None, existen=None):
        reloj, salida, llamadas = Reloj(), [], []
        estados = iter(secuencia)
        ultimo = [None]

        def consulta():
            ultimo[0] = next(estados, ultimo[0])
            return ultimo[0]

        def ejecutar(cmd):
            llamadas.append(cmd)
            return (rcs or {}).get(Path(cmd[-1]).name, 1), 'traza'
        rc = mv.comprobar(consulta, lambda _id: list(firmas), ejecutar, reloj.dormir, reloj, salida.append,
                          entorno if entorno is not None else {},
                          existe=(lambda f: f in existen) if existen is not None else (lambda f: True))
        return rc, '\n'.join(salida), llamadas, reloj.t

    def test_main_rojo_de_verdad_para_la_carga_y_lo_anota_para_el_libro(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, salida, llamadas, _ = self.comprobar(
                [[run(2, conclusion='failure'), run(1)]], firmas=['tests/test_roto.py', 'tests/test-inestable.py'],
                rcs={'test-inestable.py': 0}, entorno={'RUNNER_TEMP': tmp})
            self.assertEqual(rc, 1)
            self.assertEqual(len(llamadas), 2, 'solo repite los contratos rojos, no la suite')
            anotado = json.loads(Path(tmp, noche.FALLO).read_text(encoding='utf-8'))
            self.assertEqual(anotado['clase'], noche.DETERMINISTA)
            self.assertIn('tests/test_roto.py', anotado['firma'])
            self.assertNotIn('test-inestable', anotado['firma'])
            self.assertIn('Main en rojo', salida)

    def test_un_contrato_renombrado_no_para_la_carga(self):
        """Caso 8 de la ronda 2: el rojo era de tests/test-viejo.py, que en este HEAD ya no existe."""
        rc, salida, llamadas, _ = self.comprobar([[run(2, conclusion='failure')]], firmas=['tests/test-viejo.py'],
                                                 existen=set())
        self.assertEqual(rc, 0)
        self.assertEqual(llamadas, [], 'no se ejecuta un fichero que no está')
        self.assertIn('ya no existen', salida)

    def test_el_que_sigue_existiendo_se_repite(self):
        rc, _, llamadas, _ = self.comprobar([[run(2, conclusion='failure')]],
                                            firmas=['tests/test-viejo.py', 'tests/test_roto.py'],
                                            existen={'tests/test_roto.py'})
        self.assertEqual(rc, 1)
        self.assertEqual(len(llamadas), 1)

    def test_si_ya_pasa_sobre_este_head_sigue(self):
        rc, salida, _, _ = self.comprobar([[run(2, conclusion='failure')]], firmas=['tests/test_roto.py'],
                                          rcs={'test_roto.py': 0})
        self.assertEqual(rc, 0)
        self.assertIn('ya pasan', salida)

    def test_espera_a_la_comprobacion_en_curso(self):
        rc, _, llamadas, t = self.comprobar([[run(3, status='in_progress', conclusion=''), run(2, conclusion='failure')],
                                             [run(3, status='in_progress', conclusion='')],
                                             [run(3), run(2, conclusion='failure')]], firmas=['tests/test_roto.py'])
        self.assertEqual((rc, llamadas, t), (0, [], 2 * mv.CADA_S), 'la reparación en curso salió verde')

    def test_la_espera_tiene_tope(self):
        rc, salida, _, t = self.comprobar([[run(3, status='queued', conclusion='')]])
        self.assertEqual(rc, 0)
        self.assertGreaterEqual(t, mv.ESPERA_MIN * 60)
        self.assertLess(t, mv.ESPERA_MIN * 60 + 2 * mv.CADA_S)

    def test_las_canceladas_no_cuentan(self):
        self.assertEqual(mv.estado([run(3, conclusion='cancelled'), run(2, conclusion='failure'), run(1)])[0], 'rojo')
        self.assertEqual(mv.estado([run(3, conclusion='cancelled'), run(2)])[0], 'verde')
        self.assertEqual(mv.estado([])[0], 'desconocido')

    def test_falla_abierto(self):
        def rota():
            raise RuntimeError('gh caído')
        self.assertEqual(mv.comprobar(rota, imprimir=lambda *_: None, entorno={}), 0)
        self.assertEqual(self.comprobar([[run(2, conclusion='failure')]], firmas=[])[0], 0, 'sin FALLA legible')
        self.assertEqual(self.comprobar([[]])[0], 0, 'sin el flujo')

    def test_modos(self):
        self.assertEqual([mv.modo_de(f) for f in ('tests/test-a.py', 'tests/test_b.py', 'tests/c.mjs')],
                         ['script', 'unittest', 'node'])

    def test_la_firma_bloquea_el_reintento_con_el_mismo_codigo(self):
        """La firma que deja main_verde la lee `cerrar` y la respeta el reintento, como la del publicador."""
        with tempfile.TemporaryDirectory() as tmp:
            mv.anotar(['tests/test_roto.py'], {'RUNNER_TEMP': tmp})
            import os
            viejo = os.environ.get('RUNNER_TEMP')
            os.environ['RUNNER_TEMP'] = tmp
            try:
                clase, firma = noche._fallo_anotado()
            finally:
                if viejo is None:
                    os.environ.pop('RUNNER_TEMP')
                else:
                    os.environ['RUNNER_TEMP'] = viejo
        self.assertEqual((clase, firma), (noche.DETERMINISTA, 'main rojo: tests/test_roto.py'))

    def test_cableado_antes_de_consultar_las_fuentes(self):
        sync = (ROOT / '.github/workflows/reading-catalogue-sync.yml').read_text(encoding='utf-8')
        self.assertIn('python scripts/main_verde.py', sync)
        orden = [sync.index(x) for x in ('noche.py abrir', 'npm ci', 'main_verde.py', 'refresh-reading-catalogue.py --publish')]
        self.assertEqual(orden, sorted(orden))
        paso = sync.split('name: Main must pass its contracts', 1)[1].split('- name:', 1)[0]
        self.assertIn("steps.libro.outputs.cargar == 'true'", paso)
        self.assertIn('!inputs.dry_run', paso)
        self.assertIn('GH_TOKEN', paso)


if __name__ == '__main__':
    unittest.main()
