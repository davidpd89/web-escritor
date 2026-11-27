"""Reparto del sitio en Workers Static Assets: cada URL la atiende un Worker que tiene su fichero."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reparto_workers as rw  # noqa: E402

BASE = {'host': 'h.example.com', 'zona': 'example.com', 'nucleo': 'core', 'prefijo_worker': 'frag',
        'compatibility_date': '2026-11-27', 'noindex': True, 'bloqueante': False,
        'objetivo_ficheros': 4, 'umbral_ficheros': 6, 'maximo_ficheros': 8, 'fragmentos': []}


def sitio(slugs, extra=()):
    rels = ['index.html', '404.html', 'recomendaciones/libros/index.html']
    rels += [f'recomendaciones/libros/{s}/index.html' for s in slugs]
    return sorted(rels + list(extra))


def servido_por(rel_url, plan):
    return rw.worker_de_url(rel_url, rw.indice_prefijos(plan), plan['nucleo'])


class Asignar(unittest.TestCase):
    def test_every_url_of_every_file_is_served_by_a_worker_that_has_the_file(self):
        plan = dict(BASE, fragmentos=[{'worker': 'frag-01', 'prefijos': ['recomendaciones/libros/a']},
                                      {'worker': 'frag-02', 'prefijos': ['recomendaciones/libros/i']}])
        rels = sitio(['abeja', 'ana', 'coraline']) + ['recomendaciones/libros/indice.html']
        asignacion = rw.asignar(rels, plan)
        for rel in rels:
            for url in rw.urls_de(rel):
                self.assertIn(rel, asignacion[servido_por(url, plan)], f'{url} -> {rel}')

    def test_listing_index_stays_in_core_even_if_a_prefix_matches_its_filename(self):
        plan = dict(BASE, fragmentos=[{'worker': 'frag-01', 'prefijos': ['recomendaciones/libros/i']}])
        asignacion = rw.asignar(sitio(['ines']), plan)
        self.assertIn('recomendaciones/libros/index.html', asignacion['core'])        # sirve /libros/ y /libros
        self.assertIn('recomendaciones/libros/index.html', asignacion['frag-01'])     # sirve /libros/index.html
        self.assertNotIn('recomendaciones/libros/ines/index.html', asignacion['core'])

    def test_longest_prefix_wins_like_cloudflare_routes(self):
        plan = dict(BASE, fragmentos=[{'worker': 'frag-01', 'prefijos': ['recomendaciones/libros/c']},
                                      {'worker': 'frag-02', 'prefijos': ['recomendaciones/libros/co']}])
        self.assertEqual(servido_por('recomendaciones/libros/coraline/', plan), 'frag-02')
        self.assertEqual(servido_por('recomendaciones/libros/cielo/', plan), 'frag-01')

    def test_control_files_are_not_uploaded(self):
        self.assertNotIn('_headers', rw.asignar(['_headers', 'index.html'], BASE)['core'])


class Comprobar(unittest.TestCase):
    def test_warns_over_threshold_and_fails_over_maximum(self):
        plan = dict(BASE)
        _, avisos = rw.comprobar(plan, {'core': ['x'] * 7})
        self.assertTrue(avisos)
        errores, _ = rw.comprobar(plan, {'core': ['x'] * 9})
        self.assertTrue(errores)

    def test_rejects_empty_repeated_or_wildcard_prefixes(self):
        for prefijos in ([''], ['a*'], ['/a']):
            plan = dict(BASE, fragmentos=[{'worker': 'frag-01', 'prefijos': prefijos}])
            self.assertTrue(rw.comprobar(plan, {'core': [], 'frag-01': ['a']})[0], prefijos)
        plan = dict(BASE, fragmentos=[{'worker': 'frag-01', 'prefijos': ['a']}, {'worker': 'frag-02', 'prefijos': ['a']}])
        self.assertTrue(rw.comprobar(plan, {'core': [], 'frag-01': ['a'], 'frag-02': []})[0])


class Planificar(unittest.TestCase):
    def test_splits_the_widest_folder_until_every_worker_fits(self):
        slugs = ['abeja', 'ana', 'arco', 'boca', 'bruma', 'cielo', 'coraline', 'duna', 'eco', 'faro']
        rels = sitio(slugs)
        plan = rw.planificar(rels, BASE)
        self.assertTrue(plan['fragmentos'])
        asignacion = rw.asignar(rels, plan)
        self.assertEqual(rw.comprobar(plan, asignacion), ([], []))
        self.assertLessEqual(len(asignacion['core']), BASE['objetivo_ficheros'])
        for f in plan['fragmentos']:
            for p in f['prefijos']:
                self.assertTrue(p.startswith('recomendaciones/libros/') and len(p) > len('recomendaciones/libros/'))
        for rel in rels:
            for url in rw.urls_de(rel):
                self.assertIn(rel, asignacion[servido_por(url, plan)])

    def test_small_site_needs_no_fragments(self):
        self.assertEqual(rw.planificar(sitio(['a']), BASE)['fragmentos'], [])


class Repartir(unittest.TestCase):
    def test_writes_one_wrangler_project_per_worker_with_404_and_noindex(self):
        plan = dict(BASE, fragmentos=[{'worker': 'frag-01', 'prefijos': ['recomendaciones/libros/a']}])
        with tempfile.TemporaryDirectory() as tmp:
            dist, out = Path(tmp) / 'dist', Path(tmp) / 'out'
            for rel in sitio(['ana', 'coraline']):
                (dist / rel).parent.mkdir(parents=True, exist_ok=True)
                (dist / rel).write_text(rel, encoding='utf-8')
            _, errores, _ = rw.repartir(dist, out, plan)
            self.assertEqual(errores, [])
            core = json.loads((out / 'core/wrangler.jsonc').read_text(encoding='utf-8'))
            frag = json.loads((out / 'frag-01/wrangler.jsonc').read_text(encoding='utf-8'))
            self.assertEqual(core['routes'], [{'pattern': 'h.example.com', 'custom_domain': True}])
            self.assertNotIn('routes', frag)  # las rutas las sincroniza la API: un PUT cambia de Worker sin hueco
            self.assertTrue((out / 'frag-01/dist/404.html').exists())
            self.assertTrue((out / 'frag-01/dist/recomendaciones/libros/ana/index.html').exists())
            self.assertFalse((out / 'core/dist/recomendaciones/libros/ana').exists())
            self.assertIn('noindex', (out / 'frag-01/dist/_headers').read_text(encoding='utf-8'))
            resumen = json.loads((out / 'reparto.json').read_text(encoding='utf-8'))
            self.assertEqual(resumen['rutas'], {'h.example.com/recomendaciones/libros/a*': 'frag-01'})


class SincronizarRutas(unittest.TestCase):
    def test_moves_creates_and_deletes_only_routes_of_its_host(self):
        llamadas = []
        actuales = [{'id': '1', 'pattern': 'h.example.com/x/a*', 'script': 'frag-02'},
                    {'id': '2', 'pattern': 'h.example.com/x/z*', 'script': 'frag-01'},
                    {'id': '3', 'pattern': 'otro.example.com/*', 'script': 'ajeno'}]

        def api(metodo, ruta, token, cuerpo=None):
            llamadas.append((metodo, ruta, cuerpo))
            if ruta.startswith('/zones?'):
                return [{'id': 'Z'}]
            return actuales if metodo == 'GET' else {}

        resumen = {'zona': 'example.com', 'host': 'h.example.com',
                   'rutas': {'h.example.com/x/a*': 'frag-01', 'h.example.com/x/b*': 'frag-01'}}
        rw.sincronizar_rutas(resumen, 't', api=api)
        cambios = [(m, r, c) for m, r, c in llamadas if m != 'GET']
        self.assertIn(('PUT', '/zones/Z/workers/routes/1', {'pattern': 'h.example.com/x/a*', 'script': 'frag-01'}), cambios)
        self.assertIn(('DELETE', '/zones/Z/workers/routes/2', None), cambios)
        self.assertIn(('POST', '/zones/Z/workers/routes', {'pattern': 'h.example.com/x/b*', 'script': 'frag-01'}), cambios)
        self.assertFalse([c for c in cambios if c[1].endswith('/3')])


class Huerfanos(unittest.TestCase):
    def test_deletes_only_old_fragments_without_routes(self):
        borrados = []

        def api(metodo, ruta, token, cuerpo=None):
            if ruta.startswith('/zones?'):
                return [{'id': 'Z'}]
            if ruta.endswith('/workers/routes'):
                return [{'pattern': 'h/x*', 'script': 'frag-viejo-con-ruta'}]
            if metodo == 'GET':
                return [{'id': n} for n in ('frag-aaaa', 'frag-viejo', 'frag-viejo-con-ruta', 'core', 'ajeno')]
            borrados.append(ruta)

        resumen = {'zona': 'example.com', 'prefijo_worker': 'frag', 'workers': {'core': 1, 'frag-aaaa': 1}}
        self.assertEqual(rw.borrar_huerfanos(resumen, 't', 'A', api=api), ['frag-viejo'])
        self.assertEqual(borrados, ['/accounts/A/workers/scripts/frag-viejo'])

    def test_fragment_name_depends_only_on_its_prefixes(self):
        nombre = rw.nombre_fragmento(BASE, ['a', 'b'])
        self.assertEqual(nombre, rw.nombre_fragmento(dict(BASE, host='otro.example.com'), ['a', 'b']))
        self.assertRegex(nombre, rw.NOMBRE_WORKER)
        self.assertNotEqual(rw.nombre_fragmento(BASE, ['a', 'b']), rw.nombre_fragmento(BASE, ['a']))


class Validar(unittest.TestCase):
    def test_rejects_names_that_could_become_command_options_or_other_hosts(self):
        bueno = {'workers': {'core': 1, 'frag-ab12': 1}, 'host': 'h.example.com', 'zona': 'example.com'}
        self.assertIs(rw.validar_resumen(bueno), bueno)
        for malo in (dict(bueno, workers={'--config=x': 1}), dict(bueno, host='evil.com/x?'), dict(bueno, zona='a b')):
            with self.assertRaises(ValueError):
                rw.validar_resumen(malo)


class PlanVersionado(unittest.TestCase):
    def test_repo_plan_is_valid(self):
        plan = rw.leer_plan()
        for clave in ('host', 'zona', 'nucleo', 'umbral_ficheros', 'maximo_ficheros', 'fragmentos'):
            self.assertIn(clave, plan)
        self.assertLess(plan['umbral_ficheros'], plan['maximo_ficheros'])
        self.assertLessEqual(plan['maximo_ficheros'], 20000)  # tope de ficheros por versión en Workers Free


if __name__ == '__main__':
    unittest.main()
