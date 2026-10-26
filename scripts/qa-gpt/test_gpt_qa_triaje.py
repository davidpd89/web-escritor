import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones offline del triaje QA-GPT: decisiones, estados, reanudacion y aislamiento."""

import json
import sqlite3
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import qa_gpt as q
import qa_triaje as T


class BaseTriaje(unittest.TestCase):
    def setUp(self):
        """Aisla estado, BD, locks y repositorio para impedir efectos reales."""
        originales = {
            "STATE": q.STATE,
            "DB_PATH": q.DB_PATH,
            "ROOT": q.ROOT,
            "WT": q.WT,
            "LOCK": q.Lock.path,
        }

        def restaurar():
            q.STATE = originales["STATE"]
            q.DB_PATH = originales["DB_PATH"]
            q.ROOT = originales["ROOT"]
            q.WT = originales["WT"]
            q.Lock.path = originales["LOCK"]

        self.addCleanup(restaurar)

        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)

        self.base = Path(self.tmp.name)
        q.STATE = self.base / "state"
        q.DB_PATH = q.STATE / "estado.db"
        q.ROOT = self.base / "repo"
        q.WT = q.STATE / "worktrees"
        q.Lock.path = q.STATE / "worker.lock"

        q.STATE.mkdir(parents=True)
        q.ROOT.mkdir()
        q.WT.mkdir()

        self.c = q.db()
        self.addCleanup(self.c.close)

        T.migrar(self.c)

        self.c.execute("""
            CREATE TABLE IF NOT EXISTS lote_items (
                clave TEXT PRIMARY KEY,
                propuestas TEXT,
                local_log TEXT,
                detalle TEXT,
                estado TEXT
            )
        """)

        self.c.execute("""
            CREATE TABLE IF NOT EXISTS eventos (
                id INTEGER PRIMARY KEY,
                fecha TEXT,
                entidad TEXT,
                ident INTEGER,
                estado TEXT,
                nota TEXT
            )
        """)

        self.c.commit()

        self.git = Mock(return_value="")
        self.enqueue = Mock(return_value=True)
        self.estado_prop = Mock()

        self.fake = SimpleNamespace(
            STATE=q.STATE,
            ROOT=q.ROOT,
            HERE=Path(__file__).resolve().parent,
            CFG={"flujo": {"max_intentos": 2}},
            now=lambda: "2026-10-26T09:00:00",
            git=self.git,
            enqueue=self.enqueue,
            estado_prop=self.estado_prop,
            fill=lambda plantilla, **kw: plantilla,
        )

        self.contador = 0

    def fila(self, **campos):
        self.contador += 1
        n = self.contador

        datos = {
            "grupo": f"firma{n}#causa",
            "causa": f"Defecto reproducible {n}",
            "clase": "defecto_web",
            "propuestas": [n],
            "items": [f"gpt-qa/rama{n}@abc123"],
            "evidencia": "AssertionError: comportamiento incorrecto",
            "reproduccion": "python -m unittest",
            "arreglo": "Corregir el comportamiento",
            "fuente": "gpt",
            "estado": "triado",
        }
        datos.update(campos)

        extras = {
            "firma": f"firma{n}",
            "analisis": json.dumps({
                "archivos_a_modificar": ["assets/app.js"],
                "comportamiento_esperado": "resultado correcto",
                "comportamiento_observado": "resultado incorrecto",
            }),
            "decision": None,
            "decision_json": None,
            "parche": None,
        }

        for k in list(extras):
            if k in datos:
                extras[k] = datos.pop(k)

        T.guardar(
            self.c,
            self.fake.now(),
            datos["grupo"],
            datos["causa"],
            datos["clase"],
            datos["propuestas"],
            datos["items"],
            datos["evidencia"],
            datos["reproduccion"],
            datos["arreglo"],
            datos["fuente"],
            estado=datos["estado"],
            **extras,
        )

        return self.c.execute(
            "SELECT * FROM triaje WHERE grupo=?",
            (datos["grupo"],),
        ).fetchone()

    def refrescar(self, row):
        return self.c.execute(
            "SELECT * FROM triaje WHERE id=?",
            (row["id"],),
        ).fetchone()

    def decision(self, row, tipo="corregir", **cambios):
        d = {
            "id": row["id"],
            "decision": tipo,
            "prioridad": 2,
            "causa_probable": "Error comprobado",
            "justificacion": "Existe reproduccion verificable",
            "confianza": "alta",
            "archivos": ["assets/app.js"],
            "criterio_aceptacion": "El test falla antes y pasa despues",
            "relacionados": [],
        }
        d.update(cambios)
        return d

    def item(self, clave, estado="fallo_test", propuestas=None, log=None):
        self.c.execute(
            """
            INSERT INTO lote_items
            (clave, propuestas, local_log, detalle, estado)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                clave,
                json.dumps(propuestas or []),
                str(log) if log else "",
                "AssertionError: fallo remoto",
                estado,
            ),
        )
        self.c.commit()

    def log(self, nombre, contenido):
        ruta = q.STATE / nombre
        ruta.write_text(contenido, encoding="utf-8")
        return ruta


