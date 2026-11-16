"""D1 (R4-4): el día de la web es el del despliegue (Madrid), no el de los datos del último commit.

Antes, `data_anchor` salía solo de las fechas de los datos: una noche sin carga dejaba el portal, los próximos
lanzamientos y los descuentos en el día anterior. Ahora `--hoy` o CATALOGO_HOY mandan, y el despliegue los fija
con la fecha de Madrid y se dispara también al cambiar el día.
"""
import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
_spec = importlib.util.spec_from_file_location('build_reading_catalogue', ROOT / 'scripts/build-reading-catalogue.py')
b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b)

LIBROS = [{'titulo': 'Uno', 'fecha_actualizacion': '2026-11-15', 'fecha_publicacion': '2026-11-17'}]


class DiaDelDespliegueTest(unittest.TestCase):
    def tearDown(self):
        b.HOY = None

    def test_sin_dia_manda_la_fecha_de_los_datos(self):
        self.assertEqual(b.data_anchor(LIBROS), '2026-11-15')

    def test_el_dia_del_despliegue_manda_sobre_los_datos(self):
        b.HOY = '2026-11-17'
        self.assertEqual(b.data_anchor(LIBROS), '2026-11-17')

    def test_un_libro_deja_de_ser_proximo_el_dia_que_sale(self):
        self.assertEqual(len(b.upcoming_books(LIBROS)), 1)
        b.HOY = '2026-11-17'
        self.assertEqual(b.upcoming_books(LIBROS), [])

    def test_argumento_y_entorno(self):
        self.assertIsNone(b.dia_del_despliegue(None, {}))
        self.assertEqual(b.dia_del_despliegue(None, {'CATALOGO_HOY': '2026-11-17'}), '2026-11-17')
        self.assertEqual(b.dia_del_despliegue(date(2026, 11, 18), {'CATALOGO_HOY': '2026-11-17'}), '2026-11-18')
        with self.assertRaises(ValueError):
            b.dia_del_despliegue(None, {'CATALOGO_HOY': '17/11/2026'})  # nunca publicar otro día por error


class DespliegueTest(unittest.TestCase):
    def setUp(self):
        self.wf = yaml.safe_load((ROOT / '.github/workflows/deploy-pages.yml').read_text(encoding='utf-8'))

    def test_se_publica_al_cambiar_el_dia_de_madrid(self):
        on = self.wf.get('on', self.wf.get(True))
        crons = {c['cron'] for c in on.get('schedule', [])}
        self.assertEqual(crons, {'5 22 * * *', '5 23 * * *'})  # 00:05 Madrid en verano y en invierno
        dia = self.wf['jobs']['dia']['steps'][0]['run']
        self.assertIn('TZ=Europe/Madrid date +%F', dia)
        self.assertEqual(self.wf['jobs']['build']['if'], "needs.dia.outputs.seguir == 'true'")

    def test_lo_generado_se_rehace_con_el_dia_antes_de_publicar(self):
        pasos = self.wf['jobs']['build']['steps']
        nombres = [p.get('name', '') for p in pasos]
        rehacer = nombres.index('Rehacer lo generado con el día de hoy')
        self.assertLess(nombres.index('Materializar generados'), rehacer)
        self.assertLess(rehacer, nombres.index('Build public artifact (allowlist-first)'))
        self.assertEqual(pasos[rehacer]['env']['CATALOGO_HOY'], '${{ needs.dia.outputs.hoy }}')
        # la cadena acaba en `npx --no-install pagefind`: Node y el lockfile instalados antes de rehacer
        self.assertLess(nombres.index('Set up Node'), rehacer)
        npm = nombres.index('Instalar Pagefind (lockfile)')
        self.assertLess(npm, rehacer)
        self.assertIn('npm ci', pasos[npm]['run'])


if __name__ == '__main__':
    unittest.main()
