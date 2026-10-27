import json, unittest
from pathlib import Path
import util
import mw, claude_cli, gpt_browser, dedupe


def respuesta(obj, bloque=True):
    t = json.dumps(obj, ensure_ascii=False)
    return f"```json\n{t}\n```" if bloque else t


def ask_con(texto, calls=None, cid="c" * 32):
    def ask(question, wait_min, stall_min, on_chat=None, on_result=None, resume_cid=None, registro=None):
        if calls is not None: calls.append({"resume": resume_cid, "question": question})
        c = resume_cid or cid
        if not resume_cid and on_chat: on_chat(c)
        res = gpt_browser.Resultado("terminada", texto, c, 4, 7)
        on_result(res); return res
    return ask


class Rotacion(util.Caso):
    def test_no_se_agota_nunca_y_cada_vuelta_reordena(self):
        n = len(self.inv.lista_pares()); vistos, ordenes = set(), []
        for vuelta in range(3):
            orden = []
            for _ in range(n):
                a, l, ep = self.inv.elegir_par(self.c); self.assertEqual(ep, vuelta)
                orden.append((a, l)); self.inv.marcar_par(self.c, a, l)
            self.assertEqual(len(set(orden)), n)  # cada par exactamente una vez por vuelta
            ordenes.append(orden)
        self.assertNotEqual(ordenes[0], ordenes[1]); self.assertNotEqual(ordenes[1], ordenes[2])
        self.assertEqual(self.inv.elegir_par(self.c)[2], 3)  # y sigue: no hay catalogo que se acabe
        self.assertGreaterEqual(n, 100)

    def test_job_en_error_con_la_misma_clave_se_reintenta_y_no_atasca_el_servicio(self):
        self.assertTrue(self.inv.encolar_investigacion(self.c))
        j = self.inv.next_job(self.c)
        self.c.execute("UPDATE jobs SET estado='error', intentos=3, no_antes='2099-01-01T00:00:00' WHERE id=?", (j["id"],)); self.c.commit()
        self.assertIsNone(self.inv.next_job(self.c))
        self.assertTrue(self.inv.encolar_investigacion(self.c))
        r = self.inv.next_job(self.c)
        self.assertEqual((r["clave"], r["estado"], r["intentos"]), (j["clave"], "pendiente", 0))



