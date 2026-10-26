import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones offline de gpt_browser: backend, estados, reanudacion y limpieza."""

import tempfile
import types
import unittest
from unittest.mock import MagicMock, patch

import gpt_browser as g


CID = "a" * 36
PROJECT = g.PROJECT_URL
CHAT_URL = f"https://chatgpt.com/g/{g.PROJECT_ID}/c/{CID}"


def mensaje(
    role="assistant",
    text="respuesta",
    status="finished_successfully",
    end_turn=True,
    content_type="text",
):
    return {
        "author": {"role": role},
        "status": status,
        "end_turn": end_turn,
        "content": {
            "content_type": content_type,
            "parts": [text],
        },
    }


def conversacion(*messages):
    mapping = {}
    parent = None
    for index, message in enumerate(messages):
        node = f"node-{index}"
        mapping[node] = {"parent": parent, "message": message}
        parent = node
    return {"mapping": mapping, "current_node": parent}


def resultado(estado="terminada", texto="respuesta", cid=CID):
    return g.Resultado(estado, texto, cid, 1, 3)


class Pagina:
    """Doble de pagina que no inicia Playwright ni realiza operaciones de red."""

    def __init__(self, url=CHAT_URL, backend=None, body=""):
        self.url = url
        self.backend = backend
        self.body = body
        self.closed = False
        self.waits = []
        self.locators = {}
        self.goto_calls = []
        self.reload_calls = 0

    def evaluate(self, expression, *args):
        if "innerText" in expression:
            return self.body
        if isinstance(self.backend, Exception):
            raise self.backend
        return self.backend

    def locator(self, selector):
        return self.locators.setdefault(selector, MagicMock())

    def goto(self, url, **kwargs):
        self.goto_calls.append((url, kwargs))
        self.url = url

    def reload(self, **kwargs):
        self.reload_calls += 1

    def wait_for_timeout(self, milliseconds):
        self.waits.append(milliseconds)

    def close(self):
        self.closed = True


class NavegadorAislado(unittest.TestCase):
    """Base comun para simular el ciclo completo sin arrancar Edge."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

        self.page = Pagina(url=PROJECT)
        self.context = MagicMock()
        self.context.pages = []
        self.context.new_page.return_value = self.page

        self.playwright = MagicMock()
        self.playwright.stop = MagicMock()

        self.sync = MagicMock()
        self.sync.start.return_value = self.playwright

        fake_sync = types.ModuleType("playwright.sync_api")
        fake_sync.sync_playwright = lambda: self.sync

        fake_playwright = types.ModuleType("playwright")
        fake_playwright.sync_api = fake_sync

        modules = patch.dict(
            sys.modules,
            {
                "playwright": fake_playwright,
                "playwright.sync_api": fake_sync,
            },
        )
        modules.start()
        self.addCleanup(modules.stop)

        connector = patch.object(
            g, "_conectar", return_value=(MagicMock(), self.context)
        )
        connector.start()
        self.addCleanup(connector.stop)

        cleaner = patch.object(g, "limpiar_pestanas", return_value=0)
        cleaner.start()
        self.addCleanup(cleaner.stop)

        self.original_parada = g.PARADA
        g.PARADA = None
        self.addCleanup(setattr, g, "PARADA", self.original_parada)


