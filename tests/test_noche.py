"""Fable R4-1 (F1): un solo libro de la noche para el juez de los relojes, el reintento y la cadena.

Antes cada decisión deducía «esta noche» de listas de Actions: el juez desde las 00:00 UTC, el reintento desde la
medianoche de Madrid. Una carga fallida a las 00:30 de Madrid (23:30 UTC) la contaba el reintento y no el juez.
"""
import json
import random
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import noche  # noqa: E402

UTC = timezone.utc


def ida_y_vuelta(libro):
    return json.loads(json.dumps(libro))  # el libro viaja como JSON por la rama catalogo-estado


class SimulacionF1Test(unittest.TestCase):
    """60 cargas seguidas de 22:30 UTC a 05:30 UTC (cruza las dos medianoches), en invierno y en verano."""

    def simular(self, inicio):
        rnd = random.Random(1116)
        libro, historia = None, []  # historia: (hora, resultado) de verdad, para contar sin el libro
        ahora = inicio
        for run in range(1, 61):
            ahora += timedelta(minutes=7)
            dia = ahora.astimezone(noche.MADRID).date()
            fallidas = sum(r == 'fallido' and h.astimezone(noche.MADRID).date() == dia for h, r in historia)
            hora = ahora.astimezone(noche.MADRID).hour
            # Las tres decisiones ven la misma noche: la de Madrid.
            self.assertEqual(noche.resumen(libro, ahora)['fallidos'], fallidas, ahora)
            ultima = next((r for h, r in reversed(historia) if h.astimezone(noche.MADRID).date() == dia), None)
            esperado = fallidas < noche.MAX_FALLIDOS and ultima not in ('publicado',)
            self.assertEqual(noche.decidir(libro, ahora)[0], esperado, (ahora, fallidas, ultima))
            cargar, _, libro = noche.abrir(libro, ahora, run, 1, 'sha', 'cron' if run % 3 else 'cadena')
            libro = ida_y_vuelta(libro)
            if not cargar:
                continue
            self.assertFalse(noche.decidir(libro, ahora + timedelta(minutes=1))[0], 'en curso: ningún reloj carga')
            fin = ahora + timedelta(minutes=5)
            resultado = rnd.choice(['success', 'failure', 'failure', 'cancelled'])
            libro = ida_y_vuelta(noche.cerrar(libro, fin, run, 1, resultado))
            final = noche.RESULTADOS[resultado]
            historia.append((ahora, final))
            dia_fin = fin.astimezone(noche.MADRID).date()
            fallidas_fin = sum(r == 'fallido' and h.astimezone(noche.MADRID).date() == dia_fin for h, r in historia)
            de_noche = fin.astimezone(noche.MADRID).hour < noche.HORA_FIN
            if final == 'fallido':
                self.assertEqual(noche.toca_reintento(libro, fin)[0], de_noche and fallidas_fin < noche.MAX_FALLIDOS,
                                 (fin, fallidas_fin))
            if final == 'publicado':
                self.assertEqual(noche.toca_cadena(libro, fin, 5)[0], de_noche, fin)
            ahora = fin
            del hora
        return historia

    def test_invierno_utc_mas_1(self):
        historia = self.simular(datetime(2026, 11, 15, 22, 30, tzinfo=UTC))
        self.assertGreater(len({h.astimezone(UTC).date() for h, _ in historia}), 1, 'cruza la medianoche UTC')

    def test_verano_utc_mas_2(self):
        self.simular(datetime(2026, 7, 15, 21, 30, tzinfo=UTC))

    def test_fallo_entre_medianoches_cuenta_igual_para_todos(self):
        """El caso exacto de F1: fallo a las 00:30 de Madrid (23:30 UTC del día anterior)."""
        t = datetime(2026, 11, 15, 23, 30, tzinfo=UTC)
        libro = noche.abrir(None, t, 1, 1, 's', 'cron')[2]
        libro = noche.cerrar(libro, t + timedelta(minutes=10), 1, 1, 'failure')
        libro = noche.abrir(libro, t + timedelta(minutes=20), 2, 1, 's', 'reintento')[2]
        libro = noche.cerrar(libro, t + timedelta(minutes=40), 2, 1, 'failure')
        libro = noche.abrir(libro, t + timedelta(minutes=50), 3, 1, 's', 'reintento')[2]
        libro = noche.cerrar(libro, t + timedelta(minutes=70), 3, 1, 'failure')
        despues = t + timedelta(hours=1, minutes=30)  # 00:00 UTC pasadas: el juez viejo empezaba de cero
        self.assertEqual(noche.resumen(libro, despues)['fallidos'], 3)
        self.assertFalse(noche.decidir(libro, despues)[0], 'el reloj no insiste tras 3 fallos de esta noche')
        self.assertFalse(noche.toca_reintento(libro, despues)[0])

    def test_la_noche_de_ayer_no_cuenta(self):
        ayer = datetime(2026, 11, 15, 22, 50, tzinfo=UTC)  # 23:50 Madrid del 15
        libro = noche.cerrar(noche.abrir(None, ayer, 1, 1, 's', 'cron')[2], ayer + timedelta(minutes=5), 1, 1, 'success')
        hoy = datetime(2026, 11, 15, 23, 17, tzinfo=UTC)  # 00:17 Madrid del 16
        self.assertTrue(noche.decidir(libro, hoy)[0], 'la carga publicada ayer no cede la noche de hoy')