class TestPersistencia(BaseTriaje):

    def test_migracion_idempotente_con_datos_existentes(self):
        """Evita perder decisiones al reiniciar y ejecutar migraciones repetidas."""
        row = self.fila()

        T.migrar(self.c)
        T.migrar(self.c)

        actual = self.refrescar(row)

        self.assertEqual(actual["grupo"], row["grupo"])
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM triaje WHERE grupo=?",
                (row["grupo"],),
            ).fetchone()[0],
            1,
        )

        columnas = {
            r[1] for r in self.c.execute("PRAGMA table_info(triaje)")
        }

        self.assertTrue({
            "decision",
            "decision_hash",
            "decision_json",
            "intentos_dev",
            "dev_estado",
            "duplicado_de",
        }.issubset(columnas))

    def test_guardar_mismo_grupo_no_duplica_expediente(self):
        """Evita duplicar una causa al reingerir un job tras una caida."""
        row = self.fila()

        T.guardar(
            self.c,
            self.fake.now(),
            row["grupo"],
            "Causa actualizada",
            "defecto_web",
            [101],
            ["rama@sha"],
            "evidencia nueva",
            "reproduccion",
            "arreglo",
            "gpt",
        )

        filas = self.c.execute(
            "SELECT * FROM triaje WHERE grupo=?",
            (row["grupo"],),
        ).fetchall()

        self.assertEqual(len(filas), 1)
        self.assertEqual(filas[0]["causa_raiz"], "Causa actualizada")

    def test_guardar_conserva_decision_preexistente(self):
        """Evita borrar la aprobacion tecnica al actualizar evidencia del mismo grupo."""
        row = self.fila()
        d = self.decision(row)

        T.aplicar_decision(self.fake, self.c, row, d, "huella")

        T.guardar(
            self.c,
            self.fake.now(),
            row["grupo"],
            "Evidencia ampliada",
            "defecto_web",
            [row["id"]],
            ["rama@sha"],
            "nueva evidencia",
            "reproduccion",
            "arreglo",
            "gpt",
        )

        actual = self.refrescar(row)

        self.assertEqual(actual["decision"], "corregir")
        self.assertEqual(actual["decision_hash"], "huella")

    def test_decision_y_evento_persisten_tras_reabrir_bd(self):
        """Evita decisiones perdidas por falta de commit antes de detener EJECUTAR."""
        row = self.fila()
        d = self.decision(row)

        T.aplicar_decision(self.fake, self.c, row, d, "hash-persistente")

        segunda = sqlite3.connect(str(q.DB_PATH), timeout=1)
        self.addCleanup(segunda.close)

        decision = segunda.execute(
            "SELECT decision, decision_hash FROM triaje WHERE id=?",
            (row["id"],),
        ).fetchone()

        eventos = segunda.execute(
            "SELECT COUNT(*) FROM eventos WHERE entidad='triaje' AND ident=?",
            (row["id"],),
        ).fetchone()[0]

        self.assertEqual(decision, ("corregir", "hash-persistente"))
        self.assertEqual(eventos, 1)