class Evaluacion(unittest.TestCase):
    def test_rama_actual_ignora_respuesta_terminada_en_rama_abandonada(self):
        """Evita aceptar una respuesta antigua ajena a la rama activa."""
        data = conversacion(
            mensaje("user", "pregunta"),
            mensaje("assistant", "respuesta vigente", end_turn=False),
        )
        data["mapping"]["rama-abandonada"] = {
            "parent": "node-0",
            "message": mensaje("assistant", "respuesta antigua"),
        }

        estado, texto, _, nodos = g.evaluar(data)

        self.assertEqual(estado, "generando")
        self.assertEqual(texto, "")
        self.assertEqual(nodos, 3)

    def test_solo_usa_la_ultima_respuesta_del_ultimo_turno(self):
        """Evita devolver razonamientos intermedios en lugar del resultado final."""
        data = conversacion(
            mensaje("user", "primera"),
            mensaje("assistant", "anterior"),
            mensaje("user", "segunda"),
            mensaje("assistant", "analisis", end_turn=False),
            mensaje("assistant", "resultado definitivo"),
        )

        estado, texto, _, _ = g.evaluar(data)

        self.assertEqual(estado, "terminada")
        self.assertEqual(texto, "resultado definitivo")

    def test_ignora_mensajes_de_herramienta_como_respuesta_final(self):
        """Impide que la salida del conector GitHub sustituya a ChatGPT."""
        data = conversacion(
            mensaje("user", "lee el repositorio"),
            mensaje("tool", '{"content":"codigo"}'),
            mensaje("assistant", "analizando", end_turn=False),
        )

        estado, texto, herramientas, _ = g.evaluar(data)

        self.assertEqual(estado, "generando")
        self.assertEqual(texto, "")
        self.assertEqual(herramientas, 1)

    def test_no_cuenta_herramientas_de_ramas_abandonadas(self):
        """Evita acreditar lecturas del repositorio que no pertenecen al turno activo."""
        data = conversacion(
            mensaje("user", "pregunta"),
            mensaje("assistant", "respuesta"),
        )
        data["mapping"]["herramienta-huerfana"] = {
            "parent": "node-0",
            "message": mensaje("tool", "lectura antigua"),
        }

        self.assertEqual(g.evaluar(data)[2], 0)

    def test_concatena_partes_textuales_sin_incluir_objetos(self):
        """Evita contaminar la respuesta con metadatos estructurados del backend."""
        assistant = mensaje()
        assistant["content"]["parts"] = [
            "primera",
            {"asset_pointer": "archivo"},
            "\nsegunda",
            None,
        ]
        data = conversacion(mensaje("user"), assistant)

        estado, texto, _, _ = g.evaluar(data)

        self.assertEqual(estado, "terminada")
        self.assertEqual(texto, "primera\nsegunda")

    def test_mensaje_sin_contenido_no_se_considera_final_valido(self):
        """Evita marcar como completado un turno que carece de respuesta textual."""
        assistant = mensaje()
        assistant["content"] = None

        data = conversacion(mensaje("user"), assistant)
        estado, texto, _, _ = g.evaluar(data)

        self.assertNotEqual(estado, "terminada")
        self.assertEqual(texto, "")

    def test_miles_de_nodos_no_producen_recursion_error(self):
        """Evita desbordar la pila al reanudar conversaciones largas."""
        messages = [mensaje("user", "pregunta")]
        messages.extend(
            mensaje("tool", f"lectura {index}") for index in range(2500)
        )
        messages.append(mensaje("assistant", "respuesta final"))

        estado, texto, herramientas, nodos = g.evaluar(
            conversacion(*messages)
        )

        self.assertEqual(estado, "terminada")
        self.assertEqual(texto, "respuesta final")
        self.assertEqual(herramientas, 2500)
        self.assertEqual(nodos, 2502)

    # BUG: Un mapping ciclico hace que evaluar() entre en un bucle infinito.
    # Arreglo minimo: registrar los identificadores visitados y cortar ante ciclos.
    def test_mapping_ciclico_no_bloquea_el_pipeline(self):
        """Evita esperas infinitas ante relaciones parent corruptas."""
        data = conversacion(mensaje("user"))
        data["mapping"]["node-0"]["parent"] = "node-0"

        # Se ejecuta en un hilo con plazo: si el ciclo no se corta, el test falla en vez de colgarse.
        import threading

        hilo = threading.Thread(target=g.evaluar, args=(data,), daemon=True)
        hilo.start(); hilo.join(5)
        self.assertFalse(hilo.is_alive())


class Backend(unittest.TestCase):
    def test_http_403_exige_login(self):
        """Evita continuar trabajando con una sesion sin autorizacion."""
        page = Pagina(backend={"http": 403})

        with self.assertRaises(g.LoginRequired):
            g.leer_chat(page, CID)

    def test_http_429_preserva_cid_y_estado_backend(self):
        """Evita perder la referencia del chat durante una limitacion temporal."""
        page = Pagina(backend={"http": 429})

        with self.assertRaises(g.Incompleta) as caught:
            g.leer_chat(page, CID)

        self.assertEqual(caught.exception.cid, CID)
        self.assertEqual(caught.exception.estado, "backend")
        self.assertIn("429", str(caught.exception))

    def test_backend_sin_mapping_no_se_acepta_como_respuesta(self):
        """Evita procesar JSON valido pero ajeno al esquema de conversacion."""
        page = Pagina(backend={"current_node": "node-1"})

        with self.assertRaises(g.Incompleta) as caught:
            g.leer_chat(page, CID)

        self.assertEqual(caught.exception.cid, CID)
        self.assertEqual(caught.exception.estado, "backend")

    def test_backend_no_json_no_se_interpreta_como_exito(self):
        """Evita dar por completada una respuesta HTML o corrupta."""
        page = Pagina(backend="<html>Error 502</html>")

        with self.assertRaises(g.Incompleta):
            g.leer_chat(page, CID)

    def test_resultado_conserva_identidad_y_metricas(self):
        """Evita perder el cid y la evidencia de lecturas al persistir resultados."""
        page = Pagina(
            backend=conversacion(
                mensaje("user", "consulta"),
                mensaje("tool", "repositorio"),
                mensaje("assistant", "respuesta"),
            )
        )

        res = g.leer_chat(page, CID)

        self.assertIsInstance(res, g.Resultado)
        self.assertEqual(res.cid, CID)
        self.assertEqual(res.estado, "terminada")
        self.assertEqual(res.texto, "respuesta")
        self.assertEqual(res.herramientas, 1)
        self.assertEqual(res.nodos, 3)