class Investigacion(util.Caso):
    def procesar(self, job, texto):
        self.inv.ASK = ask_con(texto); self.inv.procesar_job(self.c, job)

    def test_generacion_de_una_propuesta_persistida(self):
        j = self.job(); self.procesar(j, respuesta(self.investigacion()))
        e = self.c.execute("SELECT * FROM expedientes").fetchone()
        self.assertEqual(e["estado"], "investigado"); self.assertEqual(e["id"], "MW-0001"); self.assertEqual(e["area"], "accesibilidad")
        self.assertTrue(e["h_necesidad"] and e["h_comportamiento"])
        self.assertEqual(self.c.execute("SELECT estado FROM jobs").fetchone()[0], "hecho")
        p = self.c.execute("SELECT * FROM peticiones").fetchone(); self.assertEqual((p["ok"], p["estado"]), (1, "terminada"))
        self.assertEqual(self.c.execute("SELECT veces FROM pares WHERE par='accesibilidad|1'").fetchone()[0], 1)
        self.assertTrue(list((mw.STATE / "respuestas").glob("job1_*.txt")))  # la respuesta queda en disco antes de ingerir

    def test_gpt_puede_descartar_sin_codigo(self):
        self.procesar(self.job(), respuesta({"descartar": True, "motivo_descarte": "El sitio ya cubre esto con enlaces de salto en todas las paginas."}))
        e = self.c.execute("SELECT * FROM expedientes").fetchone(); self.assertEqual(e["estado"], "descartado_gpt"); self.assertIsNone(e["parche"])
        self.assertIn("ya cubre", e["motivo"])

    def test_descartar_sin_motivo_es_invalido(self):
        j = self.job(); self.procesar(j, respuesta({"descartar": True}))
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM expedientes").fetchone()[0], 0)
        self.assertEqual(self.c.execute("SELECT estado FROM jobs").fetchone()[0], "pendiente")

    def test_archivos_leidos_inventados_se_rechazan(self):
        d = self.investigacion(); d["estado_sitio"] = {"archivos_leidos": ["no/existe.html", "tampoco.js"], "observacion": "Lei los archivos y no tienen skip link para nada."}
        j = self.job(); self.procesar(j, respuesta(d))
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM expedientes").fetchone()[0], 0)
        r = self.c.execute("SELECT * FROM jobs").fetchone(); self.assertEqual(r["estado"], "pendiente"); self.assertIn("no existen", r["error"]); self.assertIsNone(r["chat_id"])

    def test_forma_invalida_no_crea_expediente(self):
        d = self.investigacion(fuentes=[{"url": "ftp://x", "titulo": "t"}], necesidad="corta")
        self.procesar(self.job(), respuesta(d))
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM expedientes").fetchone()[0], 0)

    def test_duplicado_por_necesidad_aunque_cambien_titulo_y_fuente(self):
        self.procesar(self.job(), respuesta(self.investigacion()))
        d2 = self.investigacion(titulo="Saltar bloques repetidos con teclado", necesidad="Un lector que navega con teclado no puede saltar directamente al contenido principal de cada pagina sin tabular todo el menu.",
                                fuentes=[{"url": "https://developer.mozilla.org/es/docs/Web/Accessibility", "titulo": "MDN", "fecha": "2025-02-02", "afirma": "x"}])
        self.procesar(self.job(), respuesta(d2))
        e = self.c.execute("SELECT * FROM expedientes WHERE id='MW-0002'").fetchone()
        self.assertEqual(e["estado"], "duplicado"); self.assertEqual(e["duplicado_de"], "MW-0001")

    def test_distinta_necesidad_aunque_misma_fuente_no_es_duplicado(self):
        self.procesar(self.job(), respuesta(self.investigacion()))
        d2 = self.investigacion(titulo="Fecha de actualizacion en las fichas", necesidad="Las fichas de libros no muestran cuando se revisaron por ultima vez los datos bibliograficos publicados.",
                                propuesta="Mostrar la fecha de la ultima revision de cada ficha leyendola del JSON de datos al generar la pagina.", archivos_objetivo=["libros/ficha.html"],
                                criterio_aceptacion="Cada ficha incluye un elemento time con la fecha de revision de los datos.")
        self.procesar(self.job(), respuesta(d2))
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes WHERE id='MW-0002'").fetchone()[0], "investigado")

    def test_prompt_incluye_lista_de_lo_ya_investigado_y_la_rama(self):
        self.procesar(self.job(), respuesta(self.investigacion()))
        j2 = self.job(payload={"area": "rendimiento", "lente": 0, "epoca": 0}, area="rendimiento|0")
        txt = self.inv.prompt_investigar(j2, self.c)
        self.assertIn("Enlace para saltar al contenido principal", txt); self.assertIn("lab/mejoras-web-20261024", txt); self.assertNotIn("{{", txt)


class ProjectCompartido(util.Caso):
    """El Project puede llevar las instrucciones del QA: cada prompt del laboratorio debe prevalecer sobre ellas y no pedir nada que choque."""
    def test_los_prompts_declaran_que_no_son_qa_y_fijan_el_esquema(self):
        j = self.job(); t1 = self.inv.prompt_investigar(j, self.c)
        self.c.execute("INSERT INTO expedientes(id,area,lente,titulo,necesidad,estado,datos,contraste,intentos_parche,creado,actualizado) VALUES('MW-0001','a','1','t',?,'desarrollando',?,'{}',1,?,?)", ("n" * 50, json.dumps(self.investigacion()), mw.now(), mw.now()))
        self.inv.encolar_desarrollo(self.c, "MW-0001"); t2 = self.inv.prompt_desarrollar(self.c.execute("SELECT * FROM jobs WHERE tipo='D'").fetchone(), self.c)
        for t in (t1, t2):
            self.assertIn("AVISO DE CONTEXTO", t); self.assertIn("NO es una ronda de QA", t); self.assertIn("SI debes proponer cambios de produccion", t)
            self.assertIn("lab/mejoras-web-20261024", t); self.assertIn("UNICAMENTE con el JSON", t)
        self.assertTrue(t1.startswith("[INVESTIGACION DE MEJORAS WEB")); self.assertTrue(t2.startswith("[DESARROLLO DE MEJORA WEB"))  # la primera linea es la que reconoce el Project

    def test_la_respuesta_con_campos_extra_de_qa_se_acepta_si_cumple_el_esquema(self):
        d = self.investigacion(); d.update(lectura_repo={"commit": "abc", "ficheros": ["index.html"]}, propuestas=[]); j = self.job()
        self.inv.ASK = ask_con(respuesta(d)); self.inv.procesar_job(self.c, j)
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "investigado")

    def test_instrucciones_del_project_compartido_documentadas(self):
        t = (mw.LAB / "project_instructions.md").read_text(encoding="utf-8")
        self.assertIn("Si el Project se COMPARTE con el QA GPT", t); self.assertIn("[INVESTIGACION DE MEJORAS WEB", t)


