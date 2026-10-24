#!/usr/bin/env python3
"""Pruebas reales offline del descubrimiento, estados, revisión y parche en laboratorio."""
import json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"motor"))
sys.path.insert(0,str(HERE))
from motor import descubrimiento, ciclo, pr_laboratorio

class Fuentes(unittest.TestCase):
    def test_rss_primario(self):
        xml=b'<rss><channel><item><title>New guide</title><link>https://developers.google.com/search/docs/foo</link><pubDate>Sat, 24 Oct 2026 10:00:00 +0000</pubDate></item></channel></rss>'
        x=descubrimiento.feed(xml)
        self.assertEqual(x[0]["publicado"],"2026-10-24")
        self.assertEqual(len(x),1)

    def test_rss_no_acepta_enlace_externo(self):
        xml=b'<rss><channel><item><title>Ignore</title><link>https://evil.invalid/test</link><pubDate>Sat, 24 Oct 2026 10:00:00 +0000</pubDate></item></channel></rss>'
        self.assertEqual(descubrimiento.feed(xml),[])

    def test_rss_malformado_no_es_novedad(self):
        with self.assertRaises(descubrimiento.FuenteError):
            descubrimiento.feed(b'<?xml version="1.0"?><bad>')

    def test_github_sin_necesidad_de_red(self):
        item={"items":[{"full_name":"org/project","html_url":"https://github.com/org/project",
                         "pushed_at":"2026-10-24T12:00:00Z","description":"Code",
                         "fork":False,"archived":False,"stargazers_count":430,
                         "default_branch":"main","license":{"spdx_id":"MIT"}}]}
        out=descubrimiento.github("github","SEO",fetch=lambda url:item)
        self.assertEqual(out[0]["licencia_declarada"],"MIT")
        self.assertEqual(out[0]["tipo"],"repositorio")

    def test_github_error_en_vez_de_inventar(self):
        with self.assertRaises(descubrimiento.FuenteError):
            descubrimiento.github("api","DAT",fetch=lambda url:{"message":"rate limit"})

    def test_novedad_y_huella_estable(self):
        fuente={"url":"https://github.com/Pagefind/pagefind","publicado":descubrimiento.hoy().isoformat()}
        self.assertEqual(len(descubrimiento.nuevas([fuente])),1)
        self.assertEqual(descubrimiento.nuevas([fuente],[descubrimiento.huella(fuente)]),[])


class Parche(unittest.TestCase):
    def test_rutas_prohibidas(self):
        for ruta in ("../main.py",".github/workflows/deploy.yml","scripts/qa-gpt/qa_gpt.py",
                     "package.json","C:/credentials.txt","experimentos/mejoras-web/rotacion.py"):
            with self.subTest(ruta=ruta): self.assertFalse(pr_laboratorio.ruta_segura(ruta))

    def test_reemplazos_unicos_y_aplicacion(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"script.js").write_text("const x = 1;",encoding="utf-8")
            p={"ficheros":[{"ruta":"script.js","reemplazos":[{"buscar":"x = 1","por":"x = 2"}]}],
               "tests":["tests/test_script.py"]}
            self.assertEqual(pr_laboratorio.comprobar_parche(p,root),["script.js"])
            self.assertEqual(pr_laboratorio.aplicar_parche(p,root),["script.js"])
            self.assertIn("x = 2",(root/"script.js").read_text(encoding="utf-8"))

    def test_reemplazo_ambiguo_rechazado(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"script.js").write_text("x x",encoding="utf-8")
            p={"ficheros":[{"ruta":"script.js","reemplazos":[{"buscar":"x","por":"y"}]}]}
            with self.assertRaises(pr_laboratorio.PreparacionError):
                pr_laboratorio.comprobar_parche(p,root)

    def test_sin_tests_no_hay_pr(self):
        with self.assertRaises(pr_laboratorio.PreparacionError):
            pr_laboratorio.comandos_test({"tests":[]})

    def test_no_se_inyectan_comandos_shell(self):
        with self.assertRaises(pr_laboratorio.PreparacionError):
            pr_laboratorio.comandos_test({"tests":["python -c 'print(1)'"]})


