"""Clave única de orden por fecha: nunca lanza, aunque la fecha sea absurda."""
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fecha_cercana as fc  # noqa: E402

HOY = date(2026, 11, 16)


class Cercania(unittest.TestCase):
    def test_orden_hoy_futuro_pasado_ilegible(self):
        fechas = ['2026-11-10', 'roto', '2026-11-17', '2027-01-01', '2026-11']
        self.assertEqual(sorted(fechas, key=lambda f: fc.cercania(f, HOY)),
                         ['2026-11', '2026-11-17', '2027-01-01', '2026-11-10', 'roto'])

    def test_fechas_en_el_limite_del_calendario_no_paran_el_orden(self):
        # «9999-12» desbordaba date.max al calcular el último día del mes (OverflowError) y abortaba sorted.
        for f in ('9999-12', '9999-12-31', '9999', '0001-01', '0-1', '10000-01'):
            fc.cercania(f, HOY)
        self.assertEqual(fc.periodo('9999-12'), (date(9999, 12, 1), date(9999, 12, 31)))


if __name__ == '__main__':
    unittest.main()
