"""Veredictos automáticos de clasificación (scripts/reading-classification-verdicts.py, 27/11).

Cubre la parte que no necesita ChatGPT: validación de respuestas, reglas de decisión R2/R3/R4, cola por huella
de la ficha y fusión con lo publicado sin pisar veredictos vigentes."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('verdicts_auto', ROOT / 'scripts/reading-classification-verdicts.py')
va = importlib.util.module_from_spec(spec)
spec.loader.exec_module(va)

GEN = {'fantasia': ('Fantasía', ''), 'romance': ('Romance', ''), 'narrativa': ('Narrativa', ''),
       'misterio-y-thriller': ('Misterio', ''), 'infantil': ('Infantil', ''), 'terror': ('Terror', '')}


def libro(i, **kw):
    return {'id': i, 'estado': 'publicado', 'titulo': 'T' + i, 'autores': ['A'], 'editorial': 'E',
            'descripcion_breve': 'sinopsis', **kw}


def catalogo(*libros, rels=()):
    cats = [{'id': g, 'nombre': n, 'tipo': 'genero', 'activa': True} for g, (n, _) in GEN.items()]
    cats.append({'id': 'juvenil', 'nombre': 'Juvenil', 'tipo': 'edad'})
    return {'categorias': cats, 'libros': list(libros),
            'libro_categorias': [{'libro_id': i, 'categoria_id': c} for i, c in rels]}


class Validacion(unittest.TestCase):
    def test_extrae_json_entre_texto_y_citas(self):
        r = 'Aquí va:\n{"libros": [{"id": "b01", "pub": "a", "gen": ["fantasia"]}]}\nFuentes: {x}'
        self.assertEqual(va.extraer(r), [{'id': 'b01', 'pub': 'a', 'gen': ['fantasia']}])
        self.assertIsNone(va.extraer('sin json'))

    def test_descarta_ids_ajenos_repetidos_y_generos_fuera_de_taxonomia(self):
        r = json.dumps({'libros': [
            {'id': 'b01', 'pub': 'a', 'gen': ['fantasia', 'romance']},
            {'id': 'b02', 'pub': 'a', 'gen': ['inventado']},
            {'id': 'b03', 'pub': 'a', 'gen': ['terror']}, {'id': 'b03', 'pub': 'j', 'gen': ['terror']},
            {'id': 'b99', 'pub': 'a', 'gen': ['terror']},
            {'id': 'b04', 'pub': 'x', 'gen': ['terror']}]})
        out = va.validar('r2', r, ['b01', 'b02', 'b03', 'b04'], GEN)
        self.assertEqual(list(out), ['b01'])
        self.assertEqual(out['b01'], {'gen': ['fantasia', 'romance'], 'pub': 'a', 'dudoso': False})

    def test_normaliza_narrativa_y_generos_adultos_en_infantil(self):
        self.assertEqual(va.normalizar({'pub': 'a', 'gen': ['narrativa', 'terror']}, GEN), (('terror',), 'a'))
        self.assertEqual(va.normalizar({'pub': 'i', 'gen': ['romance']}, GEN), (('infantil',), 'i'))
        self.assertEqual(va.normalizar({'pub': 'a', 'gen': ['fantasia', 'romance', 'terror', 'narrativa']}, GEN)[0],
                         ('fantasia', 'romance', 'terror'))

    def test_r4_exige_confianza(self):
        r = json.dumps({'libros': [{'id': 'b01', 'elige': 'A', 'pub': 'a', 'gen': ['terror'], 'conf': 'alta', 'fuente': 'u'},
                                   {'id': 'b02', 'elige': 'B', 'pub': 'a', 'gen': ['terror']}]})
        self.assertEqual(list(va.validar('r4', r, ['b01', 'b02'], GEN)), ['b01'])

    def test_prompt_ciego_no_ensena_la_etiqueta_de_las_reglas(self):
        t = va.prompt('r2', [('b01', libro('isbn-1'))], GEN)
        self.assertIn('b01 | Tisbn-1', t)
        self.assertNotIn('\nisbn-1 |', t)
        self.assertNotIn('A: pub=', t)


class Decision(unittest.TestCase):
    R = (frozenset({'terror'}), 'a')

    def test_r2_igual_a_las_reglas_acepta(self):
        e = {'r2': {'gen': ['terror'], 'pub': 'a', 'dudoso': False}}
        self.assertEqual(va.decidir(self.R, e), ('acepta', ['terror'], 'a', 'r2'))

    def test_r2_dudoso_o_distinto_pide_r3(self):
        self.assertEqual(va.decidir(self.R, {'r2': {'gen': ['terror'], 'pub': 'a', 'dudoso': True}}), ('r3',))
        self.assertEqual(va.decidir(self.R, {'r2': {'gen': ['fantasia'], 'pub': 'a', 'dudoso': False}}), ('r3',))

    def test_r3_coincide_con_r2_en_principal_y_publico(self):
        e = {'r2': {'gen': ['fantasia', 'romance', 'terror'], 'pub': 'j', 'dudoso': False},
             'r3': {'gen': ['fantasia', 'terror'], 'pub': 'j', 'dudoso': False}}
        self.assertEqual(va.decidir(self.R, e), ('acepta', ['fantasia', 'terror'], 'j', 'r2r3'))

    def test_r3_coincide_con_las_reglas(self):
        e = {'r2': {'gen': ['fantasia'], 'pub': 'a', 'dudoso': False}, 'r3': {'gen': ['terror'], 'pub': 'a', 'dudoso': False}}
        self.assertEqual(va.decidir(self.R, e), ('acepta', ['terror'], 'a', 'r3=reglas'))

    def test_desacuerdo_va_a_r4_y_baja_se_queda_con_reglas(self):
        e = {'r2': {'gen': ['fantasia'], 'pub': 'a', 'dudoso': False}, 'r3': {'gen': ['romance'], 'pub': 'a', 'dudoso': False}}
        self.assertEqual(va.decidir(self.R, e), ('r4',))
        e['r4'] = {'gen': ['romance'], 'pub': 'a', 'conf': 'media'}
        self.assertEqual(va.decidir(self.R, e), ('acepta', ['romance'], 'a', 'r4'))
        e['r4']['conf'] = 'baja'
        self.assertEqual(va.decidir(self.R, e), ('reglas',))

    def test_opciones_r4_barajan_segun_semilla(self):
        e = {'r2': {'gen': ['fantasia'], 'pub': 'a'}, 'r3': {'gen': ['romance'], 'pub': 'a'}}
        vistos = {va.opciones_r4(f's{n}', e)[0][0][0] for n in range(20)}
        self.assertEqual(vistos, {'fantasia', 'romance'})

    def test_orden_estable_y_distinto_por_semilla(self):
        ids = [f'isbn-{n}' for n in range(30)]
        self.assertEqual(va.orden(ids, 'a'), va.orden(list(reversed(ids)), 'a'))
        self.assertNotEqual(va.orden(ids, 'a'), va.orden(ids, 'b'))


class Cola(unittest.TestCase):
    def test_pendientes_por_huella_e_intentos(self):
        a, b, c, d = libro('isbn-a'), libro('isbn-b'), libro('isbn-c'), libro('isbn-d')
        data = catalogo(a, b, c, d, libro('isbn-x', estado='borrador'))
        veredictos = {'isbn-a': {'gen': ['terror'], 'pub': 'a'},                      # antiguo sin huella: vale
                      'isbn-b': {'gen': ['terror'], 'pub': 'a', 'h': 'otra'}}         # ficha cambiada: vuelve
        estado = {'isbn-c': {'h': va.huella(c), 'intentos': va.INTENTOS}}              # agotado con esta ficha
        self.assertEqual(va.pendientes(data, veredictos, estado), ['isbn-b', 'isbn-d'])
        c['descripcion_breve'] = 'sinopsis nueva'
        self.assertIn('isbn-c', va.pendientes(data, veredictos, estado))

    def test_etiquetas_de_las_reglas(self):
        data = catalogo(libro('isbn-a'), rels=[('isbn-a', 'terror'), ('isbn-a', 'juvenil'), ('isbn-b', 'infantil')])
        r = va.etiquetas_reglas(data)
        self.assertEqual(r['isbn-a'], (frozenset({'terror'}), 'j'))
        self.assertEqual(r['isbn-b'], (frozenset(), 'i'))


class Fusion(unittest.TestCase):
    def test_fusiona_sin_pisar_vigentes_ni_fichas_cambiadas(self):
        a, b, c = libro('isbn-a'), libro('isbn-b'), libro('isbn-c')
        with tempfile.TemporaryDirectory() as d:
            tree = Path(d)
            (tree / 'data').mkdir()
            (tree / 'data/reading-catalogue.json').write_text(json.dumps(catalogo(a, b, c)), encoding='utf-8')
            (tree / va.VERDICTS).write_text(json.dumps({'isbn-a': {'gen': ['romance'], 'pub': 'a'}}), encoding='utf-8')
            acept = lambda x, h: {'aceptado': {'gen': ['terror'], 'pub': 'a', 'h': h, 'm': 'r2', 'v': '1'}}
            estado = {'isbn-a': acept(a, va.huella(a)), 'isbn-b': acept(b, va.huella(b)), 'isbn-c': acept(c, 'vieja')}
            (tree / 'estado.json').write_text(json.dumps(estado), encoding='utf-8')
            self.assertEqual(va.fusionar(tree, tree / 'estado.json'), 1)
            out = json.loads((tree / va.VERDICTS).read_text(encoding='utf-8'))
            self.assertEqual(out['isbn-a'], {'gen': ['romance'], 'pub': 'a'})
            self.assertEqual(out['isbn-b']['gen'], ['terror'])
            self.assertNotIn('isbn-c', out)
            self.assertEqual(va.fusionar(tree, tree / 'estado.json'), 0)  # idempotente

    def test_el_publicador_acepta_el_fichero_de_veredictos(self):
        spec = importlib.util.spec_from_file_location('pub_refresh', ROOT / 'scripts/publish-reading-refresh.py')
        pub = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pub)
        self.assertTrue(pub.allowed_path(va.VERDICTS))


if __name__ == '__main__':
    unittest.main()
