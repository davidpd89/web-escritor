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
        self.assertEqual((rc, t), (0, 10 * (c.ERRORES - 1)), 'reintenta antes de abrir')
        self.assertIn('No se pudo mirar', salida)

    def test_un_fallo_suelto_de_gh_no_abre_main_en_plena_carga(self):
        """Caso 7 de la revisión GPT (25/11): un 502 de gh abría main con la carga en marcha."""
        ocupada = consulta_de({'reading-catalogue-sync.yml': 'in_progress'}, {'reading-catalogue-sync.yml': 'in_progress'}, {})
        fallos = {'n': 1}

        def a_ratos(flujo):
            if fallos['n']:
                fallos['n'] -= 1
                raise subprocess.CalledProcessError(1, 'gh')
            return ocupada(flujo)
        rc, t, salida = self.esperar(a_ratos)
        self.assertEqual(rc, 0)
        self.assertIn('Main congelado', salida)
        self.assertIn('Main libre', salida)
        self.assertGreaterEqual(t, 20)

    def test_tope_agotado_abre_con_aviso(self):
        rc, t, salida = self.esperar(consulta_de({'reading-catalogue-sync.yml': 'in_progress'}), tope_s=50)
        self.assertEqual((rc, t), (0, 50))
        self.assertIn('Congelación agotada', salida)

    def test_ejecucion_terminada_no_cuenta(self):
        self.assertEqual(c.activas(consulta_de({'reading-catalogue-sync.yml': 'completed'})), [])


class GhFalso:
    """gh con las PR abiertas en memoria: `pr list` las lista, `pr edit` y `pr ready` las cambian."""

    def __init__(self, prs, rompe=()):
        self.prs = {p['number']: dict(p, labels=[{'name': n} for n in p.get('labels', [])]) for p in prs}
        self.rompe = set(rompe)
        self.llamadas = []
        self.etiquetas = set()

    def __call__(self, *args):
        import json
        self.llamadas.append(args)
        if args[:2] == ('pr', 'list'):
            return json.dumps(list(self.prs.values()))
        if args[0] == 'label':
            self.etiquetas.add(args[2])
            return ''
        numero = int(args[2])
        if numero in self.rompe:
            raise subprocess.CalledProcessError(1, 'gh')
        pr = self.prs[numero]
        if args[1] == 'ready':
            pr['isDraft'] = '--undo' in args
            if pr['isDraft']:
                pr['autoMergeRequest'] = None  # como GitHub: el borrador desactiva el auto-merge
        elif args[1] == 'merge':
            assert not pr['isDraft'], 'GitHub no activa auto-merge en un borrador'
            pr['autoMergeRequest'] = {'mergeMethod': 'SQUASH'}
        elif '--add-label' in args:
            assert set(args[-1].split(',')) <= self.etiquetas, 'gh falla con una etiqueta que no existe'
            pr['labels'] += [{'name': n} for n in args[-1].split(',')]
        elif '--remove-label' in args:
            quitar = args[-1].split(',')
            pr['labels'] = [e for e in pr['labels'] if e['name'] not in quitar]
        return ''

    def estado(self):
        return {n: (p['isDraft'], c.ETIQUETA_CARGA in [e['name'] for e in p['labels']]) for n, p in self.prs.items()}


def libre(flujo):
    return [{'databaseId': 1, 'status': 'completed', 'createdAt': 'x', 'event': 'schedule'}]


def ocupada(flujo):
    return [{'databaseId': 2, 'status': 'queued', 'createdAt': 'x', 'event': 'workflow_dispatch'}]


