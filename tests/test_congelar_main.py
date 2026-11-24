"""Congelación de main durante la carga (scripts/congelar_main.py): espera, exenciones y fallos abiertos."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import congelar_main as c  # noqa: E402


def consulta_de(*turnos):
    """Cada llamada de la ronda n devuelve los estados del turno n (repite el último)."""
    estado = {'ronda': 0, 'llamadas': 0}

    def consulta(flujo):
        estado['llamadas'] += 1
        if estado['llamadas'] > 2:  # dos flujos por ronda
            estado['llamadas'] = 1
            estado['ronda'] += 1
        turno = turnos[min(estado['ronda'], len(turnos) - 1)]
        return [{'databaseId': 7, 'status': turno.get(flujo, 'completed'), 'createdAt': 'x', 'event': 'schedule'}]
    return consulta


class Reloj:
    def __init__(self):
        self.t = 0

    def dormir(self, s):
        self.t += s

    def ahora(self):
        return self.t


class CongelarMainTest(unittest.TestCase):
    def esperar(self, consulta, head_ref='fix/algo', etiquetas='', tope_s=1000):
        reloj = Reloj()
        salida = []
        rc = c.esperar(head_ref, etiquetas, consulta, reloj.dormir, reloj.ahora, tope_s, 10, salida.append)
        return rc, reloj.t, '\n'.join(salida)

    def test_libre_pasa_enseguida(self):
        rc, t, salida = self.esperar(consulta_de({}))
        self.assertEqual((rc, t), (0, 0))
        self.assertIn('Main libre', salida)

    def test_espera_a_que_acabe_la_carga_y_luego_pasa(self):
        rc, t, salida = self.esperar(consulta_de({'reading-catalogue-sync.yml': 'in_progress'},
                                                 {'reading-catalogue-sync.yml': 'in_progress'}, {}))
        self.assertEqual(rc, 0)
        self.assertEqual(t, 20, 'duerme dos rondas y la tercera la encuentra libre')
        self.assertIn('Main congelado: reading-catalogue-sync.yml', salida)

    def test_el_refresco_del_radar_tambien_congela(self):
        _, t, salida = self.esperar(consulta_de({'radar-clock-refresh.yml': 'queued'}, {}))
        self.assertEqual(t, 10)
        self.assertIn('radar-clock-refresh.yml', salida)

    def test_la_pr_de_la_carga_y_las_de_revision_no_esperan(self):
        ocupada = consulta_de({'reading-catalogue-sync.yml': 'in_progress'})
        for rama in ('automation/reading-catalogue-2026-11-24', 'automation/radar-clock-refresh', 'revision/paquete-06'):
            rc, t, _ = self.esperar(ocupada, head_ref=rama)
            self.assertEqual((rc, t), (0, 0), rama)

    def test_etiqueta_de_emergencia(self):
        ocupada = consulta_de({'reading-catalogue-sync.yml': 'in_progress'})
        self.assertEqual(self.esperar(ocupada, etiquetas='bug, sin-congelar')[:2], (0, 0))
        self.assertEqual(self.esperar(ocupada, etiquetas='sin-congelar-no')[0], 0)  # no exenta, pero acaba por el tope

    def test_si_no_se_puede_mirar_no_congela(self):
        def roto(flujo):
            raise subprocess.CalledProcessError(1, 'gh')
        rc, t, salida = self.esperar(roto)
        self.assertEqual((rc, t), (0, 0))
        self.assertIn('No se pudo mirar', salida)

    def test_tope_agotado_abre_con_aviso(self):
        rc, t, salida = self.esperar(consulta_de({'reading-catalogue-sync.yml': 'in_progress'}), tope_s=50)
        self.assertEqual((rc, t), (0, 50))
        self.assertIn('Congelación agotada', salida)

    def test_ejecucion_terminada_no_cuenta(self):
        self.assertEqual(c.activas(consulta_de({'reading-catalogue-sync.yml': 'completed'})), [])


if __name__ == '__main__':
    unittest.main()
