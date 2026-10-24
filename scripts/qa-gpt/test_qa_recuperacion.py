"""Recuperacion de conversaciones ChatGPT inaccesibles (offline: pagina y backend simulados)."""
import os, sys, tempfile, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qa_gpt as q, gpt_browser as g
from test_qa_gpt import conv, msg

TXT_ERROR = "No se ha podido cargar esta conversación de ChatGPT. Intentarlo de nuevo"
HTML_ERROR = f"<main><h1>{TXT_ERROR}</h1><button>Intentarlo de nuevo</button></main>"


class Loc:
    def __init__(s, n): s.n = n
    def count(s): return s.n


class Pagina:
    """`pasos`: por cada carga (goto/reload) -> (texto visible, mensajes en DOM, respuesta del backend) o una excepcion."""
    def __init__(s, pasos, url="https://chatgpt.com/g/x/c/aaaa"):
        s.pasos, s.i, s.url, s.cargas, s.vis, s.dom, s.back = list(pasos), -1, url, 0, "", 0, {"http": 500}

    def _carga(s):
        s.i = min(s.i + 1, len(s.pasos) - 1); s.cargas += 1; p = s.pasos[s.i]
        if isinstance(p, Exception): raise p
        s.vis, s.dom, s.back = p

    def goto(s, *a, **k): s._carga()
    def reload(s, *a, **k): s._carga()
    def wait_for_timeout(s, ms): pass
    def locator(s, sel): return Loc(s.dom if "data-message-author-role" in sel else 1)
    def evaluate(s, js, *a): return s.vis if "innerText" in js else s.back


OK = conv(msg("user"), msg("assistant", text='{"a":1}'))
CARGADA = ("", 2, OK)
ERROR = (TXT_ERROR, 0, {"http": 500})


class Recarga(unittest.TestCase):
    def test_detecta_el_texto_de_la_captura(self):
        self.assertTrue(g.ERROR_CARGA_RE.search(TXT_ERROR)); self.assertTrue(g.ERROR_CARGA_RE.search(HTML_ERROR))
        self.assertFalse(g.ERROR_CARGA_RE.search("Hola, ¿en qué puedo ayudarte?"))

    def test_conversacion_cargada_sin_recargar(self):
        pg = Pagina([CARGADA]); r = g.abrir_chat(pg, "aaaa")
        self.assertEqual((r.estado, pg.cargas), ("terminada", 1))

    def test_error_explicito_y_recarga_exitosa(self):
        pg = Pagina([ERROR, CARGADA]); r = g.abrir_chat(pg, "aaaa")
        self.assertEqual((r.estado, pg.cargas), ("terminada", 2))

    def test_recarga_fallida_es_acotada(self):
        pg = Pagina([ERROR])
        with self.assertRaises(g.ChatInaccesible) as cm: g.abrir_chat(pg, "aaaa")
        self.assertEqual(pg.cargas, g.RECARGAS + 1)  # nunca infinito
        self.assertFalse(cm.exception.perdida)  # backend 500: incierto, no se abre otro chat

    def test_backend_404_confirma_perdida(self):
        pg = Pagina([(TXT_ERROR, 0, {"http": 404})])
        with self.assertRaises(g.ChatInaccesible) as cm: g.abrir_chat(pg, "aaaa")
        self.assertTrue(cm.exception.perdida)

    def test_pagina_con_error_pero_backend_responde(self):  # el visor falla, la conversacion existe: se reconcilia sin chat nuevo
        pg = Pagina([(TXT_ERROR, 0, OK)])
        self.assertEqual(g.abrir_chat(pg, "aaaa").estado, "terminada"); self.assertEqual(pg.cargas, 1)

    def test_perdida_de_conexion_y_navegacion_fallida(self):
        pg = Pagina([RuntimeError("net::ERR_INTERNET_DISCONNECTED"), ("", 0, {"http": 500}), CARGADA])
        self.assertEqual(g.abrir_chat(pg, "aaaa").estado, "terminada")
        pg = Pagina([RuntimeError("Timeout 40000ms exceeded")])
        with self.assertRaises(g.ChatInaccesible) as cm: g.abrir_chat(pg, "aaaa")
        self.assertFalse(cm.exception.perdida)  # navegacion fallida != conversacion inexistente

    def test_sesion_caducada_no_se_elude(self):
        pg = Pagina([("", 0, {"http": 401})]); pg.url = "https://chatgpt.com/auth/login"
        with self.assertRaises(g.LoginRequired): g.abrir_chat(pg, "aaaa")

    def test_respuesta_anterior_ya_terminada_no_reenvia(self):  # GPT contesto antes del error: se recupera el texto, no se pregunta de nuevo
        pg = Pagina([(TXT_ERROR, 0, OK)])
        self.assertEqual(g.abrir_chat(pg, "aaaa").texto, '{"a":1}')