class CongelarPrAbiertasTest(unittest.TestCase):
    """Caso 6 de la revisión GPT (25/11): el check solo corre al abrir o actualizar la PR, así que una PR verde de
    antes de la carga se fusionaba en mitad de ella. La carga las pasa a borrador y el segador las devuelve."""

    PRS = [
        {'number': 1, 'headRefName': 'fix/algo', 'isDraft': False},
        {'number': 2, 'headRefName': 'feat/borrador-del-autor', 'isDraft': True},
        {'number': 3, 'headRefName': 'automation/reading-catalogue-2026-11-25', 'isDraft': False},
        {'number': 4, 'headRefName': 'fix/urgente', 'isDraft': False, 'labels': ['sin-congelar']},
        {'number': 5, 'headRefName': 'revision/paquete-07', 'isDraft': False},
    ]

    def test_una_pr_verde_de_antes_queda_sin_poder_fusionarse_y_vuelve_al_acabar(self):
        gh = GhFalso(self.PRS)
        self.assertEqual(c.congelar(gh, imprimir=lambda *_: None), [1])
        self.assertEqual(gh.estado()[1], (True, True), 'borrador y marcada')
        self.assertEqual({n: e for n, e in gh.estado().items() if n != 1},
                         {2: (True, False), 3: (False, False), 4: (False, False), 5: (False, False)},
                         'ni el borrador del autor, ni la carga, ni las exentas')
        self.assertEqual(c.descongelar(gh, libre, imprimir=lambda *_: None, pausa_s=0), [1])
        self.assertEqual(gh.estado()[1], (False, False))
        self.assertEqual(gh.estado()[2], (True, False), 'el borrador del autor sigue siéndolo')

    def test_con_otra_carga_en_cola_siguen_congeladas(self):
        gh = GhFalso(self.PRS)
        c.congelar(gh, imprimir=lambda *_: None)
        self.assertEqual(c.descongelar(gh, ocupada, imprimir=lambda *_: None, pausa_s=0), [])
        self.assertEqual(gh.estado()[1], (True, True))

    def test_falla_abierto(self):
        gh = GhFalso(self.PRS + [{'number': 6, 'headRefName': 'fix/otra', 'isDraft': False}], rompe={1})
        salida = []
        self.assertEqual(c.congelar(gh, imprimir=salida.append), [6], 'una PR que falla no para las demás')
        self.assertIn('#1 sin congelar', '\n'.join(salida))

        def roto(*args):
            raise subprocess.CalledProcessError(1, 'gh')
        self.assertEqual(c.congelar(roto, imprimir=lambda *_: None), [])
        self.assertEqual(c.descongelar(roto, libre, imprimir=lambda *_: None, pausa_s=0), [])

    def test_si_falla_el_borrador_la_etiqueta_la_devuelve_igual(self):
        """Etiqueta antes que borrador: descongelar quita la etiqueta aunque la PR no llegara a borrador."""
        gh = GhFalso([{'number': 1, 'headRefName': 'fix/algo', 'isDraft': False, 'labels': [c.ETIQUETA_CARGA]}])
        self.assertEqual(c.descongelar(gh, libre, imprimir=lambda *_: None, pausa_s=0), [1])
        self.assertEqual(gh.estado()[1], (False, False))
        self.assertNotIn(('pr', 'ready', '1'), gh.llamadas, 'no la marca lista si no era borrador')

    def test_el_auto_merge_vuelve_tras_la_noche(self):
        """Caso 1 de la ronda 2: la reparación con auto-merge lo perdía al pasar a borrador."""
        gh = GhFalso([{'number': 7, 'headRefName': 'autorepair/x-1', 'isDraft': False,
                       'autoMergeRequest': {'mergeMethod': 'SQUASH'}},
                      {'number': 8, 'headRefName': 'fix/sin-auto', 'isDraft': False, 'autoMergeRequest': None}])
        c.congelar(gh, imprimir=lambda *_: None)
        self.assertIsNone(gh.prs[7]['autoMergeRequest'])
        self.assertEqual(c.descongelar(gh, libre, imprimir=lambda *_: None, pausa_s=0), [7, 8])
        self.assertTrue(gh.prs[7]['autoMergeRequest'], 'vuelve con auto-merge')
        self.assertIsNone(gh.prs[8]['autoMergeRequest'], 'la que no lo tenía no lo gana')
        self.assertEqual(gh.prs[7]['labels'], [], 'sin etiquetas de congelación')

    def test_si_falla_el_auto_merge_sigue_marcada_para_reintentar(self):
        gh = GhFalso([{'number': 7, 'headRefName': 'autorepair/x-1', 'isDraft': False,
                       'autoMergeRequest': {'mergeMethod': 'SQUASH'}}])
        c.congelar(gh, imprimir=lambda *_: None)

        def merge_roto(*args):
            if args[1] == 'merge':
                raise subprocess.CalledProcessError(1, 'gh')
            return gh(*args)
        self.assertEqual(c.descongelar(merge_roto, libre, imprimir=lambda *_: None, pausa_s=0), [])
        self.assertIn(c.ETIQUETA_AUTO, [e['name'] for e in gh.prs[7]['labels']])
        self.assertEqual(c.descongelar(gh, libre, imprimir=lambda *_: None, pausa_s=0), [7],
                         'la siguiente pasada lo completa')
        self.assertTrue(gh.prs[7]['autoMergeRequest'])

    def test_la_carga_que_tarda_en_aparecer_mantiene_la_congelacion(self):
        """Caso 2 de la ronda 2: A acaba y B ya está despachada, pero el listado aún no la muestra."""
        gh = GhFalso(self.PRS)
        c.congelar(gh, imprimir=lambda *_: None)
        vistas = iter([libre, ocupada])
        pausas = []
        self.assertEqual(c.descongelar(gh, lambda f: next(vistas)(f), imprimir=lambda *_: None,
                                       dormir=pausas.append), [])
        self.assertEqual(pausas, [c.CONFIRMAR_S])
        self.assertEqual(gh.estado()[1], (True, True))

    def test_workflows_cableados(self):
        sync = (ROOT / '.github/workflows/reading-catalogue-sync.yml').read_text(encoding='utf-8')
        segador = (ROOT / '.github/workflows/reading-catalogue-reaper.yml').read_text(encoding='utf-8')
        espera = (ROOT / '.github/workflows/congelar-main.yml').read_text(encoding='utf-8')
        self.assertIn('scripts/congelar_main.py congelar', sync)
        self.assertLess(sync.index('noche.py abrir'), sync.index('congelar_main.py congelar'))
        tras = segador.split('descongelar:', 1)[1]
        self.assertIn('scripts/congelar_main.py descongelar', tras)
        self.assertNotIn('conclusion', tras.split('steps:', 1)[0], 'como acabe la carga, no solo en rojo')
        self.assertIn('pull-requests: write', tras)
        self.assertIn(c.ETIQUETA_CARGA, espera, 'su etiqueta no relanza la espera')


if __name__ == '__main__':
    unittest.main()