class ReglasTest(unittest.TestCase):
    T = datetime(2026, 11, 16, 1, 0, tzinfo=UTC)

    def test_corte_sin_cierre_cuenta_como_fallida_tras_el_tope_del_job(self):
        libro = noche.abrir(None, self.T, 1, 1, 's', 'cron')[2]
        self.assertFalse(noche.decidir(libro, self.T + timedelta(minutes=200))[0], 'aún puede estar viva')
        self.assertTrue(noche.decidir(libro, self.T + timedelta(minutes=260))[0], 'murió sin cerrar: se reintenta')
        self.assertEqual(noche.resumen(libro, self.T + timedelta(minutes=260))['fallidos'], 1)

    def test_pendiente_bloquea_y_caduca(self):
        libro = noche.pendiente(None, self.T, 'cadena')
        self.assertFalse(noche.decidir(libro, self.T + timedelta(minutes=5))[0], 'un despacho en vuelo')
        self.assertTrue(noche.decidir(libro, self.T + timedelta(minutes=30))[0], 'un despacho perdido no bloquea')

    def test_dos_relojes_a_la_vez_cargan_una_vez(self):
        """El segundo coge el turno del grupo de concurrencia después y vuelve a decidir con el libro."""
        libro = noche.abrir(None, self.T, 1, 1, 's', 'cron')[2]
        cargar, porque, _ = noche.abrir(ida_y_vuelta(libro), self.T + timedelta(seconds=30), 2, 1, 's', 'respaldo')
        self.assertFalse(cargar, porque)

    def test_cadena_y_reintento_cargan_aunque_haya_pendiente_y_lo_consumen(self):
        libro = noche.pendiente(None, self.T, 'cadena')
        cargar, _, libro = noche.abrir(libro, self.T + timedelta(minutes=1), 2, 1, 's', 'cadena')
        self.assertTrue(cargar)
        self.assertEqual([i['resultado'] for i in libro['intentos']], ['en_curso'])

    def test_un_reintento_de_actions_es_otro_intento(self):
        libro = noche.cerrar(noche.abrir(None, self.T, 7, 1, 's', 'cron')[2], self.T, 7, 1, 'failure')
        libro = noche.abrir(libro, self.T + timedelta(minutes=1), 7, 2, 's', 'manual')[2]
        libro = noche.cerrar(libro, self.T + timedelta(minutes=2), 7, 2, 'success')
        self.assertEqual([(i['intento'], i['resultado']) for i in libro['intentos']], [(1, 'fallido'), (2, 'publicado')])
        self.assertFalse(noche.decidir(libro, self.T + timedelta(minutes=3))[0])

    def test_de_dia_ni_cadena_ni_reintento(self):
        dia = datetime(2026, 11, 16, 5, 30, tzinfo=UTC)  # 06:30 Madrid
        self.assertFalse(noche.toca_cadena(None, dia, 10)[0])
        self.assertFalse(noche.toca_reintento(None, dia)[0])
        self.assertFalse(noche.toca_cadena(None, self.T, 0)[0], 'sin altas no se encadena')

    def test_juez_sin_libro_legible_carga(self):
        with mock.patch.object(noche, 'leer', side_effect=OSError('git')), \
                mock.patch('sys.stdout') as out, mock.patch.dict('os.environ', {}, clear=False):
            self.assertEqual(noche.main(['juez']), 0)
        self.assertIn('run=true', ''.join(c.args[0] for c in out.write.call_args_list))


class GuardiaTest(unittest.TestCase):
    """Hecho de R4-1: ninguna de esas decisiones vuelve a mirar listas de ejecuciones de Actions."""

    def test_ninguna_decision_lista_ejecuciones(self):
        wf = (ROOT / '.github/workflows/reading-catalogue-sync.yml').read_text(encoding='utf-8')
        fuentes = {'reading-catalogue-sync.yml': wf,
                   'ci_intake_backup.py': (ROOT / 'scripts/ci_intake_backup.py').read_text(encoding='utf-8'),
                   'noche.py': (ROOT / 'scripts/noche.py').read_text(encoding='utf-8')}
        for nombre, texto in fuentes.items():
            for prohibido in ('gh run list', '/actions/workflows/', '/actions/runs', 'TZ=Europe/Madrid date'):
                self.assertNotIn(prohibido, texto, f'{nombre} decide con {prohibido!r}')

    def test_workflow_abre_y_cierra_el_libro(self):
        wf = (ROOT / '.github/workflows/reading-catalogue-sync.yml').read_text(encoding='utf-8').replace('\r\n', '\n')
        self.assertIn('python scripts/noche.py abrir --motivo "$MOTIVO" >> "$GITHUB_OUTPUT"', wf)
        self.assertIn("if: ${{ !inputs.dry_run }}", wf, 'un ensayo no escribe en el libro')
        self.assertIn('python scripts/noche.py cerrar --resultado "$RESULTADO"', wf)
        self.assertIn("if: inputs.dry_run || steps.libro.outputs.cargar == 'true'", wf)
        self.assertIn('-f motivo=cadena', wf)
        self.assertIn('-f motivo=reintento', wf)
        # El cierre va antes que el reintento: el reintento cuenta la fallida que acaba de pasar.
        self.assertLess(wf.index('name: Close the night turn'), wf.index('name: Retry a failed night batch'))
        self.assertLess(wf.index('name: Close the night turn'), wf.index('name: Chain the next night batch'))
        # El reloj descarga lo que necesita para leer el libro.
        for script in ('scripts/ci_intake_backup.py', 'scripts/noche.py', 'scripts/catalogo_estado.py'):
            self.assertIn(f'            {script}\n', wf)


if __name__ == '__main__':
    unittest.main()