class Reanudacion(util.Caso):
    def test_chat_conservado_tras_corte_y_reanudado_sin_reenviar(self):
        llamadas = []
        def ask_cae(question, wait_min, stall_min, on_chat=None, on_result=None, resume_cid=None, registro=None):
            llamadas.append(resume_cid); on_chat("d" * 32)
            raise gpt_browser.Incompleta("plazo agotado con la generacion en curso", "d" * 32, "generando")
        self.inv.ASK = ask_cae; j = self.job(); self.inv.procesar_job(self.c, j)
        r = self.c.execute("SELECT * FROM jobs").fetchone()
        self.assertEqual((r["estado"], r["chat_id"], r["fase"]), ("pendiente", "d" * 32, "generando"))
        # "reinicio": el servicio pone en_curso -> pendiente y adelanta no_antes; el job sigue con su chat
        self.c.execute("UPDATE jobs SET no_antes=NULL"); self.c.commit()
        self.inv.ASK = ask_con(respuesta(self.investigacion()), calls := [])
        self.inv.procesar_job(self.c, self.c.execute("SELECT * FROM jobs").fetchone())
        self.assertEqual(calls[0]["resume"], "d" * 32)  # reanuda el MISMO chat
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM peticiones").fetchone()[0], 1)  # y no se envio una segunda peticion
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "investigado")
        self.assertEqual(self.c.execute("SELECT intentos FROM jobs").fetchone()[0], 1)

    def test_respuesta_guardada_se_reingiere_sin_preguntar(self):
        f = mw.STATE / "respuestas" / "x.txt"; f.parent.mkdir(parents=True); f.write_text(respuesta(self.investigacion()), encoding="utf-8")
        j = self.job(); self.c.execute("UPDATE jobs SET respuesta=?, fase='capturada'", (str(f),)); self.c.commit()
        self.inv.ASK = lambda *a, **k: self.fail("no debe volver a preguntar a GPT")
        self.inv.procesar_job(self.c, self.c.execute("SELECT * FROM jobs").fetchone())
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "investigado")

    def test_login_y_limite_conservan_el_job(self):
        def ask_login(*a, **k): raise gpt_browser.LoginRequired("sin sesion")
        self.inv.ASK = ask_login; self.job()
        with self.assertRaises(SystemExit): self.inv.procesar_job(self.c, self.c.execute("SELECT * FROM jobs").fetchone())
        self.assertEqual(self.c.execute("SELECT estado FROM jobs").fetchone()[0], "pendiente")
        def ask_lim(*a, **k): raise gpt_browser.RateLimited("limite")
        self.inv.ASK = ask_lim
        with self.assertRaises(SystemExit): self.inv.procesar_job(self.c, self.c.execute("SELECT * FROM jobs").fetchone())
        self.assertTrue((mw.STATE / "limite").exists())

    def test_reintentos_acotados_y_error_visible(self):
        def ask_mal(question, wait_min, stall_min, on_chat=None, on_result=None, resume_cid=None, registro=None):
            raise RuntimeError("fallo tecnico sin chat")
        self.inv.ASK = ask_mal; self.job()
        for _ in range(3):
            self.c.execute("UPDATE jobs SET no_antes=NULL WHERE estado='pendiente'"); self.c.commit()
            self.inv.procesar_job(self.c, self.c.execute("SELECT * FROM jobs").fetchone())
        r = self.c.execute("SELECT * FROM jobs").fetchone(); self.assertEqual(r["estado"], "error"); self.assertEqual(r["intentos"], 3)

    def test_reconciliar_reencola_el_desarrollo_perdido(self):
        self.exp_preparado(estado="aprobado")
        self.assertEqual(self.inv.reconciliar(self.c), 1)
        j = self.c.execute("SELECT * FROM jobs WHERE tipo='D'").fetchone(); self.assertEqual((j["area"], j["estado"]), ("MW-0001", "pendiente"))
        self.assertEqual(self.inv.reconciliar(self.c), 0)  # idempotente: no duplica