class Flujo(unittest.TestCase):
    def tarea(self):
        return {"id":"A-01","familia":"SEO","canal":"github",
                "titulo":"Un caso de prueba"}

    def test_cadena_simulada_sin_red(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            calls=[]
            def rotador(_dir,*args):
                calls.append(args)
                if args[0]=="--siguiente":
                    return {"disponible":True,"tarea":self.tarea()}
                if args[0]=="--resultado": return {"cerrada":"A-01"}
                raise AssertionError(args)
            with mock.patch.object(ciclo,"comando_rotacion",side_effect=rotador):
                estados=[]
                for _ in range(4):
                    s=ciclo.paso(d,simular=True)
                    estados.append(s["fase"])
                self.assertEqual(estados,["seleccionado","fuente","gpt_completo","ampliacion"])
                self.assertFalse((d/"historial.json").exists(), "Claude pide ampliar: NO cerrar ni saltar tema")
                for _ in range(4):
                    s=ciclo.paso(d,simular=True)
                self.assertEqual(s["fase"],"pendiente_revision", "Dos ampliaciones y después revisión humana")
                self.assertTrue((d/"historial.json").exists())
                self.assertEqual(ciclo.leer(d/"actual.json",{})["id"],"A-01")
                self.assertIn(("--resultado","pendiente_revision"),calls)

    def test_sondeo_continuo_despues_de_agotar_semillas(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            with mock.patch.object(ciclo,"comando_rotacion",return_value={"disponible":False}):
                task,typ=ciclo.reservar(d)
                self.assertEqual(typ,"sondeo")
                self.assertTrue(task["id"].startswith("SONDEO-"))
                self.assertIn(task["canal"],descubrimiento.ANGULOS.keys()|{"web","auditoria_local"})

    def test_validacion_exige_codigo_y_fuente(self):
        fuente={"url":"https://github.com/org/repo"}
        d={k:"contenido verificado y reproducible" for k in ciclo.GPT_KEYS}
        d["fuente_url"]="https://github.com/otro/repo"
        with self.assertRaises(ValueError): ciclo.validar_investigacion(d,fuente)

    def test_no_pasar_automáticamente_a_merge(self):
        self.assertEqual(pr_laboratorio.BASE,"lab/mejoras-web-20261024")
        self.assertFalse(hasattr(pr_laboratorio,"fusionar_main"))

    def test_documentacion_sin_codigo_externo_pero_con_fecha(self):
        fuente={"url":"https://developers.google.com/search/docs/foo"}
        datos={k:"Información verificable y justificada" for k in ciclo.GPT_KEYS}
        datos["fuente_url"]=fuente["url"]
        datos["fecha_fuente"]="2026-10-24"
        self.assertIs(ciclo.validar_investigacion(datos,fuente),datos)
        datos.pop("fecha_fuente")
        with self.assertRaises(ValueError): ciclo.validar_investigacion(datos,fuente)

    def test_repositorio_exige_bloque_original(self):
        fuente={"url":"https://github.com/org/repo"}
        datos={k:"Información verificable y justificada" for k in ciclo.GPT_KEYS}
        datos["fuente_url"]=fuente["url"]
        with self.assertRaises(ValueError): ciclo.validar_investigacion(datos,fuente)

    def test_un_director_y_no_dos(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            with ciclo.exclusivo(d):
                with self.assertRaises(RuntimeError):
                    with ciclo.exclusivo(d):
                        self.fail("No debe coexistir un segundo director")
            self.assertFalse((d/"director.lock").exists())

    def test_riesgo_alto_de_claude_no_desarrolla(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            s={"id":"A-01","fase":"gpt_completo","tipo":"sondeo",
               "tarea":self.tarea(),"chats":{},
               "investigacion":{"problema":"Caso"}} 
            ciclo.guardar(d/"actual.json",s)
            dictamen={"decision":"aprobar","riesgo":"alto","duplicado":False,
                     "motivo":"No debe ejecutarse sin revisión humana"}
            with mock.patch.object(ciclo,"revisar",return_value=dictamen):
                result=ciclo.paso(d)
            self.assertEqual(result["fase"],"pendiente_revision")

    def test_segunda_revision_de_parche_obligatoria(self):
        with tempfile.TemporaryDirectory() as temp:
            d=Path(temp)
            s={"id":"A-01","fase":"parche_propuesto","tipo":"sondeo",
               "tarea":self.tarea(),"parche":{"ficheros":[],"tests":[]},
               "investigacion":{},"revision":{"decision":"aprobar"}}
            ciclo.guardar(d/"actual.json",s)
            r={"decision":"rechazar","riesgo":"medio","duplicado":False,
               "motivo":"El parche aún no tiene justificación suficiente"}
            with mock.patch.object(ciclo,"revisar_parche",return_value=r):
                result=ciclo.paso(d)
            self.assertEqual(result["fase"],"pendiente_revision")

    def test_recuperar_pr_tras_push_sin_duplicar_otra_rama(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            state=root/"estado"
            expediente={"id":"A-01","titulo":"Una mejora","fuente":{"url":"https://github.com/org/p"},
                        "veredicto":"aprobar"}
            patch={"ficheros":[{"ruta":"styles.css","reemplazos":[{"buscar":"red","por":"blue"}]}],
                   "tests":["tests/test_styles.py"]}
            tag=pr_laboratorio.identificador(expediente)
            rama="feature/mejoras-web/"+tag
            wt=state/"worktrees"/tag
            wt.mkdir(parents=True)
            calls=[]
            def fake_run(args,cwd,timeout=240,extra_env=None):
                calls.append(args)
                if args[:3]==["gh","pr","list"]: return "[]"
                if args[:3]==["git","branch","--show-current"]: return rama
                if args[:2]==["git","status"]: return ""
                if args[:3]==["git","rev-list","--count"]: return "1"
                if args[:3]==["git","diff","--name-only"]: return "styles.css"
                if args[:3]==["gh","pr","create"]: return "https://github.com/davidpd89/web-escritor/pull/9900"
                return ""
            with mock.patch.object(pr_laboratorio,"validar_contexto",return_value="lab/mejoras-local"), \
                 mock.patch.object(pr_laboratorio,"run",side_effect=fake_run), \
                 mock.patch.object(pr_laboratorio,"ejecutar_tests",return_value=[("tests/test_styles.py","PASS")]):
                result=pr_laboratorio.abrir_pr(root,state,expediente,patch,publicar=True)
            self.assertEqual(result["estado"],"pr_borrador")
            self.assertIn("--base",next(x for x in calls if x[:3]==["gh","pr","create"]))
            self.assertEqual(result["rama"],rama)


if __name__=="__main__": unittest.main()
