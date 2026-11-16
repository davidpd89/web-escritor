"""Fable R4-1 (F1): un solo libro de la noche para el juez de los relojes, el reintento y la cadena.

Antes cada decisión deducía «esta noche» de listas de Actions: el juez desde las 00:00 UTC, el reintento desde la
medianoche de Madrid. Una carga fallida a las 00:30 de Madrid (23:30 UTC) la contaba el reintento y no el juez.
"""
import io
import json
import random
import sys
import unittest.mock  # también enlaza `unittest`
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
            # Las tres decisiones ven la misma noche: la de Madrid.
            self.assertEqual(noche.resumen(libro, ahora)['fallidos'], fallidas, ahora)
            ultima = next((r for h, r in reversed(historia) if h.astimezone(noche.MADRID).date() == dia), None)
            esperado = fallidas < noche.MAX_FALLIDOS and ultima not in ('publicado',)
            self.assertEqual(noche.decidir(libro, ahora)[0], esperado, (ahora, fallidas, ultima))
            cargar, _, libro = noche.abrir(libro, ahora, run, 1, 'sha', 'cron' if run % 3 else 'manual')
            libro = ida_y_vuelta(libro)
            if not cargar:
                continue
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
        libro = noche.pendiente(libro, t + timedelta(minutes=11), 'reintento')
        libro = noche.abrir(libro, t + timedelta(minutes=20), 2, 1, 's', 'reintento')[2]
        libro = noche.cerrar(libro, t + timedelta(minutes=40), 2, 1, 'failure')
        libro = noche.pendiente(libro, t + timedelta(minutes=41), 'reintento')
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

    def test_corte_sin_cierre_cuenta_como_fallida_al_coger_el_turno(self):
        libro = noche.abrir(None, self.T, 1, 1, 's', 'cron')[2]
        cargar, _, libro = noche.abrir(ida_y_vuelta(libro), self.T + timedelta(minutes=5), 2, 1, 's', 'respaldo')
        self.assertTrue(cargar, 'el grupo no deja dos a la vez: el en_curso ajeno murió')
        self.assertEqual([(i['run'], i['resultado'], i['clase']) for i in libro['intentos']],
                         [(1, 'fallido', 'corte'), (2, 'en_curso', None)])

    def test_dos_relojes_a_la_vez_cargan_una_vez(self):
        """El segundo coge el turno del grupo de concurrencia después y vuelve a decidir con el libro."""
        libro = noche.abrir(None, self.T, 1, 1, 's', 'cron')[2]
        libro = noche.cerrar(ida_y_vuelta(libro), self.T + timedelta(minutes=20), 1, 1, 'success')
        cargar, porque, _ = noche.abrir(ida_y_vuelta(libro), self.T + timedelta(minutes=21), 2, 1, 's', 'respaldo')
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
        with unittest.mock.patch.object(noche, 'leer', side_effect=OSError('git')), \
                unittest.mock.patch('sys.stdout') as out, unittest.mock.patch.dict('os.environ', {}, clear=False):
            self.assertEqual(noche.main(['juez']), 0)
        self.assertIn('run=true', ''.join(c.args[0] for c in out.write.call_args_list))


class HilosRevisionTest(unittest.TestCase):
    """Revisión de #1385: casos en los que el libro perdía una carga o autorizaba un reintento de más."""
    T = datetime(2026, 11, 16, 1, 0, tzinfo=UTC)

    def test_cierre_tras_medianoche_de_madrid_se_guarda_en_su_noche(self):
        abre = datetime(2026, 11, 15, 22, 50, tzinfo=UTC)  # 23:50 Madrid
        libro = ida_y_vuelta(noche.abrir(None, abre, 1, 1, 's', 'manual')[2])
        cerrado = noche.cerrar(libro, abre + timedelta(minutes=20), 1, 1, 'success')  # 00:10 Madrid
        self.assertEqual(cerrado['dia'], '2026-11-15')
        self.assertEqual([i['resultado'] for i in cerrado['intentos']], ['publicado'])

    def test_reintento_solo_si_esta_carga_consta_fallida(self):
        libro = noche.abrir(None, self.T, 5, 1, 's', 'cron')[2]
        self.assertFalse(noche.toca_reintento(libro, self.T, 5, 1)[0], 'el cierre no llegó: sigue en curso')
        publicado = noche.cerrar(libro, self.T, 5, 1, 'success')
        self.assertFalse(noche.toca_reintento(publicado, self.T, 5, 1)[0], 'publicó y falló un paso posterior')
        fallido = noche.cerrar(noche.abrir(None, self.T, 5, 1, 's', 'cron')[2], self.T, 5, 1, 'failure')
        self.assertTrue(noche.toca_reintento(fallido, self.T, 5, 1)[0])
        otro = noche.pendiente(fallido, self.T, 'cadena')
        self.assertFalse(noche.toca_reintento(otro, self.T, 5, 1)[0], 'ya hay otra despachada')

    def test_abrir_sin_libro_carga_y_no_ensucia_github_output(self):
        import catalogo_estado

        def escribe(*_a, **_k):
            print('Estado guardado en catalogo-estado@abc')  # lo que imprime catalogo_estado._commit

        for leer, esc in ((OSError('git'), escribe), (None, OSError('push'))):
            with unittest.mock.patch.object(noche, 'leer', side_effect=leer, return_value=None), \
                    unittest.mock.patch.object(catalogo_estado, 'escribir', side_effect=esc), \
                    unittest.mock.patch('sys.stdout', new_callable=io.StringIO) as out, \
                    unittest.mock.patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': ''}):
                self.assertEqual(noche.main(['abrir', '--motivo', 'cron']), 0)
            self.assertEqual(out.getvalue(), 'cargar=true\n')


    def test_abrir_con_libro_ilegible_no_lo_sobrescribe(self):
        import catalogo_estado
        with unittest.mock.patch.object(noche, 'leer', side_effect=OSError('git')), \
                unittest.mock.patch.object(catalogo_estado, 'escribir') as esc, \
                unittest.mock.patch('sys.stdout', new_callable=io.StringIO) as out, \
                unittest.mock.patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': ''}):
            self.assertEqual(noche.main(['abrir', '--motivo', 'cron']), 0)
        self.assertEqual(out.getvalue(), 'cargar=true\n')
        esc.assert_not_called()  # un libro vacío pisaría el historial remoto que no se pudo leer