class Espera(unittest.TestCase):
    def test_parada_preserva_cid_para_reanudacion(self):
        """Evita reenviar el prompt cuando se solicita detener el worker."""
        page = Pagina()
        running = resultado("generando", "")

        with (
            patch.object(g, "leer_chat", return_value=running),
            patch.object(g, "PARADA", return_value=True),
        ):
            with self.assertRaises(g.Incompleta) as caught:
                g._esperar(page, CID, 1, 1)

        self.assertEqual(caught.exception.cid, CID)
        self.assertEqual(caught.exception.estado, "generando")

    def test_resultado_fallido_termina_el_sondeo(self):
        """Evita esperar hasta el timeout tras un fallo definitivo del servicio."""
        page = Pagina()
        failed = resultado("fallida", "")

        with patch.object(g, "leer_chat", return_value=failed) as read:
            res = g._esperar(page, CID, 1, 1)

        self.assertIs(res, failed)
        read.assert_called_once()
        self.assertEqual(page.waits, [])

    def test_backend_503_tiene_reintentos_acotados(self):
        """Evita sondeos ilimitados cuando el backend permanece caido."""
        page = Pagina()

        def unavailable(*args):
            raise g.Incompleta("backend sin conversacion (http 503)", CID, "backend")

        with patch.object(g, "leer_chat", side_effect=unavailable) as read:
            with self.assertRaises(g.Incompleta) as caught:
                g._esperar(page, CID, 30, 12)

        self.assertEqual(caught.exception.cid, CID)
        self.assertEqual(read.call_count, 7)
        self.assertEqual(len(page.waits), 6)
        self.assertLessEqual(max(page.waits), 240000)

    def test_timeout_preserva_cid_sin_sondear(self):
        """Evita consultas innecesarias cuando el plazo ya ha vencido."""
        page = Pagina()

        with patch.object(g, "leer_chat") as read:
            with self.assertRaises(g.Incompleta) as caught:
                g._esperar(page, CID, 0, 1)

        self.assertEqual(caught.exception.cid, CID)
        self.assertEqual(caught.exception.estado, "generando")
        read.assert_not_called()

    def test_callback_progreso_recibe_resultado_real(self):
        """Evita perder las metricas necesarias para supervisar una generacion."""
        page = Pagina()
        complete = resultado()
        seen = []

        with patch.object(g, "leer_chat", return_value=complete):
            res = g._esperar(page, CID, 1, 1, progreso=seen.append)

        self.assertIs(res, complete)
        self.assertEqual(seen, [complete])


