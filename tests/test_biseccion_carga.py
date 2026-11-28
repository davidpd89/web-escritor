"""Un fallo de contrato que no nombra libros se atribuye por bisección a los libros de la carga que lo provocan.

28/11: seis tests de código de test_reading_texts tomaban el primer libro del catálogo real como ejemplo; el lote
de 992 libros salió rojo en la QA de la PR dos veces sin que ningún fallo nombrara un id. Aquí: la búsqueda
encuentra uno o varios culpables con pocas sondas, no aparta nada si el fallo no depende de los datos de esta noche
(código), respeta el plazo del job, y assemble() aparta lo hallado en vez de parar (datos) o deja la decisión a la
PR (código).
"""
import contextlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import biseccion_carga as bis  # noqa: E402

spec = importlib.util.spec_from_file_location('refresh_reading_catalogue_bis', ROOT / 'scripts/refresh-reading-catalogue.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)


def libro(i, **kw):
    return {'id': i, 'titulo': i, **kw}


class BusquedaTest(unittest.TestCase):
    def test_encuentra_el_culpable_con_log2_sondas(self):
        cands = [f'b{i}' for i in range(1000)]
        sondas = []

        def falla(quitar):
            sondas.append(len(quitar))
            return 'b637' not in quitar
        self.assertEqual(bis.culpables(cands, falla), ['b637'])
        self.assertLessEqual(len(sondas), 14)  # reproducir + 1 + log2(1000) + confirmar dos veces

    def test_varios_culpables_se_encuentran_todos(self):
        cands = [f'b{i}' for i in range(64)]
        self.assertEqual(sorted(bis.culpables(cands, lambda q: not {'b3', 'b40'} <= set(q))), ['b3', 'b40'])
        # cualquiera de los dos basta para que falle: también ambos
        self.assertEqual(sorted(bis.culpables(cands, lambda q: bool({'b5', 'b9'} - set(q)))), ['b5', 'b9'])

    def test_si_ni_sin_la_carga_pasa_no_es_un_dato(self):
        self.assertIsNone(bis.culpables(['a', 'b'], lambda q: True))
        self.assertIsNone(bis.culpables([], lambda q: True))

    def test_un_fallo_inestable_no_aparta_nada(self):
        respuestas = iter([True, False, True, True, True])  # pasa al quitar todo y luego nunca: no monótono
        self.assertIsNone(bis.culpables(['a', 'b', 'c', 'd'], lambda q: next(respuestas, True)))

    def test_si_el_fallo_no_se_reproduce_no_se_busca(self):
        sondas = []
        self.assertIsNone(bis.culpables(['a', 'b'], lambda q: sondas.append(q) or False))
        self.assertEqual(sondas, [[]])

    def test_un_arreglo_que_no_aguanta_la_segunda_comprobacion_no_aparta(self):
        vistas = {}

        def falla(q):
            k = tuple(q)
            vistas[k] = vistas.get(k, 0) + 1
            return 'b' not in q or vistas[k] > 1  # quitar b arregla solo la primera vez
        self.assertIsNone(bis.culpables(['a', 'b'], falla))

    def test_el_plazo_corta_la_busqueda(self):
        reloj = iter(range(100))
        with self.assertRaises(bis.SinTiempo):
            bis.culpables([f'b{i}' for i in range(100)], lambda q: 'b99' not in q, hasta=3, reloj=lambda: next(reloj))

    def test_el_plazo_cubre_tambien_la_primera_sonda_y_las_confirmaciones(self):
        sondas = []
        with self.assertRaises(bis.SinTiempo):
            bis.culpables(['a'], lambda q: sondas.append(q) or True, hasta=0, reloj=lambda: 0)
        self.assertEqual(sondas, [])
        reloj = iter([0, 0, 0, 5])  # reproducir, sonda con a retirado (un solo candidato) -> confirmar ya sin plazo
        with self.assertRaises(bis.SinTiempo):
            bis.culpables(['a'], lambda q: 'a' not in q, hasta=3, reloj=lambda: next(reloj))

    def test_candidatos_son_altas_y_cambiados_en_orden_y_retirar_vuelve_a_lo_publicado(self):
        pub = {'libros': [libro('a'), libro('b')], 'libro_categorias': [{'libro_id': 'b', 'categoria_id': 'x'}]}
        data = {'libros': [libro('n1'), libro('a'), libro('b', titulo='cambiado'), libro('n2')],
                'libro_categorias': [{'libro_id': 'b', 'categoria_id': 'y'}, {'libro_id': 'n1', 'categoria_id': 'x'}]}
        self.assertEqual(bis.candidatos(data, pub), ['n1', 'b', 'n2'])
        solo_generos = {'libros': [libro('a'), libro('b')], 'libro_categorias': [{'libro_id': 'b', 'categoria_id': 'y'}]}
        self.assertEqual(bis.candidatos(solo_generos, pub), ['b'])
        out = bis.retirar(data, pub, ['n1', 'b'])
        self.assertEqual(out['libros'], [libro('a'), libro('b'), libro('n2')])
        self.assertEqual(out['libro_categorias'], [{'libro_id': 'b', 'categoria_id': 'x'}])
        self.assertEqual(len(data['libros']), 4)  # no muta la entrada

    def test_ids_que_sabe_repetir_la_puerta(self):
        self.assertEqual(bis.ids_solo([{'test': 'm.C.test_a (libro=1)'}, {'test': 'm.C.test_a (libro=2)'},
                                       {'test': 'unittest.loader._FailedTest.test_mod'}, {'test': 'tests/test-x.py'}]),
                         ['m.C.test_a', 'test_mod', 'tests/test-x.py'])


class SondaSobreElCatalogoTest(unittest.TestCase):
    def test_cada_sonda_deja_el_catalogo_como_estaba(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / refresh.reading_quarantine.CATALOGUE
            path.parent.mkdir(parents=True)
            data = {'libros': [libro('a'), libro('n1'), libro('n2')], 'libro_categorias': []}
            path.write_text(json.dumps(data), encoding='utf-8')
            original = path.read_bytes()
            vistos = []

            def puerta(*args):
                vistos.append(args)
                ids = {b['id'] for b in json.loads(path.read_text(encoding='utf-8'))['libros']}
                return [{'test': 'm.C.test_x', 'texto': 'Best Seller'}] if 'n2' in ids else []
            with patch.object(refresh, 'ROOT', root), patch.object(refresh, 'data_contract_failures', puerta), \
                    patch.object(refresh.reading_quarantine, 'committed', lambda r: {'libros': [libro('a')], 'libro_categorias': []}):
                found = refresh.bisect_unattributed([{'test': 'm.C.test_x (p=1)', 'texto': 'Best Seller'}])
            self.assertEqual(list(found), ['n2'])
            self.assertIn('bisección', found['n2'])
            self.assertEqual(path.read_bytes(), original)
            self.assertTrue(all(a == ('--solo', 'm.C.test_x') for a in vistos))

    def test_una_sonda_que_no_se_puede_evaluar_abandona_sin_apartar(self):
        for puerta in (lambda *a: (_ for _ in ()).throw(RuntimeError('sin fallos.json')),
                       lambda *a: [{'test': 'm', 'texto': 'sin terminar en 1800 s'}]):
            with self.subTest(puerta=puerta), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                path = root / refresh.reading_quarantine.CATALOGUE
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({'libros': [libro('n1'), libro('n2')], 'libro_categorias': []}), encoding='utf-8')
                original = path.read_bytes()
                with patch.object(refresh, 'ROOT', root), patch.object(refresh, 'data_contract_failures', puerta),                         patch.object(refresh.reading_quarantine, 'committed', lambda r: {'libros': [], 'libro_categorias': []}):
                    self.assertEqual(refresh.bisect_unattributed([{'test': 'm.C.test_x', 'texto': 'x'}]), {})
                self.assertEqual(path.read_bytes(), original)


class AssembleTest(unittest.TestCase):
    def run_assemble(self, datos, codigo, bisect):
        """datos/codigo: listas de rondas de fallos de cada pasada; bisect: {id: motivo} o {}."""
        calls = {'codigo': [], 'flagged': [], 'published': []}
        datos, codigo = list(datos), list(codigo)

        def code(only=None):
            calls['codigo'].append(only)
            return codigo.pop(0) if codigo else []

        def apply(root=None, today=None, flagged=None):
            calls['flagged'].append(dict(flagged or {}))
            return [{'libro': {'id': i}, 'motivo': m} for i, m in (flagged or {}).items()]
        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as s:
            for owner, name, value in [
                    (refresh, 'ROOT', Path(tmp)), (refresh, 'command', lambda *a: None), (refresh, 'push', lambda *a, **k: None),
                    (refresh, 'bot_identity', lambda: None), (refresh, 'read_json', lambda p: {'rss_enabled': False, 'libros': []}),
                    (refresh, 'quarantine_summary', lambda *a: ''), (refresh, 'quarantine_alert', lambda *a: None),
                    (refresh, 'data_contract_failures', lambda *a: datos.pop(0) if datos else []),
                    (refresh, 'code_contract_failures', code), (refresh, 'bisect_unattributed', lambda u: dict(bisect)),
                    (refresh, 'drop_orphan_pages', lambda q: None), (refresh.reading_quarantine, 'apply', apply),
                    (refresh.materializar, 'construir', lambda *a, **k: None), (refresh.materializar, 'comprobar', lambda *a, **k: None),
                    (refresh.subprocess, 'check_output', lambda *a, **k: ' M data/reading-catalogue.json\n'),
                    (refresh.git_estado, 'rutas', lambda *a, **k: ['data/reading-catalogue.json']),
                    (refresh.git_estado, 'preparar', lambda *a, **k: None), (refresh.publisher, 'allowed_path', lambda p: True),
                    (refresh.publisher, 'run', lambda b: calls['published'].append(b)),
                    (refresh.publisher.publication, 'fresh_branch', lambda *a, **k: 'automation/reading-catalogue-test'),
                    (refresh.publisher.publication, 'gh', lambda *a: None), (refresh, 'drop_checkpoint', lambda b: None)]:
                s.enter_context(patch.object(owner, name, value))
            refresh.assemble({'new_books': ['n'], 'updated_books': [], 'stats': {}}, changed=True, checkpoint='saved')
        return calls

    SIN_LIBRO = [{'test': 'test_reading_texts.T.test_ejemplo', 'texto': 'Best Seller'}]

    def test_un_test_de_codigo_sin_libro_aparta_el_culpable_y_publica(self):
        calls = self.run_assemble([], [self.SIN_LIBRO], {'isbn-1': 'bisección'})
        self.assertEqual(calls['flagged'][-1], {'isbn-1': 'bisección'})
        self.assertEqual(calls['codigo'], [None, ['test_reading_texts.T.test_ejemplo']])  # entera y luego solo lo que falló
        self.assertEqual(len(calls['published']), 1)

    def test_codigo_roto_sin_culpable_no_pierde_el_lote(self):
        calls = self.run_assemble([], [self.SIN_LIBRO], {})
        self.assertEqual(calls['flagged'], [{}])  # solo la cuarentena inicial: nada apartado
        self.assertEqual(len(calls['published']), 1)

    def test_un_contrato_de_datos_sin_libro_se_atribuye_por_biseccion(self):
        calls = self.run_assemble([self.SIN_LIBRO], [], {'isbn-2': 'bisección'})
        self.assertEqual(calls['flagged'][-1], {'isbn-2': 'bisección'})
        self.assertEqual(len(calls['published']), 1)

    def test_un_contrato_de_datos_sin_libro_ni_culpable_sigue_parando(self):
        with self.assertRaisesRegex(RuntimeError, 'no nombran ningún libro'):
            self.run_assemble([self.SIN_LIBRO], [], {})


if __name__ == '__main__':
    unittest.main()
