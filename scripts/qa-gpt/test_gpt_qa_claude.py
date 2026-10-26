import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones offline de qa_claude: CLI, cache, esquema, fallos y SQLite."""

import json
import os
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import qa_claude as claude
import qa_gpt as q


ESQUEMA = {
    "type": "object",
    "properties": {
        "accion": {
            "type": "string",
            "enum": ["aprobar", "rechazar"],
        },
        "motivo": {
            "type": "string",
            "minLength": 1,
        },
    },
    "required": ["accion", "motivo"],
}


def respuesta(
    salida=None,
    *,
    result=None,
    coste=0.012,
    turnos=1,
    is_error=False,
    usage=None,
):
    """Construye una respuesta CLI sin ejecutar procesos externos."""
    dato = {
        "is_error": is_error,
        "total_cost_usd": coste,
        "num_turns": turnos,
        "usage": usage if usage is not None else {
            "input_tokens": 100,
            "output_tokens": 30,
            "cache_read_input_tokens": 10,
            "cache_creation_input_tokens": 5,
        },
    }
    if salida is not None:
        dato["structured_output"] = salida
    if result is not None:
        dato["result"] = result
    return json.dumps(dato, ensure_ascii=False)


class TestQaClaude(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="qa-claude-test-")
        self.addCleanup(self.tmp.cleanup)

        self.base = Path(self.tmp.name)
        self.state = self.base / "state"
        self.root = self.base / "repo"
        self.state.mkdir()
        self.root.mkdir()
        (self.state / "claude").mkdir()

        self._patch(q, "STATE", self.state)
        self._patch(q, "DB_PATH", self.state / "estado.db")
        self._patch(q, "ROOT", self.root)
        self._patch(q, "WT", self.state / "wt")
        self._patch(q.Lock, "path", self.state / "worker.lock")

        self._patch(claude, "_CLAUDE_EXE", None)

        self.cfg = {
            "modelo": "claude-sonnet-5-5",
            "esfuerzo": "low",
            "max_turnos": 2,
            "timeout_s": 7,
            "max_usd_llamada": 0.25,
        }

        self.fake_q = SimpleNamespace(
            STATE=self.state,
            CFG={"claude": self.cfg.copy()},
            now=lambda: "2026-10-26T09:00:00",
        )

        self.c = sqlite3.connect(
            self.state / "estado.db",
            timeout=1,
        )
        self.c.row_factory = sqlite3.Row
        self.addCleanup(self.c.close)

        claude.migrar(self.c)

        self.run = Mock(
            return_value=subprocess.CompletedProcess(
                args=["claude"],
                returncode=0,
                stdout=respuesta({
                    "accion": "aprobar",
                    "motivo": "Validado",
                }),
                stderr="",
            )
        )

        self._patch(claude, "exe", Mock(return_value="claude-test.exe"))
        self._patch(claude.subprocess, "run", self.run)

    def _patch(self, obj, nombre, valor):
        p = patch.object(obj, nombre, valor)
        p.start()
        self.addCleanup(p.stop)

    def llamar(self, **kwargs):
        opciones = {
            "clave": "decision:123",
            "tipo": "decision",
            "sistema": "Decide sobre la evidencia.",
            "entrada": "Evidencia de prueba",
            "esquema": ESQUEMA,
        }
        opciones.update(kwargs)
        return claude.llamar(self.fake_q, self.c, **opciones)

    def filas(self):
        return self.c.execute(
            "SELECT * FROM claude_llamadas ORDER BY id"
        ).fetchall()

    def cache(self):
        return self.c.execute(
            "SELECT * FROM claude_veredictos"
        ).fetchall()

    def poner_respuesta(self, stdout, returncode=0, stderr=""):
        self.run.return_value = subprocess.CompletedProcess(
            args=["claude"],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    def test_smoke_decision_valida_y_auditoria(self):
        """Evita perder el veredicto y sus métricas tras una llamada correcta."""
        dato, meta = self.llamar()

        self.assertEqual(dato["accion"], "aprobar")
        self.assertEqual(meta["coste"], 0.012)
        self.assertEqual(meta["tok_in"], 100)
        self.assertEqual(meta["tok_out"], 30)
        self.assertEqual(meta["cache_lee"], 10)
        self.assertEqual(meta["cache_crea"], 5)

        fila = self.filas()[0]
        self.assertEqual(fila["ok"], 1)
        self.assertEqual(fila["tipo"], "decision")
        self.assertEqual(fila["turnos"], 1)
        self.assertEqual(len(self.cache()), 1)

    def test_cli_sin_herramientas_ni_sesion(self):
        """Evita que Claude herede herramientas o persista sesiones de decisión."""
        self.llamar()

        args = self.run.call_args.args[0]

        self.assertEqual(
            args[args.index("--tools") + 1],
            "",
        )
        self.assertIn("--no-session-persistence", args)
        self.assertIn("--strict-mcp-config", args)
        self.assertIn("--disable-slash-commands", args)
        self.assertNotIn("--allowedTools", args)

        self.assertEqual(
            args[args.index("--max-budget-usd") + 1],
            "0.25",
        )
        self.assertEqual(
            args[args.index("--max-turns") + 1],
            "2",
        )

        kwargs = self.run.call_args.kwargs
        self.assertEqual(kwargs["input"], "Evidencia de prueba")
        self.assertEqual(kwargs["timeout"], 7)
        self.assertEqual(kwargs["cwd"], str(self.state / "claude"))
        self.assertTrue(kwargs["capture_output"])
        self.assertEqual(kwargs["encoding"], "utf-8")

    def test_herramientas_restringidas_no_se_amplian(self):
        """Evita conceder comandos adicionales al traducir permisos de Claude."""
        self.llamar(
            herramientas="Read,Grep,Bash(pytest:*),Read",
            usar_cache=False,
        )

        args = self.run.call_args.args[0]

        self.assertEqual(
            args[args.index("--tools") + 1],
            "Read,Grep,Bash",
        )
        self.assertEqual(
            args[args.index("--allowedTools") + 1],
            "Read,Grep,Bash(pytest:*),Read",
        )

    def test_timeout_acotado_registra_fallo(self):
        """Evita que un timeout deje una llamada aparentemente exitosa."""
        self.run.side_effect = subprocess.TimeoutExpired(
            cmd=["claude"],
            timeout=7,
        )

        with self.assertRaisesRegex(claude.ClaudeError, "timeout"):
            self.llamar()

        self.assertEqual(self.run.call_count, 1)
        self.assertEqual(self.run.call_args.kwargs["timeout"], 7)
        self.assertEqual(self.filas()[0]["ok"], 0)
        self.assertEqual(len(self.cache()), 0)

    def test_timeout_permite_reintento_posterior(self):
        """Evita que un timeout envenene la caché e impida recuperar el servicio."""
        self.run.side_effect = [
            subprocess.TimeoutExpired(["claude"], 7),
            subprocess.CompletedProcess(
                ["claude"],
                0,
                respuesta({
                    "accion": "aprobar",
                    "motivo": "Recuperado",
                }),
                "",
            ),
        ]

        with self.assertRaises(claude.ClaudeError):
            self.llamar()

        dato, _ = self.llamar()

        self.assertEqual(dato["motivo"], "Recuperado")
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(
            [f["ok"] for f in self.filas()],
            [0, 1],
        )

    def test_cli_ausente_registra_error_y_reintenta(self):
        """Evita perder trazabilidad cuando Windows no encuentra el ejecutable."""
        self.run.side_effect = FileNotFoundError(
            2, "No such file or directory"
        )

        for _ in range(2):
            with self.assertRaises(claude.ClaudeError):
                self.llamar()

        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(len(self.filas()), 2)
        self.assertTrue(all(f["ok"] == 0 for f in self.filas()))
        self.assertEqual(len(self.cache()), 0)

    def test_salida_vacia_no_se_acepta(self):
        """Evita aprobar decisiones cuando Claude devuelve stdout vacío."""
        self.poner_respuesta("")

        with self.assertRaises(claude.ClaudeError):
            self.llamar()

        self.assertEqual(self.filas()[0]["ok"], 0)
        self.assertEqual(len(self.cache()), 0)

    def test_json_exterior_truncado_no_se_acepta(self):
        """Evita interpretar una respuesta JSON incompleta como veredicto."""
        self.poner_respuesta('{"structured_output":{"accion":"aprobar"')

        with self.assertRaises(claude.ClaudeError):
            self.llamar()

        self.assertEqual(self.filas()[0]["ok"], 0)
        self.assertEqual(len(self.cache()), 0)

    def test_result_json_alternativo_valido(self):
        """Evita perder decisiones válidas si el CLI usa result en vez de structured_output."""
        self.poner_respuesta(respuesta(
            result=json.dumps({
                "accion": "rechazar",
                "motivo": "Falta evidencia",
            })
        ))

        dato, _ = self.llamar()

        self.assertEqual(dato["accion"], "rechazar")
        self.assertEqual(len(self.cache()), 1)

    def test_result_texto_libre_no_se_acepta(self):
        """Evita convertir prosa libre de Claude en una decisión estructurada."""
        self.poner_respuesta(respuesta(
            result="Creo que deberíamos aprobarlo."
        ))

        with self.assertRaises(claude.ClaudeError):
            self.llamar()

        self.assertEqual(self.filas()[0]["ok"], 0)
        self.assertEqual(len(self.cache()), 0)

    def test_is_error_prevalece_sobre_salida_valida(self):
        """Evita aprobar respuestas que el propio CLI marca como fallidas."""
        self.poner_respuesta(respuesta(
            salida={
                "accion": "aprobar",
                "motivo": "No fiable",
            },
            result="Rate limit exceeded",
            is_error=True,
        ))

        with self.assertRaisesRegex(claude.ClaudeError, "claude error"):
            self.llamar()

        self.assertEqual(self.filas()[0]["ok"], 0)
        self.assertEqual(len(self.cache()), 0)

    def test_exit_no_cero_no_guarda_veredicto(self):
        """Evita cachear decisiones de un proceso terminado con error."""
        self.poner_respuesta(
            respuesta({
                "accion": "aprobar",
                "motivo": "No utilizar",
            }),
            returncode=1,
            stderr="Authentication failed",
        )

        with self.assertRaisesRegex(claude.ClaudeError, "exit 1"):
            self.llamar()

        self.assertEqual(self.filas()[0]["ok"], 0)
        self.assertEqual(len(self.cache()), 0)

    def test_esquema_rechaza_campos_obligatorios_ausentes(self):
        """Evita decisiones incompletas que romperían el triaje posterior."""
        self.poner_respuesta(respuesta(
            salida={"accion": "aprobar"}
        ))

        with self.assertRaisesRegex(
            claude.ClaudeError, "esquema no cumplido"
        ):
            self.llamar()

        self.assertEqual(self.filas()[0]["ok"], 0)
        self.assertEqual(len(self.cache()), 0)

    def test_esquema_rechaza_enum_y_motivo_vacio(self):
        """Evita persistir acciones desconocidas o decisiones sin justificación."""
        self.poner_respuesta(respuesta(
            salida={
                "accion": "fusionar_directamente",
                "motivo": "",
            }
        ))

        with self.assertRaises(claude.ClaudeError):
            self.llamar()

        self.assertEqual(self.filas()[0]["ok"], 0)
        self.assertEqual(len(self.cache()), 0)

    def test_esquema_rechaza_booleanos_como_enteros(self):
        """Evita que True pase por un contador entero en las respuestas de Claude."""
        problemas = claude.validar(
            {"intentos": True},
            {
                "type": "object",
                "required": ["intentos"],
                "properties": {
                    "intentos": {"type": "integer"},
                },
            },
        )

        self.assertTrue(problemas)

    def test_esquema_rechaza_exceso_de_elementos(self):
        """Evita aceptar listas de acciones superiores al límite contratado."""
        problemas = claude.validar(
            {"acciones": ["a", "b", "c"]},
            {
                "type": "object",
                "properties": {
                    "acciones": {
                        "type": "array",
                        "maxItems": 2,
                        "items": {"type": "string"},
                    },
                },
            },
        )

        self.assertTrue(problemas)

    # BUG: validar() inspecciona solo dato[:50], por lo que una respuesta
    # con 51 elementos puede esconder una accion invalida al final.
    # Arreglo minimo: validar todos los items hasta maxItems, o rechazar
    # explicitamente cualquier lista que exceda el limite de inspeccion.
    def test_esquema_valida_tambien_elemento_51(self):
        """Evita que elementos posteriores al número 50 eludan el esquema."""
        esquema = {
            "type": "array",
            "maxItems": 100,
            "items": {
                "type": "string",
                "enum": ["seguro"],
            },
        }
        datos = ["seguro"] * 50 + ["fusionar_sin_revision"]

        self.assertTrue(claude.validar(datos, esquema))

    # BUG: llamar() devuelve json.loads(respuesta) directamente desde cache,
    # sin repetir validar(). Una fila corrupta puede introducir una accion
    # inexistente en el pipeline sin ejecutar Claude.
    # Arreglo minimo: validar la entrada cacheada; si no cumple, eliminarla
    # y regenerar el veredicto, registrando la incidencia.
    def test_cache_corrupta_no_se_convierte_en_decision(self):
        """Evita ejecutar decisiones inválidas recuperadas de SQLite."""
        self.llamar()

        self.c.execute(
            "UPDATE claude_veredictos SET respuesta=?",
            (json.dumps({
                "accion": "fusionar_directamente",
                "motivo": "",
            }),),
        )
        self.c.commit()

        dato, _ = self.llamar()

        self.assertEqual(dato["accion"], "aprobar")
        self.assertEqual(dato["motivo"], "Validado")

    # BUG: el json.loads() del acceso a cache no esta protegido. Una fila
    # truncada propaga JSONDecodeError y puede interrumpir el worker.
    # Arreglo minimo: invalidar la fila corrupta y consultar Claude de nuevo.
    def test_cache_json_truncado_se_recupera(self):
        """Evita que una escritura parcial de SQLite bloquee decisiones futuras."""
        self.llamar()

        self.c.execute(
            "UPDATE claude_veredictos SET respuesta=?",
            ('{"accion":',),
        )
        self.c.commit()

        dato, _ = self.llamar()

        self.assertEqual(dato["accion"], "aprobar")
        self.assertEqual(self.run.call_count, 2)

    def test_cache_identica_evita_segunda_llamada(self):
        """Evita duplicar coste y procesos al repetir exactamente la misma evidencia."""
        primero, meta1 = self.llamar()
        segundo, meta2 = self.llamar()

        self.assertEqual(primero, segundo)
        self.assertFalse(meta1.get("cache", False))
        self.assertTrue(meta2["cache"])
        self.assertEqual(self.run.call_count, 1)
        self.assertEqual(len(self.filas()), 1)
        self.assertEqual(len(self.cache()), 1)

    def test_cache_cambia_con_evidencia_esquema_y_modelo(self):
        """Evita reutilizar veredictos cuando cambian las condiciones de decisión."""
        self.llamar()

        self.llamar(entrada="Evidencia nueva")

        otro_esquema = {
            **ESQUEMA,
            "properties": {
                **ESQUEMA["properties"],
                "riesgo": {"type": "string"},
            },
        }
        self.llamar(esquema=otro_esquema)

        self.fake_q.CFG["claude"]["modelo"] = "modelo-alternativo"
        self.llamar()

        self.assertEqual(self.run.call_count, 4)
        self.assertEqual(len(self.cache()), 4)

    def test_cache_separa_claves_y_permisos(self):
        """Evita compartir veredictos entre jobs o conjuntos de herramientas distintos."""
        self.llamar(clave="job:1")
        self.llamar(clave="job:2")
        self.llamar(
            clave="job:1",
            herramientas="Read",
        )

        self.assertEqual(self.run.call_count, 3)
        self.assertEqual(len(self.cache()), 3)

    def test_cache_desactivada_fuerza_consulta_y_actualiza(self):
        """Evita que una revisión forzada reutilice una decisión obsoleta."""
        self.llamar()

        self.poner_respuesta(respuesta({
            "accion": "rechazar",
            "motivo": "Nueva evidencia externa",
        }))

        dato, _ = self.llamar(usar_cache=False)

        self.assertEqual(dato["accion"], "rechazar")
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(len(self.filas()), 2)
        self.assertEqual(len(self.cache()), 1)

        recuperado, meta = self.llamar()

        self.assertEqual(recuperado, dato)
        self.assertTrue(meta["cache"])
        self.assertEqual(self.run.call_count, 2)

    def test_fallo_no_sobrescribe_cache_previa(self):
        """Evita perder el último veredicto válido durante una actualización fallida."""
        original, _ = self.llamar()

        self.poner_respuesta("respuesta truncada")

        with self.assertRaises(claude.ClaudeError):
            self.llamar(usar_cache=False)

        recuperado, meta = self.llamar()

        self.assertEqual(recuperado, original)
        self.assertTrue(meta["cache"])
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(len(self.cache()), 1)

    def test_concurrencia_serializa_llamadas_normales(self):
        """Evita lanzar dos procesos de decisión simultáneos en el mismo worker."""
        activos = 0
        max_activos = 0
        contador_lock = threading.Lock()
        primera_dentro = threading.Event()
        liberar_primera = threading.Event()
        errores = []

        def fake_run(*args, **kwargs):
            nonlocal activos, max_activos

            with contador_lock:
                activos += 1
                max_activos = max(max_activos, activos)
                numero = self.run.call_count

            try:
                if numero == 1:
                    primera_dentro.set()
                    if not liberar_primera.wait(timeout=3):
                        raise RuntimeError("timeout del test")

                return subprocess.CompletedProcess(
                    args[0],
                    0,
                    respuesta({
                        "accion": "aprobar",
                        "motivo": "Concurrente",
                    }),
                    "",
                )
            finally:
                with contador_lock:
                    activos -= 1

        self.run.side_effect = fake_run

        def worker(clave):
            c = sqlite3.connect(self.state / "estado.db", timeout=3)
            try:
                claude.llamar(
                    self.fake_q,
                    c,
                    clave=clave,
                    tipo="decision",
                    sistema="Sistema",
                    entrada=clave,
                    esquema=ESQUEMA,
                    usar_cache=False,
                )
            except Exception as exc:
                errores.append(exc)
            finally:
                c.close()

        t1 = threading.Thread(target=worker, args=("concurrente:1",))
        t2 = threading.Thread(target=worker, args=("concurrente:2",))

        t1.start()
        self.assertTrue(primera_dentro.wait(timeout=3))

        t2.start()
        liberar_primera.set()

        t1.join(timeout=5)
        t2.join(timeout=5)

        self.assertFalse(t1.is_alive())
        self.assertFalse(t2.is_alive())
        self.assertEqual(errores, [])
        self.assertEqual(max_activos, 1)
        self.assertEqual(self.run.call_count, 2)

    def test_migracion_idempotente_con_datos_existentes(self):
        """Evita destruir auditorías y veredictos al reiniciar el servicio."""
        self.llamar()

        antes = self.filas()[0]["id"]
        hash_antes = self.cache()[0]["hash"]

        claude.migrar(self.c)
        claude.migrar(self.c)

        self.assertEqual(len(self.filas()), 1)
        self.assertEqual(len(self.cache()), 1)
        self.assertEqual(self.filas()[0]["id"], antes)
        self.assertEqual(self.cache()[0]["hash"], hash_antes)

    def test_resumen_consumo_miles_de_filas(self):
        """Evita degradación excesiva al consultar el consumo acumulado."""
        import time

        datos = [
            (
                "2026-10-26",
                f"clave:{i}",
                "decision",
                "modelo",
                "low",
                1,
                0.01,
                100,
                20,
                10,
                5,
                0.2,
                1,
                None,
                f"hash:{i}",
            )
            for i in range(5000)
        ]

        self.c.executemany(
            """
            INSERT INTO claude_llamadas(
                fecha, clave, tipo, modelo, esfuerzo, turnos,
                coste_usd, tok_in, tok_out, tok_cache_lee,
                tok_cache_crea, segundos, ok, error, hash
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            datos,
        )
        self.c.commit()

        inicio = time.monotonic()
        resumen = claude.resumen_consumo(self.c)
        duracion = time.monotonic() - inicio

        self.assertEqual(resumen["llamadas"], 5000)
        self.assertEqual(resumen["ok"], 5000)
        self.assertAlmostEqual(resumen["usd"], 50.0)
        self.assertEqual(resumen["tok_entrada"], 575000)
        self.assertEqual(resumen["tok_salida"], 100000)
        self.assertLess(duracion, 3.0)

    # BUG: resumen_consumo suma tok_in + tok_cache_crea + tok_cache_lee
    # por fila. Si cualquiera de esos campos es NULL, SQLite convierte
    # toda la suma de esa fila en NULL y SUM la ignora.
    # Arreglo minimo: COALESCE individual en cada campo antes de sumar.
    def test_resumen_no_pierde_tokens_parciales(self):
        """Evita infracontar tokens cuando el CLI omite métricas opcionales."""
        self.c.execute(
            """
            INSERT INTO claude_llamadas(
                fecha, clave, tipo, tok_in, tok_out,
                tok_cache_lee, tok_cache_crea, ok
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-10-26",
                "parcial",
                "decision",
                120,
                40,
                None,
                None,
                1,
            ),
        )
        self.c.commit()

        resumen = claude.resumen_consumo(self.c)

        self.assertEqual(resumen["llamadas"], 1)
        self.assertEqual(resumen["ok"], 1)
        self.assertEqual(resumen["tok_entrada"], 120)
        self.assertEqual(resumen["tok_salida"], 40)



if __name__ == "__main__":
    unittest.main()
