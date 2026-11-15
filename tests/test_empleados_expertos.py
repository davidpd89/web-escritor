import importlib.util
import json
import re
import tempfile
import unittest
from unittest import mock
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('empleados_expertos', ROOT / 'scripts/empleados_expertos.py')
emp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(emp)
WORKFLOW = (ROOT / '.github/workflows/empleados-expertos.yml').read_text(encoding='utf-8')


class RotacionTests(unittest.TestCase):
    def test_cada_dia_un_rol_distinto_con_prompt(self):
        lunes = date(2026, 11, 16)
        roles = [emp.elegir(fecha=date.fromordinal(lunes.toordinal() + i)) for i in range(7)]
        self.assertEqual(len(set(roles)), 7)
        self.assertEqual(roles[0], 'investigador')  # semanal, condición R3-14
        for rol in roles + ['comun']:
            self.assertTrue((ROOT / '.github/empleados' / f'{rol}.md').exists(), rol)

    def test_seguridad_es_turno_extra_con_prompt_y_cron(self):
        self.assertEqual(emp.elegir('seguridad'), 'seguridad')
        self.assertTrue((ROOT / '.github/empleados/seguridad.md').exists())
        self.assertIn("cron: '47 5 * * 0'", WORKFLOW)
        self.assertIn("github.event.schedule == '47 5 * * 0'", WORKFLOW)

    def test_ficheros_sensibles_por_nombre(self):
        rutas = ['.env', '.env.local', '.env.example', 'a/id_rsa', 'x/clave.pem', 'docs/09-SECRETOS.md',
                 'recomendaciones/libros/el-secreto-123/index.html', 'credentials.json', 'b/.npmrc', 'c.key.md']
        self.assertEqual(emp.ficheros_sensibles(rutas),
                         ['.env', '.env.local', 'a/id_rsa', 'x/clave.pem', 'credentials.json', 'b/.npmrc'])

    def test_rol_forzado_y_desconocido(self):
        self.assertEqual(emp.elegir('geo'), 'geo')
        with self.assertRaises(SystemExit):
            emp.elegir('marketing')


class MuestraTests(unittest.TestCase):
    def test_portada_y_novedades_primero_y_sin_repetir(self):
        urls = ['https://x.es/'] + [f'https://x.es/autor/a{i}/' for i in range(50)] + \
               ['https://x.es/recomendaciones/pagina/2/', 'https://x.es/recomendaciones/'] + \
               [f'https://x.es/libro/{i}/' for i in range(200)]
        m = emp.ordenar_muestra(urls, 20)
        self.assertEqual(m[0], 'https://x.es/')
        self.assertIn('https://x.es/recomendaciones/', m[:5])
        self.assertIn('https://x.es/recomendaciones/pagina/2/', m)
        self.assertEqual(len(m), len(set(m)))
        self.assertLessEqual(len(m), 20)

    def test_sitemap_lee_loc(self):
        xml = '<urlset><url><loc> https://x.es/a/ </loc></url><url><loc>https://x.es/b/</loc></url></urlset>'
        self.assertEqual(emp.urls_sitemap(xml), ['https://x.es/a/', 'https://x.es/b/'])
        self.assertEqual(emp.urls_sitemap('<loc>https://x.es/?a=1&amp;b=2</loc>'), ['https://x.es/?a=1&b=2'])

    def test_robots_hereda_el_comodin(self):
        bloqueo = dict(emp.robots_bots('User-agent: *\nDisallow: /\n', 'https://x.es'))
        self.assertEqual(set(bloqueo.values()), {'BLOQUEADO'})
        mixto = dict(emp.robots_bots('User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n', 'https://x.es'))
        self.assertEqual(mixto['GPTBot'], 'BLOQUEADO')
        self.assertEqual(mixto['ClaudeBot'], 'permitido')