def hook(respuestas, registro=None):
    def f(clave, tipo, sistema, entrada, esquema):
        if registro is not None: registro.append((clave, tipo, entrada))
        r = respuestas[tipo]; return r(clave) if callable(r) else r
    return f


APROBAR = {"decision": "aprobar", "motivo": "La necesidad existe: index.html no tiene skip link y ningun test lo comprueba.", "riesgo": "bajo", "criterio_aceptacion": "El primer enfocable es un enlace a #contenido.", "archivos": ["index.html"], "observaciones": "Sin tocar styles.css"}


class Contraste(util.Caso):
    def nuevo(self):
        self.inv.ASK = ask_con(respuesta(self.investigacion())); self.inv.procesar_job(self.c, self.job())
        return self.c.execute("SELECT * FROM expedientes").fetchone()

    def test_aprobar_encola_desarrollo_gpt_y_recibe_el_expediente(self):
        reg = []; self.inv.CLAUDE_HOOK = hook({"contraste": APROBAR}, reg)
        e = self.nuevo(); self.inv.contrastar(self.c, e)
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "desarrollando")
        j = self.c.execute("SELECT * FROM jobs WHERE tipo='D'").fetchone(); self.assertEqual(j["area"], "MW-0001")
        self.assertIn("Enlace para saltar", reg[0][2]); self.assertEqual(reg[0][1], "contraste")
        self.assertIn("estado_sitio", reg[0][2])

    def test_rechazar_y_ya_implementada_y_evidencia_insuficiente(self):
        for dec, esperado in (("rechazar", "descartado_claude"), ("ya_implementada", "descartado_claude"), ("investigar_mas", "evidencia_insuficiente")):
            self.c.execute("DELETE FROM expedientes"); self.c.execute("DELETE FROM jobs"); self.c.commit()
            self.inv.CLAUDE_HOOK = hook({"contraste": {**APROBAR, "decision": dec}})
            e = self.nuevo(); self.inv.contrastar(self.c, e)
            self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], esperado, dec)
            self.assertEqual(self.c.execute("SELECT COUNT(*) FROM jobs WHERE tipo='D'").fetchone()[0], 0)

    def test_respuesta_fuera_de_esquema_no_se_convierte_en_decision(self):
        self.inv.CLAUDE_HOOK = hook({"contraste": {"decision": "quizas", "motivo": "x" * 40, "riesgo": "bajo"}})
        e = self.nuevo(); self.inv.contrastar(self.c, e)
        r = self.c.execute("SELECT * FROM expedientes").fetchone(); self.assertEqual(r["estado"], "investigado"); self.assertEqual(json.loads(r["datos"])["claude_fallos"], 1)
        self.assertIsNone(self.inv.siguiente_exp(self.c, "investigado"))  # espera antes de reintentar
        for _ in range(2):
            d = json.loads(self.c.execute("SELECT datos FROM expedientes").fetchone()[0]); d["claude_no_antes"] = "2000-01-01T00:00:00"
            self.c.execute("UPDATE expedientes SET datos=?", (json.dumps(d),)); self.c.commit()
            self.inv.contrastar(self.c, self.c.execute("SELECT * FROM expedientes").fetchone())
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "claude_fallo")

    def test_tope_diario_de_gasto_pausa_el_servicio(self):
        e = self.nuevo()
        self.c.execute("INSERT INTO claude_llamadas(fecha,clave,tipo,coste_usd,ok) VALUES(?,?,?,?,1)", (mw.now(), "x", "contraste", 99.0)); self.c.commit()
        mw.CFG["claude"]["max_usd_dia"] = 50
        with self.assertRaises(claude_cli.ClaudeError): claude_cli.llamar(mw, self.c, "k", "contraste", "s", "e", self.inv.ESQUEMA_CONTRASTE)
        # a traves de contrastar(): _fallo_claude lo convierte en parada por limite
        orig = self.inv.claude
        self.inv.claude = lambda *a, **k: (_ for _ in ()).throw(claude_cli.ClaudeError("tope diario de gasto Claude alcanzado (50 USD)"))
        try:
            with self.assertRaises(SystemExit): self.inv.contrastar(self.c, e)
        finally: self.inv.claude = orig
        self.assertTrue((mw.STATE / "limite").exists())