class TestDecisiones(BaseTriaje):

    def test_corregir_sin_criterio_no_autoriza_desarrollo(self):
        """Evita abrir PR por una aprobacion sin criterio de aceptacion."""
        row = self.fila()
        d = self.decision(row, criterio_aceptacion="  ")

        resultado = T.aplicar_decision(
            self.fake, self.c, row, d, "hash"
        )

        self.assertEqual(resultado, "necesita_evidencia")
        self.assertEqual(
            self.refrescar(row)["decision"],
            "necesita_evidencia",
        )

    def test_corregir_sin_archivos_no_autoriza_desarrollo(self):
        """Evita desarrollar una correccion sin archivos identificados."""
        row = self.fila()
        d = self.decision(row, archivos=[])

        resultado = T.aplicar_decision(
            self.fake, self.c, row, d, "hash"
        )

        self.assertEqual(resultado, "necesita_evidencia")
        self.assertFalse(
            T.encolar_desarrollo(
                self.fake, self.c, self.refrescar(row)
            )
        )
        self.enqueue.assert_not_called()

    def test_corregir_con_confianza_baja_se_degrada(self):
        """Evita fusionar cambios basados en diagnosticos de baja confianza."""
        row = self.fila()
        d = self.decision(row, confianza="baja")

        resultado = T.aplicar_decision(
            self.fake, self.c, row, d, "hash"
        )

        self.assertEqual(resultado, "necesita_evidencia")

    def test_duplicado_sin_referencia_no_se_acepta(self):
        """Evita cerrar un defecto como duplicado sin identificar su causa original."""
        row = self.fila()
        d = self.decision(
            row, tipo="duplicado", relacionados=[]
        )

        resultado = T.aplicar_decision(
            self.fake, self.c, row, d, "hash"
        )

        self.assertEqual(resultado, "necesita_evidencia")
        self.assertIsNone(self.refrescar(row)["duplicado_de"])

    def test_duplicado_valido_guarda_referencia(self):
        """Evita perder la trazabilidad entre expedientes duplicados."""
        original = self.fila()
        duplicado = self.fila()

        d = self.decision(
            duplicado,
            tipo="duplicado",
            relacionados=[original["id"]],
        )

        resultado = T.aplicar_decision(
            self.fake, self.c, duplicado, d, "hash"
        )

        self.assertEqual(resultado, "duplicado")

        # duplicado_de almacena el identificador como TEXT.
        # La referencia numerica se serializa a cadena; no es un bug.
        self.assertEqual(
            self.refrescar(duplicado)["duplicado_de"],
            str(original["id"]),
        )

    def test_reglas_previas_no_aprueban_test_roto(self):
        """Evita tratar un test incorrecto como defecto del producto."""
        row = self.fila(
            clase="test_roto",
            analisis=json.dumps({"es_defecto_producto": False}),
        )

        resultado = T.reglas_previas(row)

        self.assertEqual(resultado[0], "test_incorrecto")

    def test_test_roto_con_defecto_real_exige_revision(self):
        """Evita descartar defectos reales ocultos tras un test mal planteado."""
        row = self.fila(
            clase="test_roto",
            analisis=json.dumps({"es_defecto_producto": True}),
        )

        self.assertIsNone(T.reglas_previas(row))

    def test_respuesta_sin_grupos_no_genera_aprobacion(self):
        """Evita aprobar una causa cuando GPT devuelve una respuesta vacia."""
        row = self.fila(
            grupo="firma-vacia#sin_grupos",
            clase="sin_clasificar",
        )

        resultado = T.reglas_previas(row)

        self.assertEqual(resultado[0], "necesita_evidencia")

    def test_decision_automatica_no_llama_claude(self):
        """Evita gastar consultas externas para fallos de infraestructura ya clasificados."""
        row = self.fila(clase="infraestructura")

        with patch("qa_claude.llamar") as llamar:
            n = T.decidir_pendientes(
                self.fake, self.c, out=lambda _: None
            )

        self.assertGreaterEqual(n, 1)
        llamar.assert_not_called()
        self.assertEqual(
            self.refrescar(row)["decision"],
            "infraestructura",
        )

    def test_error_claude_no_deja_decision_parcial(self):
        """Evita aprobar expedientes cuando Claude falla por red o servicio."""
        import qa_claude

        row = self.fila(clase="sin_clasificar")

        with patch.object(T, "expediente", return_value={"id": row["id"]}), \
             patch.object(
                 qa_claude,
                 "llamar",
                 side_effect=qa_claude.ClaudeError("HTTP 503"),
             ):
            n = T.decidir_pendientes(
                self.fake, self.c, out=lambda _: None
            )

        self.assertEqual(n, 0)
        self.assertIsNone(self.refrescar(row)["decision"])

    def test_respuesta_parcial_no_aprueba_id_omitido(self):
        """Evita dar por aprobados expedientes ausentes de la respuesta de Claude."""
        import qa_claude

        primero = self.fila(clase="sin_clasificar")
        segundo = self.fila(clase="sin_clasificar")

        respuesta = {
            "decisiones": [
                self.decision(primero, tipo="rechazar")
            ]
        }

        with patch.object(
            T, "expediente",
            side_effect=lambda q_, c_, row, prs: {"id": row["id"]},
        ), patch.object(
            qa_claude, "llamar", return_value=(respuesta, {})
        ):
            T.decidir_pendientes(
                self.fake, self.c, out=lambda _: None
            )

        self.assertEqual(
            self.refrescar(primero)["decision"], "rechazar"
        )
        self.assertIsNone(self.refrescar(segundo)["decision"])