class ResumenTests(unittest.TestCase):
    def test_siteone_ordena_por_gravedad_y_omite_ok(self):
        datos = {'summary': {'items': [
            {'aplCode': 'a', 'status': 'OK', 'text': 'bien'},
            {'aplCode': 'b', 'status': 'NOTICE', 'text': 'aviso'},
            {'aplCode': 'c', 'status': 'CRITICAL', 'text': 'grave'}]}}
        texto = emp.resumir_siteone(datos)
        self.assertLess(texto.index('grave'), texto.index('aviso'))
        self.assertNotIn('bien', texto)

    def test_siteone_sin_json_no_rompe(self):
        with tempfile.TemporaryDirectory() as d:
            salida = Path(d) / 'r.md'
            with mock.patch.object(emp, 'DATOS', Path(d).resolve()):
                emp.main(['resumir-siteone', '--json', str(Path(d) / 'no.json'), '--salida', str(salida)])
            self.assertIn('CRITICAL', salida.read_text(encoding='utf-8'))

    def test_rutas_fuera_de_datos_se_rechazan(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(emp, 'DATOS', Path(d).resolve()):
            self.assertEqual(emp.ruta_segura(str(Path(d) / 'a.md')), Path(d).resolve() / 'a.md')
            with self.assertRaises(ValueError):
                emp.ruta_segura(str(Path(d) / '..' / 'fuera.md'))

    def test_solo_https_del_sitio_propio(self):
        self.assertEqual(emp.url_segura('https://davidportodiaz.com/x?a=1'), 'https://davidportodiaz.com/x?a=1')
        for mala in ('http://davidportodiaz.com/', 'https://evil.com/', 'https://davidportodiaz.com.evil.com/',
                     'https://u@davidportodiaz.com/', 'file:///etc/passwd', 'https://davidportodiaz.com:8080/'):
            with self.assertRaises(ValueError, msg=mala):
                emp.url_segura(mala)

    def test_titulo_y_canonical_sin_regex(self):
        p = emp.leer_pagina('<html><head><title> Hola </title><link href="https://x/" rel="canonical"></head></html>')
        self.assertEqual(p.titulo.strip(), 'Hola')
        self.assertTrue(p.canonical)
        self.assertFalse(emp.leer_pagina('<title>t</title>').canonical)

    def test_jsonld_tipos_y_roto(self):
        html = ('<script type="application/ld+json">' + json.dumps({'@graph': [{'@type': 'Book'}, {'@type': ['Offer']}]}) +
                '</script><script type="application/ld+json">{roto</script>')
        tipos, errores = emp.revisar_jsonld(html)
        self.assertEqual(sorted(tipos), ['Book', 'Offer'])
        self.assertEqual(errores, 1)


class ContratoWorkflowTests(unittest.TestCase):
    def test_solo_schedule_y_dispatch(self):
        bloque_on = WORKFLOW.split('\non:\n', 1)[1].split('\npermissions:', 1)[0]
        disparadores = re.findall(r'^  (\w+):', bloque_on, re.M)
        self.assertEqual(disparadores, ['schedule', 'workflow_dispatch'])

    def test_permisos_minimos_y_experto_gratuito(self):
        # Sin tokens de Claude: el experto es GitHub Models con el GITHUB_TOKEN del run.
        self.assertIn('permissions:\n  contents: read\n  issues: write\n  models: read\n', WORKFLOW)
        self.assertNotIn('pull-requests: write', WORKFLOW)
        self.assertNotIn('claude-code-action', WORKFLOW)
        self.assertNotIn('CLAUDE_CODE_OAUTH_TOKEN', WORKFLOW)
        self.assertNotIn('ANTHROPIC', WORKFLOW)
        self.assertIn('empleados_expertos.py experto --rol "$ROL"', WORKFLOW)

    def test_sin_expresiones_en_run(self):
        # Las salidas de pasos entran por env, no interpoladas en el script (inyección).
        for bloque in re.findall(r'run: \|\n((?:          .*\n)+)', WORKFLOW):
            self.assertNotIn('${{', bloque)


class ModeloTests(unittest.TestCase):
    def test_propuestas_solo_completas_y_como_mucho_tres(self):
        completa = {'titulo': 't', 'evidencia': 'e', 'impacto': 'i', 'arreglo': 'a', 'comprobar': 'c'}
        texto = json.dumps({'issues': [completa, {'titulo': 'sin resto'}] + [dict(completa, titulo=f't{n}') for n in range(5)]})
        props = emp.propuestas(texto)
        self.assertEqual(len(props), 3)
        self.assertNotIn('sin resto', [p['titulo'] for p in props])
        self.assertEqual(emp.propuestas('no es json'), [])
        self.assertEqual(emp.propuestas('{"issues": []}'), [])

    def test_sin_menciones_en_el_cuerpo(self):
        p = {'titulo': 'x', 'evidencia': 'avisa a @david', 'impacto': 'i', 'arreglo': '@org/equipo', 'comprobar': 'c'}
        cuerpo = emp.cuerpo_issue(p, 'seo', 'openai/gpt-4.1')
        self.assertNotRegex(cuerpo, r'@[A-Za-z]')
        self.assertIn('**Evidencia**', cuerpo)

    def test_respuesta_no_valida_pasa_al_siguiente_y_acaba_en_rojo(self):
        with mock.patch.object(emp, '_pedir_modelo', side_effect=ValueError('OK')),                 mock.patch.object(emp, 'datos_rol', return_value='datos'),                 tempfile.TemporaryDirectory() as d, mock.patch.object(emp, 'DATOS', Path(d)):
            with self.assertRaises(SystemExit):
                emp.experto('seo', dry=True)

    def test_publicar_salta_titulos_ya_abiertos(self):
        props = [{'titulo': 'ya existe', 'evidencia': 'e', 'impacto': 'i', 'arreglo': 'a', 'comprobar': 'c'},
                 {'titulo': 'nueva', 'evidencia': 'e', 'impacto': 'i', 'arreglo': 'a', 'comprobar': 'c'}]
        llamadas = []
        def gh(*args):
            llamadas.append(args)
            return 'seo: ya existe\notra\n' if args[:2] == ('issue', 'list') else ''

        with mock.patch.object(emp, '_gh', gh), tempfile.TemporaryDirectory() as d, \
                mock.patch.object(emp, 'DATOS', Path(d)):
            creadas = emp.publicar(props, 'seo', 'm', dry=True)
        self.assertEqual(creadas, ['seo: nueva'])
        self.assertFalse([a for a in llamadas if a[:2] == ('issue', 'create')])


if __name__ == '__main__':
    unittest.main()