class Desarrollo(util.Caso):
    def en_desarrollo(self):
        self.c.execute("INSERT INTO expedientes(id,area,lente,titulo,necesidad,estado,datos,contraste,intentos_parche,creado,actualizado) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                       ("MW-0001", "accesibilidad", "1", "t", "n" * 50, "desarrollando", json.dumps(self.investigacion()), json.dumps(APROBAR), 1, mw.now(), mw.now())); self.c.commit()
        self.inv.encolar_desarrollo(self.c, "MW-0001"); return self.c.execute("SELECT * FROM jobs WHERE tipo='D'").fetchone()

    def test_prompt_lleva_codigo_actual_criterio_y_limites(self):
        j = self.en_desarrollo(); t = self.inv.prompt_desarrollar(j, self.c)
        self.assertIn("<main>", t); self.assertIn("El primer enfocable es un enlace", t); self.assertIn("tests/mejoras-web/", t); self.assertNotIn("{{", t)

    def test_parche_valido_pasa_a_parche_listo_con_rama_propia(self):
        j = self.en_desarrollo(); self.inv.ASK = ask_con(respuesta(self.propuesta_gpt())); self.inv.procesar_job(self.c, j)
        e = self.c.execute("SELECT * FROM expedientes").fetchone(); self.assertEqual(e["estado"], "parche_listo"); self.assertEqual(e["rama"], "mejoras-web/mw-0001")
        p = json.loads(e["parche"]); self.assertEqual(p["tocados"][0], "index.html"); self.assertEqual(p["pruebas"][0]["exe"], "python")

    def test_parche_que_no_encaja_se_reintenta_con_el_motivo_y_se_agota(self):
        j = self.en_desarrollo(); mal = self.propuesta_gpt(); mal["parche"]["ficheros"][0]["reemplazos"][0]["buscar"] = "NO ESTA EN EL FICHERO"
        self.inv.ASK = ask_con(respuesta(mal))
        for _ in range(3):
            self.c.execute("UPDATE jobs SET no_antes=NULL WHERE estado='pendiente'"); self.c.commit()
            self.inv.procesar_job(self.c, self.c.execute("SELECT * FROM jobs WHERE tipo='D'").fetchone())
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "fallo_desarrollo")
        self.assertIn("0 veces", self.c.execute("SELECT error FROM jobs").fetchone()[0])

    def test_gpt_dice_que_ya_existe(self):
        j = self.en_desarrollo(); self.inv.ASK = ask_con(respuesta({"resuelto_en_base": True, "explicacion": "ya hay skip link en index.html", "parche": None}))
        self.inv.procesar_job(self.c, j); self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "descartado_gpt")

    def test_sin_tests_de_aceptacion_no_se_acepta(self):
        j = self.en_desarrollo(); self.inv.ASK = ask_con(respuesta(self.propuesta_gpt(pruebas=[]))); self.inv.procesar_job(self.c, j)
        self.assertNotEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "parche_listo")