class TestReanudacionYDesarrollo(BaseTriaje):

    def test_desarrollo_rechazado_no_encola_jobs(self):
        """Evita generar parches para causas rechazadas por el filtro tecnico."""
        row = self.fila(decision="rechazar")

        ok = T.encolar_desarrollo(
            self.fake, self.c, row
        )

        self.assertFalse(ok)
        self.enqueue.assert_not_called()

    def test_desarrollo_respeta_limite_de_intentos(self):
        """Evita bucles infinitos de reparacion cuando GPT no consigue arreglar un defecto."""
        row = self.fila(
            decision="corregir",
            decision_json=json.dumps(
                self.decision(
                    {"id": 1},
                    tipo="corregir",
                )
            ),
        )

        self.assertTrue(
            T.encolar_desarrollo(
                self.fake, self.c, row
            )
        )

        row = self.refrescar(row)
        self.assertEqual(row["intentos_dev"], 1)

        self.assertTrue(
            T.encolar_desarrollo(
                self.fake, self.c, row
            )
        )

        row = self.refrescar(row)
        self.assertEqual(row["intentos_dev"], 2)

        self.assertFalse(
            T.encolar_desarrollo(
                self.fake, self.c, row
            )
        )

        self.assertEqual(self.enqueue.call_count, 2)

    def test_enqueue_fallido_no_consume_intento(self):
        """Evita agotar reparaciones cuando falla la escritura del job en cola."""
        row = self.fila(
            decision="corregir",
            decision_json=json.dumps(
                self.decision({"id": 1})
            ),
        )

        self.enqueue.return_value = False

        ok = T.encolar_desarrollo(
            self.fake, self.c, row
        )

        self.assertFalse(ok)

        actual = self.refrescar(row)

        self.assertEqual(actual["intentos_dev"], 0)
        self.assertNotEqual(actual["dev_estado"], "en_desarrollo")

    def test_desarrollo_sin_parche_queda_registrado(self):
        """Evita que una respuesta GPT sin parche deje el desarrollo indefinidamente abierto."""
        row = self.fila(decision="corregir")

        resultado = T.ingest_desarrollo(
            self.fake,
            self.c,
            {"id": row["id"]},
            {
                "parche": None,
                "explicacion": "No existe una correccion segura",
            },
        )

        actual = self.refrescar(row)

        self.assertEqual(resultado, 1)
        self.assertEqual(actual["dev_estado"], "sin_parche")
        self.assertIn(
            "No existe una correccion segura",
            actual["pr_detalle"],
        )

    def test_parche_invalido_no_sustituye_el_anterior(self):
        """Evita destruir un parche recuperable cuando una reparacion posterior falla."""
        anterior = json.dumps({
            "ficheros": [{
                "ruta": "assets/app.js",
                "reemplazos": [{"de": "viejo", "por": "nuevo"}],
            }]
        })

        row = self.fila(
            decision="corregir",
            parche=anterior,
        )

        with patch(
            "qa_pr.validar_parche",
            return_value=(False, ["texto ausente"], {}),
        ):
            T.ingest_desarrollo(
                self.fake,
                self.c,
                {"id": row["id"]},
                {
                    "parche": {"ficheros": []},
                    "explicacion": "Intento fallido",
                },
            )

        actual = self.refrescar(row)

        self.assertEqual(actual["parche"], anterior)
        self.assertEqual(actual["dev_estado"], "parche_invalido")
        self.assertFalse(json.loads(actual["validacion"])["ok"])