class R59Test(unittest.TestCase):
    """Fable R5-9 (§2.6, hallazgos 1-4 y 13 de #1385): el turno decide todo lo que depende de «hay otra activa»."""
    T = datetime(2026, 11, 16, 1, 0, tzinfo=UTC)

    def test_runner_muerto_no_bloquea_la_noche(self):
        libro = ida_y_vuelta(noche.abrir(None, self.T, 1, 1, 's', 'cron')[2])  # nunca se cierra
        self.assertTrue(noche.decidir(libro, self.T + timedelta(minutes=30))[0], 'el juez no espera 250 min')
        cargar, _, libro = noche.abrir(libro, self.T + timedelta(minutes=30), 2, 1, 's', 'respaldo')
        self.assertTrue(cargar, 'con el turno, un en_curso ajeno está muerto')
        muerto = libro['intentos'][0]
        self.assertEqual((muerto['resultado'], muerto['clase']), ('fallido', 'corte'))
        self.assertEqual(noche.resumen(libro, self.T)['fallidos'], 1)

    def test_despacho_desalojado_lo_hereda_quien_tiene_el_turno(self):
        libro = noche.cerrar(noche.abrir(None, self.T, 1, 1, 's', 'cron')[2], self.T, 1, 1, 'success')
        libro = ida_y_vuelta(noche.pendiente(libro, self.T, 'cadena'))
        cargar, _, libro = noche.abrir(libro, self.T + timedelta(minutes=2), 3, 1, 's', 'respaldo')
        self.assertTrue(cargar, 'GitHub desalojó la cadena: el reloj carga por ella')
        self.assertEqual([(i['motivo'], i['resultado']) for i in libro['intentos']],
                         [('cron', 'publicado'), ('cadena', 'en_curso')])
        # La cadena llega tarde (no la desalojaron): ya no hay pendiente, no carga dos veces.
        libro = noche.cerrar(ida_y_vuelta(libro), self.T + timedelta(minutes=9), 3, 1, 'success')
        cargar, porque, despues = noche.abrir(ida_y_vuelta(libro), self.T + timedelta(minutes=10), 4, 1, 's', 'cadena')
        self.assertFalse(cargar, porque)
        self.assertEqual(despues['intentos'], libro['intentos'], 'quien no carga no toca el libro')

    def test_el_pendiente_no_bloquea_al_juez(self):
        libro = noche.pendiente(None, self.T, 'cadena')
        self.assertTrue(noche.decidir(libro, self.T + timedelta(minutes=1))[0], 'lo decide el job con el turno')

    def test_cierre_que_falla_no_cambia_el_resultado_de_la_carga(self):
        with unittest.mock.patch.object(noche, 'leer', side_effect=OSError('git')), \
                unittest.mock.patch('sys.stdout', new_callable=io.StringIO), \
                unittest.mock.patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': ''}):
            self.assertEqual(noche.main(['cerrar', '--resultado', 'success']), 0)

    def test_despacho_que_falla_no_despacha_ni_rompe_el_paso(self):
        for accion in ('cadena', 'reintento'):
            with unittest.mock.patch.object(noche, 'leer', side_effect=OSError('git')), \
                    unittest.mock.patch('sys.stdout', new_callable=io.StringIO), \
                    unittest.mock.patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': ''}):
                self.assertEqual(noche.main([accion, '--aceptados', '5']), 1, accion)
        import catalogo_estado
        with unittest.mock.patch.object(noche, 'leer', return_value=None), \
                unittest.mock.patch.object(catalogo_estado, 'escribir', side_effect=OSError('push')), \
                unittest.mock.patch.object(noche, 'datetime', wraps=datetime) as dt, \
                unittest.mock.patch('sys.stdout', new_callable=io.StringIO), \
                unittest.mock.patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': ''}):
            dt.now.return_value = self.T
            self.assertEqual(noche.main(['cadena', '--aceptados', '5']), 1, 'sin pendiente anotado no se despacha')

    def test_el_sha_es_el_del_codigo_que_corre(self):
        import catalogo_estado
        guardado = {}

        def escribe(_f, data, _m):
            guardado.update(json.loads(data))

        with unittest.mock.patch.object(noche, 'leer', return_value=None), \
                unittest.mock.patch.object(noche, '_head', return_value='b' * 40), \
                unittest.mock.patch.object(catalogo_estado, 'escribir', side_effect=escribe), \
                unittest.mock.patch('sys.stdout', new_callable=io.StringIO), \
                unittest.mock.patch.dict('os.environ', {'GITHUB_STEP_SUMMARY': '', 'GITHUB_SHA': 'a' * 40}):
            noche.main(['abrir', '--motivo', 'manual'])
        self.assertEqual(guardado['intentos'][0]['sha'], 'b' * 40)

    def test_sin_relojes_por_tiempo(self):
        self.assertFalse(hasattr(noche, 'SIN_CIERRE') or hasattr(noche, 'PENDIENTE_CADUCA'))


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
        # Un fallo antes de la carga (carga=skipped) cuenta como el job: fallida, con tope de reintentos.
        self.assertIn('then RESULTADO="$JOB"; fi', wf)
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
