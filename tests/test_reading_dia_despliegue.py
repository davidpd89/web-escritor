"""D1 (R4-4): el día de la web es el del despliegue (Madrid), no el de los datos del último commit.

Antes, `data_anchor` salía solo de las fechas de los datos: una noche sin carga dejaba el portal, los próximos
lanzamientos y los descuentos en el día anterior. Ahora `--hoy` o CATALOGO_HOY mandan, y el despliegue los fija
con la fecha de Madrid y se dispara también al cambiar el día.
"""
import ast
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


RELOJ = {('date', 'today'), ('datetime', 'now'), ('datetime', 'today'), ('datetime', 'utcnow'), ('time', 'time'),
         ('time', 'localtime'), ('time', 'gmtime'), ('time', 'strftime'), ('time', 'time_ns')}


def _cadena_de_construccion():
    """Los builders de materializar y sus módulos locales importados, transitivamente."""
    import materializar_generados as m
    vistos, cola = set(), [ROOT / 'scripts' / builder[0] for builder in m.BUILDERS]
    while cola:
        f = cola.pop()
        if f in vistos or not f.exists():
            continue
        vistos.add(f)
        for n in ast.walk(ast.parse(f.read_text(encoding='utf-8'))):
            nombres = ([a.name for a in n.names] if isinstance(n, ast.Import)
                       else [n.module] if isinstance(n, ast.ImportFrom) and n.module and n.level == 0 else [])
            cola.extend(ROOT / 'scripts' / (x.split('.')[0] + '.py') for x in nombres)
    return vistos


class UnSoloRelojTest(unittest.TestCase):
    """R5-13 (hallazgo 24): ninguna pieza de la cadena lee el reloj por su cuenta; solo site_clock.site_today, que
    obedece a CATALOGO_HOY. Si no, la CI con «mañana» y el deploy cruzando la medianoche mezclarían días."""

    def test_la_cadena_solo_lee_el_reloj_en_site_today(self):
        modulos = _cadena_de_construccion()
        self.assertIn(ROOT / 'scripts/build-reading-catalogue.py', modulos)
        self.assertIn(ROOT / 'scripts/site_clock.py', modulos)
        lecturas = []
        for f in modulos:
            arbol = ast.parse(f.read_text(encoding='utf-8'))
            permitidas = set()
            if f.name == 'site_clock.py':
                fn = next(n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == 'site_today')
                permitidas = {id(n) for n in ast.walk(fn)}
            for n in ast.walk(arbol):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and id(n) not in permitidas:
                    base = n.func.value
                    nombre = base.attr if isinstance(base, ast.Attribute) else getattr(base, 'id', None)
                    if (nombre, n.func.attr) in RELOJ:
                        lecturas.append(f'{f.relative_to(ROOT)}:{n.lineno} {nombre}.{n.func.attr}()')
        self.assertEqual(lecturas, [])

    def test_site_today_obedece_al_dia_fijado(self):
        import site_clock
        anterior = site_clock.os.environ.pop('CATALOGO_HOY', None)
        try:
            site_clock.os.environ['CATALOGO_HOY'] = '2030-01-02'
            self.assertEqual(site_clock.site_today(), date(2030, 1, 2))
            site_clock.os.environ['CATALOGO_HOY'] = '02/01/2030'
            with self.assertRaises(ValueError):
                site_clock.site_today()
        finally:
            site_clock.os.environ.pop('CATALOGO_HOY', None)
            if anterior is not None:
                site_clock.os.environ['CATALOGO_HOY'] = anterior

    def test_badge_sin_ancla_usa_el_dia_fijado(self):
        anterior = b.site_clock.os.environ.get('CATALOGO_HOY')
        try:
            b.site_clock.os.environ['CATALOGO_HOY'] = '2026-11-17'
            self.assertEqual(b.badge({'fecha_publicacion': '2026-11-18'}), 'proximamente')
            self.assertEqual(b.badge({'fecha_publicacion': '2026-11-17'}), 'novedad')
        finally:
            b.site_clock.os.environ.pop('CATALOGO_HOY', None)
            if anterior is not None:
                b.site_clock.os.environ['CATALOGO_HOY'] = anterior


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

    def test_un_solo_despliegue_diario_por_el_cron_que_disparo(self):
        # En verano los dos horarios caen a las 00:05 y 01:05 de Madrid: decidir por la hora publicaba dos veces.
        paso = self.wf['jobs']['dia']['steps'][0]
        self.assertEqual(paso['env']['CRON'], '${{ github.event.schedule }}')
        self.assertIn("+0200 ]; then propio='5 22 * * *'; else propio='5 23 * * *'", paso['run'])
        self.assertNotIn('date +%H', paso['run'])

    def test_un_disparo_descartado_no_cancela_un_despliegue_por_push(self):
        self.assertNotIn('concurrency', self.wf)
        self.assertEqual(self.wf['jobs']['build']['concurrency'], {'group': 'pages-build', 'cancel-in-progress': True})
        self.assertFalse(self.wf['jobs']['deploy']['concurrency']['cancel-in-progress'])


    def pasos_build(self):
        """Pasos del build con la acción común (construir-como-despliegue) desplegada en su sitio."""
        pasos = []
        for paso in self.wf['jobs']['build']['steps']:
            if paso.get('uses') == './.github/actions/construir-como-despliegue':
                accion = yaml.safe_load((ROOT / '.github/actions/construir-como-despliegue/action.yml')
                                        .read_text(encoding='utf-8'))
                self.assertEqual(paso['with']['hoy'], '${{ needs.dia.outputs.hoy }}')
                pasos += accion['runs']['steps']
            else:
                pasos.append(paso)
        return pasos

    def test_dependencias_python_antes_de_la_cadena(self):
        pasos = self.pasos_build()
        nombres = [p.get('name', '') for p in pasos]
        pip = nombres.index('Dependencias Python')
        self.assertIn('requirements.txt', pasos[pip]['run'])
        self.assertLess(pip, nombres.index('Materializar generados'))

    def test_lo_generado_se_rehace_con_el_dia_antes_de_publicar(self):
        pasos = self.pasos_build()
        nombres = [p.get('name', '') for p in pasos]
        rehacer = nombres.index('Rehacer lo generado con el día')
        self.assertLess(nombres.index('Materializar generados'), rehacer)
        self.assertLess(rehacer, nombres.index('Build public artifact (allowlist-first)'))
        self.assertEqual(pasos[rehacer]['env']['CATALOGO_HOY'], '${{ inputs.hoy }}')  # = needs.dia.outputs.hoy
        # la cadena acaba en `npx --no-install pagefind`: Node y el lockfile instalados antes de rehacer
        self.assertLess(nombres.index('Set up Node'), rehacer)
        npm = nombres.index('Instalar Pagefind (lockfile)')
        self.assertLess(npm, rehacer)
        self.assertIn('npm ci', pasos[npm]['run'])


if __name__ == '__main__':
    unittest.main()