class TestAgrupacionYRendimiento(BaseTriaje):

    def test_firma_normaliza_rutas_y_numeros(self):
        """Evita repetir consultas GPT por diferencias irrelevantes de ruta o linea."""
        uno = (
            "AssertionError: C:\\GIT\\web\\tests\\test_x.py "
            "line 123 expected 4"
        )
        dos = (
            "AssertionError: D:\\TEMP\\repo\\tests\\test_x.py "
            "line 987 expected 8"
        )

        self.assertEqual(
            T.firma(uno)[0],
            T.firma(dos)[0],
        )

    def test_actions_sin_log_local_conserva_fallo(self):
        """Evita perder un fallo remoto cuando falta el fichero de salida de Actions."""
        clave = "gpt-qa/prueba@abc123"

        self.item(
            clave,
            estado="actions_fallida",
            propuestas=[17],
        )

        fila = self.c.execute(
            "SELECT * FROM lote_items WHERE clave=?",
            (clave,),
        ).fetchone()

        fallos = T.fallos_de_item(
            self.c,
            fila,
            q.STATE / "lote",
        )

        self.assertEqual(len(fallos), 1)
        self.assertEqual(fallos[0]["origen"], "actions")
        self.assertEqual(fallos[0]["item"], clave)

    def test_agrupacion_misma_causa_no_duplica_consulta(self):
        """Evita consultar GPT una vez por cada rama que reproduce el mismo fallo."""
        contenido = (
            "### propuesta #1 python -m unittest tests/test_a.py -> exit 1\n"
            "AssertionError: resultado incorrecto\n"
        )

        for n in range(2):
            ruta = self.log(f"fallo-{n}.log", contenido)
            self.item(
                f"gpt-qa/rama{n}@sha{n}",
                propuestas=[1],
                log=ruta,
            )

        nuevos, cubiertos = T.grupos_pendientes(
            self.c,
            q.STATE / "lote",
        )

        self.assertEqual(len(nuevos), 1)
        self.assertEqual(nuevos[0]["n"], 2)
        self.assertEqual(len(cubiertos), 0)

    def test_agrupacion_miles_de_fallos_acota_representantes(self):
        """Evita payloads gigantes y tiempos excesivos al agrupar miles de fallos."""
        fallos = [
            {
                "firma": "misma-causa",
                "item": f"rama-{n}@sha",
                "propuesta": n,
                "ruta": "tests/test_web.py",
                "log": "AssertionError: fallo",
            }
            for n in range(3000)
        ]

        inicio = time.monotonic()

        with patch.object(
            T, "fallos_pendientes", return_value=fallos
        ):
            nuevos, cubiertos = T.grupos_pendientes(
                self.c,
                q.STATE / "lote",
            )

        duracion = time.monotonic() - inicio

        self.assertLess(duracion, 5)
        self.assertEqual(len(nuevos), 1)
        self.assertEqual(nuevos[0]["n"], 3000)
        self.assertLessEqual(
            len(nuevos[0]["fallos"]),
            T.MAX_REPRESENTANTES,
        )
        self.assertFalse(cubiertos)


if __name__ == "__main__":
    unittest.main()
