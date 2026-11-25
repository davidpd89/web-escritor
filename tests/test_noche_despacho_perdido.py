"""Despacho perdido: la cadena anota su pendiente y `gh workflow run` falla (25/11, caso 14 de la revisión GPT).

Antes el juez (job clock) veía la última carga publicada y decía «no carga» sin mirar el pendiente: el job intake nunca
llegaba a `abrir`, que sí lo habría heredado, y el resto de la noche se perdía.
"""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import noche  # noqa: E402

T0 = datetime(2026, 11, 25, 0, 21, tzinfo=timezone.utc)


class DespachoPerdidoTest(unittest.TestCase):
    def carga(self, libro, t, run, resultado, motivo='cron'):
        cargar, porque, libro = noche.abrir(libro, t, run, 1, 'sha', motivo)
        self.assertTrue(cargar, porque)
        return noche.cerrar(libro, t + timedelta(minutes=80), run, 1, resultado)

    def test_cadena_sin_despacho_la_hereda_el_siguiente_reloj(self):
        libro = self.carga(None, T0, 1, 'success')
        libro = noche.pendiente(libro, T0 + timedelta(minutes=81), 'cadena')  # el dispatch posterior falla
        reloj = T0 + timedelta(hours=2)
        cargar, porque = noche.decidir(libro, reloj)
        self.assertTrue(cargar, porque)
        cargar, porque, libro = noche.abrir(libro, reloj, 2, 1, 'sha', 'cron')
        self.assertTrue(cargar, porque)
        self.assertIn('desalojado', porque)
        self.assertFalse(noche.resumen(libro, reloj)['pendientes'])  # consumido: el despacho que llegue tarde no repite
        cargar, _, _ = noche.abrir(noche.cerrar(libro, reloj + timedelta(minutes=80), 2, 1, 'success'),
                                   reloj + timedelta(minutes=81), 3, 1, 'sha', 'cadena')
        self.assertFalse(cargar)

    def test_reintento_sin_despacho_tambien(self):
        libro = self.carga(None, T0, 1, 'failure')
        libro = noche.pendiente(libro, T0 + timedelta(minutes=81), 'reintento')
        self.assertTrue(noche.decidir(libro, T0 + timedelta(hours=2))[0])

    def test_el_tope_de_fallidos_manda_sobre_el_pendiente(self):
        libro = None
        for n in range(noche.MAX_FALLIDOS):
            libro = self.carga(libro, T0 + timedelta(hours=2 * n), n + 1, 'failure')
        libro = noche.pendiente(libro, T0 + timedelta(hours=7), 'reintento')
        self.assertFalse(noche.decidir(libro, T0 + timedelta(hours=7, minutes=5))[0])

    def test_sin_pendiente_una_noche_publicada_sigue_sin_cargar(self):
        libro = self.carga(None, T0, 1, 'success')
        self.assertFalse(noche.decidir(libro, T0 + timedelta(hours=2))[0])


if __name__ == '__main__':
    unittest.main()
