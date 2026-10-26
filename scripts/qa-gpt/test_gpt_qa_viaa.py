import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones aisladas de qa_viaa: persistencia, cobertura, navegador y recuperación."""

import json
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import qa_gpt as q
import qa_viaa as V


RES = {
    "paginas": 10,
    "contratos": 15,
    "aserciones": 150,
    "fallos_brutos": 3,
    "fallos_unicos": 1,
    "segundos": 0.1,
    "familias": {"libros": 10},
}


def hallazgo(
    contrato="seo-title",
    causa="titulo ausente",
    familia="libros",
    urls=None,
):
    urls = urls if urls is not None else ["/libros/a/", "/libros/b/"]
    return {
        "contrato": contrato,
        "causa": causa,
        "familia": familia,
        "paginas": len(urls),
        "urls": urls,
        "ejemplos": [f"{urls[0]}: fallo"] if urls else [],
    }


class FakeQ:
    def __init__(self, state):
        self.STATE = state
        self.sha = "a" * 40
        self.calls = []

    def now(self):
        return "2026-10-26T10:00:00"

    def git(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.sha + "\n"


class FakeServer:
    instances = []

    def __init__(self, root, puerto):
        self.root = root
        self.puerto = puerto
        self.entered = False
        self.exited = False
        self.__class__.instances.append(self)

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, *args):
        self.exited = True
        return False


class Base(unittest.TestCase):
    def setUp(self):
        original = (
            q.STATE,
            q.DB_PATH,
            q.Lock.path,
            q.ROOT,
            q.WT,
            V.NODE_MODULES,
        )

        def restaurar():
            (
                q.STATE,
                q.DB_PATH,
                q.Lock.path,
                q.ROOT,
                q.WT,
                V.NODE_MODULES,
            ) = original

        self.addCleanup(restaurar)

        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)

        self.base = Path(self.tmp.name)
        self.root = self.base / "repo"
        self.root.mkdir()

        q.STATE = self.base / "state"
        q.STATE.mkdir()
        q.DB_PATH = q.STATE / "qa.sqlite"
        q.Lock.path = q.STATE / "worker.lock"
        q.ROOT = self.root
        q.WT = q.STATE / "worktrees"

        V.NODE_MODULES = str(self.base / "node_modules")

        self.fakeq = FakeQ(q.STATE)
        self.out = []

        self.c = sqlite3.connect(str(q.DB_PATH), timeout=1)
        self.c.row_factory = sqlite3.Row
        self.addCleanup(self.c.close)

        V.migrar(self.c)
        self.c.commit()

        FakeServer.instances.clear()

    def registrar(self, tipo="estatico", grupos=None, sha="a" * 40):
        if grupos is None:
            grupos = [hallazgo()]
        V.registrar(
            self.c,
            self.fakeq,
            tipo,
            RES,
            grupos,
            sha,
            "comando de prueba",
        )

    def filas(self, tabla):
        return self.c.execute(f"SELECT * FROM {tabla}").fetchall()

    def resultado_navegador(self, hallazgos=None):
        if hallazgos is None:
            hallazgos = []
        return {
            "paginas": 1,
            "aserciones": 33,
            "segundos": 0.2,
            "hallazgos": hallazgos,
        }

    def ejecutar_navegador_simulado(
        self,
        resultado=None,
        returncode=0,
        stderr="",
        error=None,
        lista=None,
    ):
        if resultado is None:
            resultado = self.resultado_navegador()

        if lista is None:
            lista = ["/libros/a/"]

        def fake_run(args, **kwargs):
            if error is not None:
                raise error
            if resultado is not False:
                Path(args[-1]).write_text(
                    json.dumps(resultado),
                    encoding="utf-8",
                )
            return Mock(returncode=returncode, stderr=stderr, stdout="")

        with (
            patch.object(V.shutil, "which", return_value="node"),
            patch.object(V, "_puerto", return_value=18437),
            patch.object(V, "elegir_navegador", return_value=lista),
            patch.object(V.cob, "ServidorEstatico", FakeServer),
            patch.object(V.cob, "run", side_effect=fake_run),
            patch.object(V, "version_contratos", return_value="v1"),
        ):
            return V.navegador(
                self.c,
                self.fakeq,
                self.root,
                out=self.out.append,
                timeout=1,
            )


class TestPersistencia(Base):
    def test_migracion_idempotente_preserva_datos(self):
        """Evita que reiniciar el pipeline destruya hallazgos históricos."""
        self.registrar()
        V.migrar(self.c)
        V.migrar(self.c)

        self.assertEqual(len(self.filas("hallazgos")), 1)
        self.assertEqual(len(self.filas("viaa_runs")), 1)

    def test_registro_persiste_tras_reabrir_sqlite(self):
        """Evita perder resultados cuando EJECUTAR termina y vuelve a arrancar."""
        self.registrar()
        self.c.commit()

        with sqlite3.connect(str(q.DB_PATH)) as nueva:
            nueva.row_factory = sqlite3.Row
            self.assertEqual(
                nueva.execute("SELECT COUNT(*) FROM hallazgos").fetchone()[0],
                1,
            )
            self.assertEqual(
                nueva.execute("SELECT COUNT(*) FROM viaa_runs").fetchone()[0],
                1,
            )

    def test_actualizacion_conserva_identidad_y_primera_fecha(self):
        """Evita duplicar incidencias persistentes en ejecuciones sucesivas."""
        self.registrar(sha="a" * 40)
        primera = self.filas("hallazgos")[0]

        self.registrar(sha="b" * 40)
        segunda = self.filas("hallazgos")[0]

        self.assertEqual(len(self.filas("hallazgos")), 1)
        self.assertEqual(primera["clave"], segunda["clave"])
        self.assertEqual(primera["sha_primero"], segunda["sha_primero"])
        self.assertEqual(segunda["sha_ultimo"], "b" * 40)
        self.assertEqual(len(self.filas("viaa_runs")), 2)

    def test_reaparicion_reabre_hallazgo_resuelto(self):
        """Evita mantener como resuelto un defecto que vuelve a reproducirse."""
        self.registrar()
        self.registrar(grupos=[])
        self.assertEqual(self.filas("hallazgos")[0]["estado"], "resuelto")

        self.registrar(sha="b" * 40)
        self.assertEqual(self.filas("hallazgos")[0]["estado"], "a_triar")

    def test_hallazgo_navegador_no_se_resuelve_por_muestra_ausente(self):
        """Evita cerrar defectos porque la rotación no volvió a visitar su página."""
        self.registrar(tipo="navegador")
        self.registrar(tipo="navegador", grupos=[])

        self.assertEqual(self.filas("hallazgos")[0]["estado"], "a_triar")

    def test_hallazgos_de_tipos_distintos_no_colisionan(self):
        """Evita mezclar defectos estáticos y de navegador con igual causa."""
        h = hallazgo()
        self.registrar(tipo="estatico", grupos=[h])
        self.registrar(tipo="navegador", grupos=[h])

        filas = self.filas("hallazgos")
        self.assertEqual(len(filas), 2)
        self.assertEqual({r["tipo"] for r in filas}, {"estatico", "navegador"})

    def test_no_resuelve_clasificaciones_humanas(self):
        """Evita borrar decisiones humanas cuando desaparece un fallo estático."""
        estados = ("defecto_demostrado", "falso_positivo", "duplicado", "infra")

        for i, estado in enumerate(estados):
            h = hallazgo(contrato=f"contrato-{i}")
            self.registrar(grupos=[h])
            self.c.execute(
                "UPDATE hallazgos SET estado=? WHERE contrato=?",
                (estado, h["contrato"]),
            )

        self.c.commit()
        self.registrar(grupos=[])

        reales = {
            r["estado"]
            for r in self.c.execute("SELECT estado FROM hallazgos")
        }
        self.assertEqual(reales, set(estados))

    def test_registro_con_miles_de_hallazgos_no_duplica_filas(self):
        """Evita crecimiento explosivo de SQLite al repetir auditorías grandes."""
        grupos = [
            hallazgo(
                contrato=f"contrato-{i}",
                causa=f"causa-{i}",
                urls=[f"/libros/{i}/"],
            )
            for i in range(1200)
        ]

        inicio = time.monotonic()
        self.registrar(grupos=grupos)
        self.registrar(grupos=grupos)
        duracion = time.monotonic() - inicio

        self.assertEqual(len(self.filas("hallazgos")), 1200)
        self.assertEqual(len(self.filas("viaa_runs")), 2)
        self.assertLess(duracion, 10)


class TestEstatico(Base):
    def test_cache_evitar_reanalizar_mismo_sha_y_version(self):
        """Evita repetir auditorías costosas sin cambios de código ni contratos."""
        with (
            patch.object(V, "version_contratos", return_value="v1"),
            patch.object(V.qa_contratos, "ejecutar_sitio", return_value={
                **RES,
                "grupos": [hallazgo()],
            }) as ejecutar,
            patch.object(
                V.qa_contratos,
                "paginas_del_sitio",
                return_value={},
            ),
        ):
            primero = V.estatico(
                self.c, self.fakeq, self.root, out=self.out.append
            )
            segundo = V.estatico(
                self.c, self.fakeq, self.root, out=self.out.append
            )

        self.assertEqual((primero, segundo), (1, 1))
        ejecutar.assert_called_once()
        self.assertEqual(len(self.filas("viaa_runs")), 1)

    def test_cambio_version_contratos_invalida_cache(self):
        """Evita reutilizar validaciones antiguas después de modificar contratos."""
        with (
            patch.object(V, "version_contratos", side_effect=["v1", "v2", "v2"]),
            patch.object(V.qa_contratos, "ejecutar_sitio", return_value={
                **RES,
                "grupos": [],
            }) as ejecutar,
            patch.object(
                V.qa_contratos,
                "paginas_del_sitio",
                return_value={},
            ),
        ):
            V.estatico(self.c, self.fakeq, self.root, out=self.out.append)
            V.estatico(self.c, self.fakeq, self.root, out=self.out.append)

        self.assertEqual(ejecutar.call_count, 2)
        self.assertEqual(len(self.filas("viaa_runs")), 2)

    def test_forzar_ignora_cache(self):
        """Evita que una auditoría forzada devuelva resultados históricos."""
        with (
            patch.object(V, "version_contratos", return_value="v1"),
            patch.object(V.qa_contratos, "ejecutar_sitio", return_value={
                **RES,
                "grupos": [],
            }) as ejecutar,
            patch.object(
                V.qa_contratos,
                "paginas_del_sitio",
                return_value={},
            ),
        ):
            V.estatico(self.c, self.fakeq, self.root, out=self.out.append)
            V.estatico(
                self.c,
                self.fakeq,
                self.root,
                forzar=True,
                out=self.out.append,
            )

        self.assertEqual(ejecutar.call_count, 2)

    def test_fallo_auditoria_no_registra_exito(self):
        """Evita registrar auditorías completas cuando el analizador falla."""
        with (
            patch.object(V, "version_contratos", return_value="v1"),
            patch.object(
                V.qa_contratos,
                "ejecutar_sitio",
                side_effect=OSError("disco inaccesible"),
            ),
        ):
            with self.assertRaises(OSError):
                V.estatico(
                    self.c,
                    self.fakeq,
                    self.root,
                    out=self.out.append,
                )

        self.assertEqual(len(self.filas("viaa_runs")), 0)
        self.assertEqual(len(self.filas("hallazgos")), 0)

    # BUG: estatico() guarda la ejecución antes de completar la cobertura.
    # Si falla la escritura de viaa_cobertura, el siguiente arranque reutiliza
    # el SHA y nunca termina de registrar las páginas. Arreglo mínimo:
    # guardar hallazgos, ejecución y cobertura en una única transacción,
    # haciendo commit solamente al finalizar todo.
    def test_fallo_cobertura_no_deja_cache_incompleta(self):
        """Evita dar por completa una auditoría interrumpida al guardar cobertura."""
        with (
            patch.object(V, "version_contratos", return_value="v1"),
            patch.object(V.qa_contratos, "ejecutar_sitio", return_value={
                **RES,
                "grupos": [],
            }),
            patch.object(
                V.qa_contratos,
                "paginas_del_sitio",
                side_effect=OSError("lectura de sitemap interrumpida"),
            ),
        ):
            with self.assertRaises(OSError):
                V.estatico(
                    self.c,
                    self.fakeq,
                    self.root,
                    out=self.out.append,
                )

        self.assertEqual(len(self.filas("viaa_runs")), 0)


class TestRotacion(Base):
    def test_primero_paginas_nunca_visitadas(self):
        """Evita repetir páginas conocidas mientras quedan páginas sin auditar."""
        self.c.execute(
            "INSERT INTO viaa_cobertura(url,familia,navegador) VALUES(?,?,?)",
            ("/libros/a/", "libros", "2026-10-25"),
        )
        self.c.commit()

        with (
            patch.object(
                V.qa_contratos,
                "paginas_del_sitio",
                return_value={"libros": ["a", "b", "c"]},
            ),
            patch.object(
                V.qa_contratos,
                "url_de",
                side_effect=lambda root, ruta: f"https://x/libros/{ruta}/",
            ),
        ):
            elegidas = V.elegir_navegador(self.c, self.root, 2)

        self.assertEqual(elegidas, ["/libros/b/", "/libros/c/"])

    def test_paginas_antiguas_rotan_antes_que_recientes(self):
        """Evita que páginas antiguas queden permanentemente fuera del navegador."""
        for url, fecha in (
            ("/libros/a/", "2026-10-25"),
            ("/libros/b/", "2026-10-20"),
            ("/libros/c/", "2026-10-23"),
        ):
            self.c.execute(
                "INSERT INTO viaa_cobertura(url,familia,navegador) VALUES(?,?,?)",
                (url, "libros", fecha),
            )
        self.c.commit()

        with (
            patch.object(
                V.qa_contratos,
                "paginas_del_sitio",
                return_value={"libros": ["a", "b", "c"]},
            ),
            patch.object(
                V.qa_contratos,
                "url_de",
                side_effect=lambda root, ruta: f"https://x/libros/{ruta}/",
            ),
        ):
            elegidas = V.elegir_navegador(self.c, self.root, 2)

        self.assertEqual(elegidas, ["/libros/b/", "/libros/c/"])

    def test_familia_generales_tiene_cupo_triple(self):
        """Evita perder cobertura de rutas generales por aplicarles el cupo normal."""
        rutas = {
            "libros": ["l1", "l2", "l3", "l4"],
            "generales": [f"g{i}" for i in range(10)],
        }

        with (
            patch.object(
                V.qa_contratos,
                "paginas_del_sitio",
                return_value=rutas,
            ),
            patch.object(
                V.qa_contratos,
                "url_de",
                side_effect=lambda root, ruta: f"https://x/{ruta}/",
            ),
        ):
            elegidas = V.elegir_navegador(self.c, self.root, 2)

        self.assertEqual(len(elegidas), 8)
        self.assertEqual(
            sum(url.startswith("/g") for url in elegidas),
            6,
        )


class TestNavegador(Base):
    def test_node_ausente_no_arranca_servidor(self):
        """Evita abrir procesos o servidores cuando Node no está instalado."""
        with (
            patch.object(V.shutil, "which", return_value=None),
            patch.object(V.cob, "ServidorEstatico") as servidor,
            patch.object(V.cob, "run") as ejecutar,
        ):
            resultado = V.navegador(
                self.c,
                self.fakeq,
                self.root,
                out=self.out.append,
            )

        self.assertIsNone(resultado)
        servidor.assert_not_called()
        ejecutar.assert_not_called()
        self.assertEqual(len(self.filas("viaa_runs")), 0)

    def test_smoke_navegador_guarda_cobertura_y_run(self):
        """Evita ejecuciones correctas sin registro persistente de cobertura."""
        resultado = self.ejecutar_navegador_simulado()

        self.assertEqual(resultado, 0)
        self.assertEqual(len(self.filas("viaa_runs")), 1)

        fila = self.c.execute(
            "SELECT * FROM viaa_cobertura WHERE url='/libros/a/'"
        ).fetchone()

        self.assertIsNotNone(fila)
        self.assertIsNotNone(fila["navegador"])
        self.assertTrue(FakeServer.instances[-1].exited)

    def test_timeout_cierra_servidor_y_no_guarda_run(self):
        """Evita dejar servidores huérfanos tras agotar el tiempo de navegador."""
        with self.assertRaises(TimeoutError):
            self.ejecutar_navegador_simulado(
                error=TimeoutError("navegador bloqueado"),
            )

        self.assertTrue(FakeServer.instances[-1].exited)
        self.assertEqual(len(self.filas("viaa_runs")), 0)

    def test_error_subprocess_cierra_servidor(self):
        """Evita fugas del servidor local cuando falla el proceso de Node."""
        with self.assertRaises(OSError):
            self.ejecutar_navegador_simulado(
                error=OSError("no se pudo ejecutar Node"),
            )

        self.assertTrue(FakeServer.instances[-1].exited)
        self.assertEqual(len(self.filas("viaa_runs")), 0)

    def test_salida_no_cero_no_registra_auditoria(self):
        """Evita interpretar una ejecución fallida de Node como auditoría válida."""
        resultado = self.ejecutar_navegador_simulado(
            resultado=False,
            returncode=1,
            stderr="fallo simulado",
        )

        self.assertIsNone(resultado)
        self.assertEqual(len(self.filas("viaa_runs")), 0)
        self.assertTrue(FakeServer.instances[-1].exited)

    def test_resultado_anterior_no_se_reutiliza(self):
        """Evita aceptar un JSON antiguo cuando el navegador no genera uno nuevo."""
        salida = q.STATE / "auditoria"
        salida.mkdir()
        (salida / "navegador-ultimo.json").write_text(
            json.dumps(self.resultado_navegador()),
            encoding="utf-8",
        )

        resultado = self.ejecutar_navegador_simulado(
            resultado=False,
            returncode=0,
        )

        self.assertIsNone(resultado)
        self.assertEqual(len(self.filas("viaa_runs")), 0)

    def test_hallazgos_multivista_se_agrupan_por_causa(self):
        """Evita abrir incidencias duplicadas por cada resolución del navegador."""
        resultado = self.resultado_navegador([
            {
                "contrato": "titulo",
                "causa": "ausente",
                "url": "/libros/a/",
                "vista": "movil",
                "detalle": "sin h1",
            },
            {
                "contrato": "titulo",
                "causa": "ausente",
                "url": "/libros/a/",
                "vista": "desktop",
                "detalle": "sin h1",
            },
            {
                "contrato": "titulo",
                "causa": "ausente",
                "url": "/libros/b/",
                "vista": "tablet",
                "detalle": "sin h1",
            },
        ])

        n = self.ejecutar_navegador_simulado(
            resultado=resultado,
            lista=["/libros/a/", "/libros/b/"],
        )

        self.assertEqual(n, 1)

        fila = self.filas("hallazgos")[0]
        self.assertEqual(fila["paginas"], 2)
        self.assertEqual(
            json.loads(fila["urls"]),
            ["/libros/a/", "/libros/b/"],
        )

    # BUG: navegador() hace json.loads y accede directamente a las claves
    # del resultado sin validar su estructura. Un JSON truncado o inválido
    # propaga la excepción al llamador directo. Arreglo mínimo: validar
    # esquema y capturar JSONDecodeError/KeyError/TypeError, devolviendo
    # fallo de infraestructura sin registrar cobertura.
    def test_json_malformado_devuelve_fallo_infraestructura(self):
        """Evita que una salida JSON corrupta interrumpa la auditoría."""
        resultado = self.ejecutar_navegador_simulado(
            resultado={"paginas": 1},
        )

        self.assertIsNone(resultado)
        self.assertEqual(len(self.filas("viaa_runs")), 0)

    def test_ejecutar_continua_si_falla_navegador(self):
        """Evita que un fallo aislado del navegador impida terminar la Vía A."""
        with (
            patch.object(V, "estatico", return_value=4),
            patch.object(
                V,
                "navegador",
                side_effect=OSError("Node no responde"),
            ),
        ):
            resultado = V.ejecutar(
                self.c,
                self.fakeq,
                self.root,
                out=self.out.append,
            )

        self.assertEqual(resultado, {"estatico": 4, "navegador": None})
        self.assertTrue(
            any("infraestructura" in mensaje for mensaje in self.out)
        )


if __name__ == "__main__":
    unittest.main()