class Revision(util.Caso):
    def listo(self):
        self.exp_preparado(estado="parche_listo"); self.c.execute("UPDATE expedientes SET intentos_parche=1"); self.c.commit()
        return self.c.execute("SELECT * FROM expedientes").fetchone()

    def rev(self, **kw):
        return {"decision": "aprobar", "motivo": "El parche cumple el criterio, el test falla sin el y pasa con el; sin duplicidades.", "riesgo": "bajo", "problemas": [], **kw}

    def test_aprobar(self):
        self.inv.CLAUDE_HOOK = hook({"revision": self.rev()}); self.inv.revisar(self.c, self.listo())
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "preparado")
        self.assertEqual(json.loads(self.c.execute("SELECT revision FROM expedientes").fetchone()[0])["decision"], "aprobar")

    def test_corregir_vuelve_a_gpt_con_los_problemas_y_se_agota(self):
        reg = []; self.inv.CLAUDE_HOOK = hook({"revision": self.rev(decision="corregir", problemas=["duplica .skip de styles.css"])}, reg)
        self.inv.revisar(self.c, self.listo())
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "desarrollando")
        j = self.c.execute("SELECT payload FROM jobs WHERE tipo='D' ORDER BY id DESC").fetchone(); self.assertIn("duplica .skip", j[0])
        self.c.execute("UPDATE expedientes SET estado='parche_listo', intentos_parche=2"); self.c.commit()  # ya no quedan intentos
        self.inv.revisar(self.c, self.c.execute("SELECT * FROM expedientes").fetchone())
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "parche_rechazado")

    def test_rechazar(self):
        self.inv.CLAUDE_HOOK = hook({"revision": self.rev(decision="rechazar", motivo="Rompe la estructura de cabecera usada por todas las paginas del sitio.")}); self.inv.revisar(self.c, self.listo())
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "parche_rechazado")

    def test_codigo_externo_no_verificado_nunca_llega_a_claude(self):
        e = self.listo(); p = json.loads(e["parche"]); p["codigo_externo"] = [{"url": "https://github.com/o/r", "commit_upstream": "c" * 40, "ruta_upstream": "a.js", "fuente_sha": "a" * 40, "codigo_original": "function x() { return 1; }", "licencia": "MIT"}]
        self.c.execute("UPDATE expedientes SET parche=?", (json.dumps(p),)); self.c.commit()
        self.inv.CLAUDE_HOOK = lambda *a: self.fail("Claude no debe revisar un parche con procedencia sin verificar")
        self.inv.revisar(self.c, self.c.execute("SELECT * FROM expedientes").fetchone(), fetch=lambda url: (_ for _ in ()).throw(OSError("sin red")))
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "desarrollando")


class CircuitoCompleto(util.Caso):
    def test_investigar_contrastar_desarrollar_revisar_hasta_preparado(self):
        gpt = []
        def ask(question, wait_min, stall_min, on_chat=None, on_result=None, resume_cid=None, registro=None):
            gpt.append(question[:30]); cid = f"{len(gpt):032d}"; on_chat(cid)
            d = self.investigacion() if question.startswith("[INVESTIGACION") else self.propuesta_gpt()
            res = gpt_browser.Resultado("terminada", respuesta(d), cid, 3, 5); on_result(res); return res
        claude = []
        self.inv.ASK = ask
        self.inv.CLAUDE_HOOK = hook({"contraste": APROBAR, "revision": Revision.rev(self)}, claude)
        for _ in range(8):
            if self.c.execute("SELECT estado FROM expedientes WHERE id='MW-0001'").fetchone() and self.c.execute("SELECT estado FROM expedientes WHERE id='MW-0001'").fetchone()[0] == "preparado": break
            self.assertTrue(self.inv.paso(self.c))
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes WHERE id='MW-0001'").fetchone()[0], "preparado")
        self.assertEqual(len(gpt), 2); self.assertEqual([c[1] for c in claude], ["contraste", "revision"])
        h = [r[0] for r in self.c.execute("SELECT estado FROM historial WHERE exp='MW-0001' ORDER BY rowid")]
        self.assertEqual(h, ["investigado", "aprobado", "parche_listo", "preparado"])

    def test_capacidad_limita_investigaciones_nuevas(self):
        mw.CFG["max_pendientes"] = 1; self.exp_preparado()
        self.assertFalse(self.inv.capacidad(self.c)); self.assertFalse(self.inv.paso(self.c))  # nada que hacer: no abre otra investigacion
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0], 0)

    def test_tope_horario_de_consultas_a_chatgpt(self):
        mw.CFG["flujo"]["consultas_gpt_por_hora"] = 1
        self.c.execute("INSERT INTO peticiones(fecha,hora,tipo) VALUES(?,?,?)", (mw.today(), mw.now(), "I")); self.c.commit()
        self.inv.ASK = lambda *a, **k: self.fail("no debe consultar a ChatGPT por encima del tope horario")
        self.assertFalse(self.inv.paso(self.c))


if __name__ == "__main__":
    unittest.main()