class Reanudacion(NavegadorAislado):
    def test_resume_cid_no_reenvia_prompt(self):
        """Evita duplicar consultas tras reiniciar INICIAR."""
        expected = resultado()

        with (
            patch.object(g, "abrir_chat", return_value=expected) as open_chat,
            patch.object(g, "_esperar", return_value=expected),
        ):
            res = g.ask("PROMPT ORIGINAL", resume_cid=CID)

        self.assertIs(res, expected)
        open_chat.assert_called_once_with(self.page, CID)
        self.assertEqual(self.page.goto_calls, [])
        self.assertTrue(self.page.closed)
        self.playwright.stop.assert_called_once()

    def test_chat_incierto_no_crea_conversacion_nueva(self):
        """Evita duplicar trabajos cuando la red falla al recuperar el chat."""
        inaccessible = g.ChatInaccesible(
            "backend no alcanzable", CID, perdida=False
        )

        with patch.object(g, "abrir_chat", side_effect=inaccessible):
            with self.assertRaises(g.Incompleta) as caught:
                g.ask("PROMPT ORIGINAL", resume_cid=CID)

        self.assertEqual(caught.exception.cid, CID)
        self.assertEqual(caught.exception.estado, "backend")
        self.assertEqual(self.page.goto_calls, [])
        self.assertFalse(self.page.closed)
        self.playwright.stop.assert_called_once()


    def test_callback_persistencia_fallido_conserva_pestana(self):
        """Evita perder una respuesta generada cuando falla su guardado en disco."""
        expected = resultado()

        def disk_full(_):
            raise OSError("No space left on device")

        with (
            patch.object(g, "abrir_chat", return_value=expected),
            patch.object(g, "_esperar", return_value=expected),
        ):
            with self.assertRaises(OSError):
                g.ask(
                    "PROMPT",
                    resume_cid=CID,
                    on_result=disk_full,
                )

        self.assertFalse(self.page.closed)
        self.playwright.stop.assert_called_once()

    def test_respuesta_vacia_no_cierra_pestana(self):
        """Evita descartar una conversacion cuya respuesta no contiene texto."""
        empty = resultado("vacia", "")

        with (
            patch.object(g, "abrir_chat", return_value=empty),
            patch.object(g, "_esperar", return_value=empty),
        ):
            with self.assertRaises(g.Incompleta) as caught:
                g.ask("PROMPT", resume_cid=CID)

        self.assertEqual(caught.exception.estado, "vacia")
        self.assertEqual(caught.exception.cid, CID)
        self.assertFalse(self.page.closed)
        self.playwright.stop.assert_called_once()

    def test_generacion_fallida_no_se_persiste_como_exito(self):
        """Evita entregar resultados parciales a la fase EJECUTAR."""
        failed = resultado("fallida", "")
        saved = MagicMock()

        with (
            patch.object(g, "abrir_chat", return_value=failed),
            patch.object(g, "_esperar", return_value=failed),
        ):
            with self.assertRaises(g.Incompleta) as caught:
                g.ask(
                    "PROMPT",
                    resume_cid=CID,
                    on_result=saved,
                )

        self.assertEqual(caught.exception.estado, "fallida")
        saved.assert_not_called()
        self.assertFalse(self.page.closed)
        self.playwright.stop.assert_called_once()

    def test_error_al_reanudar_libera_playwright(self):
        """Evita dejar procesos de automatizacion vivos tras perder la sesion."""
        with patch.object(
            g, "abrir_chat", side_effect=g.LoginRequired("sesion caducada")
        ):
            with self.assertRaises(g.LoginRequired):
                g.ask("PROMPT", resume_cid=CID)

        self.assertFalse(self.page.closed)
        self.playwright.stop.assert_called_once()


class Limpieza(unittest.TestCase):
    def test_chat_generando_y_desconocido_permanecen_abiertos(self):
        """Evita cerrar conversaciones recuperables durante la limpieza."""
        running = Pagina(url=CHAT_URL)
        unknown = Pagina(
            url=f"https://chatgpt.com/c/{'b' * 36}"
        )
        ctx = types.SimpleNamespace(pages=[running, unknown])

        with patch.object(
            g,
            "estado_chat_seguro",
            side_effect=["generando", "desconocido"],
        ):
            closed = g.limpiar_pestanas(ctx)

        self.assertEqual(closed, 0)
        self.assertFalse(running.closed)
        self.assertFalse(unknown.closed)

    def test_chat_guardado_se_cierra_sin_consultar_backend(self):
        """Evita depender de la red para limpiar una respuesta ya persistida."""
        page = Pagina(url=CHAT_URL)
        ctx = types.SimpleNamespace(pages=[page])

        with patch.object(g, "estado_chat_seguro") as state:
            closed = g.limpiar_pestanas(
                ctx,
                guardados=(CID,),
            )

        self.assertEqual(closed, 1)
        self.assertTrue(page.closed)
        state.assert_not_called()

    def test_cid_conservado_prevalece_sobre_resultado_guardado(self):
        """Evita cerrar el chat que otro trabajo necesita reanudar."""
        page = Pagina(url=CHAT_URL)
        ctx = types.SimpleNamespace(pages=[page])

        closed = g.limpiar_pestanas(
            ctx,
            conservar=(CID,),
            guardados=(CID,),
        )

        self.assertEqual(closed, 0)
        self.assertFalse(page.closed)

    def test_limpieza_no_toca_paginas_ajenas_a_chatgpt(self):
        """Evita cerrar pestanas personales abiertas en el Edge dedicado."""
        external = Pagina(url="https://github.com/")
        project = Pagina(url=PROJECT)
        ctx = types.SimpleNamespace(pages=[external, project])

        closed = g.limpiar_pestanas(ctx)

        self.assertEqual(closed, 0)
        self.assertFalse(external.closed)
        self.assertFalse(project.closed)


if __name__ == "__main__":
    unittest.main()