def lanza(e):
    def f(*a, **k): raise e
    return f


class Cola(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); q.STATE = Path(self.tmp.name); q.DB_PATH = q.STATE / "e.db"; q.Lock.path = q.STATE / "worker.lock"
        self.c = q.db(); self.orig = (g.ask, q.prompt_for)
        q.prompt_for = lambda job, c: "PROMPT ORIGINAL con evidencias"

    def tearDown(self): g.ask, q.prompt_for = self.orig; self.c.close(); self.tmp.cleanup()

    def job(self, area, cid=None, fase=None, intentos=1):
        clave = f"A:{area}:{os.urandom(3).hex()}"; q.enqueue(self.c, "A", area, {"motivo": "t"}, clave)
        jid = self.c.execute("SELECT id FROM jobs WHERE clave=?", (clave,)).fetchone()[0]
        self.c.execute("UPDATE jobs SET chat_id=?,fase=?,intentos=? WHERE id=?", (cid, fase, intentos, jid)); self.c.commit()
        return self.fila(jid)

    def fila(self, jid): return self.c.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()

    def test_incierto_reintenta_sin_perder_chat_ni_duplicar(self):
        j = self.job("zona:rss", "aaaa", "generando", 1)
        g.ask = lanza(g.Incompleta("conversacion inaccesible", "aaaa", "backend")); q.process(j, self.c); f = self.fila(j["id"])
        self.assertEqual((f["estado"], f["chat_id"], f["intentos"]), ("pendiente", "aaaa", 2))

    def test_fallo_reiterado_abandona_chat_y_reencola_con_prompt(self):
        j = self.job("zona:rss", "aaaa", "generando", q.CFG["reintentos"])
        g.ask = lanza(g.Incompleta("conversacion inaccesible", "aaaa", "backend")); q.process(j, self.c); f = self.fila(j["id"])
        self.assertEqual((f["estado"], f["chat_id"], f["fase"]), ("pendiente", None, None))  # chat nuevo la proxima vez
        self.assertTrue(f["error"].startswith("[reencolado]")); self.assertGreater(f["no_antes"], q.now())
        self.assertEqual(f["payload"], j["payload"])  # el trabajo y sus datos siguen intactos

    def test_reencolado_ocurre_una_vez_y_luego_error_visible(self):
        j = self.job("zona:rss", None, None, q.CFG["reintentos"] + 1)
        self.c.execute("UPDATE jobs SET error='[reencolado] x' WHERE id=?", (j["id"],)); self.c.commit()
        q.fallo(self.c, j, "chat inaccesible: otra vez"); f = self.fila(j["id"])
        self.assertEqual(f["estado"], "error"); self.assertIn("reencolado", f["error"])

    def test_chat_nuevo_actualiza_la_referencia(self):
        j = self.job("zona:rss", "aaaa", "generando"); vistos = {}

        def ask(texto, w, s, on_chat, on_result, resume_cid=None, registro=None):
            vistos["texto"] = texto; registro("conversacion perdida"); on_chat("bbbb")
            raise g.Incompleta("generando", "bbbb", "generando")
        g.ask = ask; q.process(j, self.c); f = self.fila(j["id"])
        self.assertEqual((f["chat_id"], f["estado"]), ("bbbb", "pendiente"))
        self.assertEqual(vistos["texto"], "PROMPT ORIGINAL con evidencias")

    def test_un_trabajo_bloqueado_no_detiene_a_otros(self):
        a = self.job("zona:a", "aaaa", "generando"); b = self.job("zona:b")
        self.c.execute("UPDATE jobs SET no_antes='2000-01-01T00:00:00'"); self.c.commit()
        g.ask = lanza(g.Incompleta("conversacion inaccesible", "aaaa", "backend")); q.process(a, self.c)  # a queda aplazado con backoff
        self.assertGreater(self.fila(a["id"])["no_antes"], q.now())  # a aplazado con backoff
        self.assertEqual(q.next_job(self.c)["id"], b["id"])  # el planificador real pasa a b

    def test_worker_reiniciado_conserva_pendientes_y_chat(self):
        j = self.job("zona:rss", "aaaa", "generando"); self.c.close(); self.c = q.db()
        f = self.fila(j["id"]); self.assertEqual((f["estado"], f["chat_id"]), (j["estado"], "aaaa"))

    def test_login_requerido_conserva_el_trabajo(self):
        j = self.job("zona:rss", "aaaa", "generando"); g.ask = lanza(g.LoginRequired("x"))
        with self.assertRaises(SystemExit): q.process(j, self.c)
        f = self.fila(j["id"]); self.assertEqual((f["estado"], f["error"]), ("pendiente", "login"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
