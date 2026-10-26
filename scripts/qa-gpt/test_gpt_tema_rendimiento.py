import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones offline de rendimiento para qa_gpt, qa_lote, qa_pr y qa_cobertura."""

import json
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import qa_gpt as q
import qa_lote as L
import qa_pr as P
import qa_cobertura as cob


class BaseRendimiento(unittest.TestCase):
    """Aislamiento de SQLite, estado, repositorio y cachés entre pruebas."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)

        self.root = Path(self.tmp.name)
        self.state = self.root / "estado"
        self.repo = self.root / "repositorio"
        self.repo.mkdir()

        originales = {
            "STATE": q.STATE,
            "DB_PATH": q.DB_PATH,
            "ROOT": q.ROOT,
            "WT": q.WT,
            "LOCK": q.Lock.path,
            "CACHE": cob._CACHE_DIR,
        }

        def restaurar():
            q.STATE = originales["STATE"]
            q.DB_PATH = originales["DB_PATH"]
            q.ROOT = originales["ROOT"]
            q.WT = originales["WT"]
            q.Lock.path = originales["LOCK"]
            cob._CACHE_DIR = originales["CACHE"]
            cob.olvidar_git()

        self.addCleanup(restaurar)

        q.STATE = self.state
        q.DB_PATH = self.state / "estado.db"
        q.ROOT = self.repo
        q.WT = self.state / "worktrees"
        q.Lock.path = self.state / "worker.lock"
        cob._CACHE_DIR = self.state / "cache"

        cob.olvidar_git()

        self.c = q.db()
        self.addCleanup(self.c.close)

        self.fecha = q.now()

    def medir(self, funcion, limite=3.0):
        inicio = time.perf_counter()
        resultado = funcion()
        duracion = time.perf_counter() - inicio
        self.assertLess(
            duracion,
            limite,
            f"{funcion!r} tardó {duracion:.3f}s; límite {limite:.3f}s",
        )
        return resultado

    def propuestas(self, n, estado="aceptada", rama=None):
        filas = []
        for i in range(n):
            ident = i + 1
            datos = {
                "titulo": f"Propuesta {ident}",
                "categoria": "regresion",
                "ficheros_nuevos": [
                    {
                        "ruta": f"tests/test_rendimiento_{ident}.py",
                        "contenido": "assert True\n",
                    }
                ],
            }
            filas.append(
                (
                    ident,
                    f"rendimiento-{ident}",
                    f"zona:{ident % 30}",
                    f"Propuesta {ident}",
                    json.dumps(datos),
                    estado,
                    rama,
                    self.fecha,
                    self.fecha,
                )
            )

        self.c.executemany(
            """
            INSERT INTO propuestas
            (id, huella, area, titulo, datos, estado, rama, creado, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            filas,
        )
        self.c.commit()

    def ramas(self, n, estado="preparada"):
        filas = [
            (
                f"gpt-qa/rendimiento-{i:05d}",
                f"zona:{i % 30}",
                "",
                f"{i + 1:040x}",
                estado,
            )
            for i in range(n)
        ]

        self.c.executemany(
            """
            INSERT INTO ramas(rama, area, ruta, sha, estado)
            VALUES (?, ?, ?, ?, ?)
            """,
            filas,
        )
        self.c.commit()

    def indice(self, tabla, columnas):
        indices = self.c.execute(
            f"PRAGMA index_list({tabla})"
        ).fetchall()

        for indice in indices:
            nombre = indice[1]
            presentes = [
                fila[2]
                for fila in self.c.execute(
                    f"PRAGMA index_info('{nombre}')"
                )
            ]
            if presentes[:len(columnas)] == list(columnas):
                return True

        return False

    def plan(self, sql, parametros=()):
        return [
            str(fila[3]).upper()
            for fila in self.c.execute(
                "EXPLAIN QUERY PLAN " + sql,
                parametros,
            )
        ]

    def lote(self, **config):
        cfg = {
            "tam_lote": 30,
            "poll_s": 0,
            "concurrencia": 2,
            "max_horas": 1,
            "node_modules": str(self.root / "sin-node-modules"),
            "timeout_test_s": 30,
            **config,
        }

        gh = Mock()
        gh.ok.return_value = True

        lo = L.Lote(
            q,
            gh=gh,
            runner=Mock(return_value=(0, "")),
            sleep=lambda _: None,
            out=lambda _: None,
            cfg=cfg,
        )
        self.addCleanup(lo.c.close)
        return lo


class RendimientoSQLite(BaseRendimiento):

    def test_inicializacion_miles_de_propuestas(self):
        """Evita que abrir estado.db degrade con miles de propuestas históricas."""
        self.propuestas(5000)

        def abrir():
            conexion = q.db()
            try:
                return conexion.execute(
                    "SELECT COUNT(*) FROM propuestas"
                ).fetchone()[0]
            finally:
                conexion.close()

        self.assertEqual(self.medir(abrir, 4.0), 5000)

    def test_consulta_propuesta_por_id(self):
        """Evita búsquedas lineales al recuperar propuestas individuales."""
        self.propuestas(6000)

        ids = [1, 1500, 3000, 4500, 6000]

        def consultar():
            for _ in range(100):
                for ident in ids:
                    fila = self.c.execute(
                        "SELECT datos FROM propuestas WHERE id=?",
                        (ident,),
                    ).fetchone()
                    self.assertIsNotNone(fila)

        self.medir(consultar, 2.0)

        plan = self.plan(
            "SELECT datos FROM propuestas WHERE id=?",
            (3000,),
        )
        self.assertTrue(
            any("PRIMARY KEY" in p or "SEARCH" in p for p in plan),
            plan,
        )

    def test_consulta_job_por_clave(self):
        """Evita exploraciones completas de jobs al deduplicar peticiones."""
        filas = [
            (
                f"job-rendimiento-{i}",
                "zona",
                "zona:rendimiento",
                "pendiente",
                "{}",
                self.fecha,
                self.fecha,
            )
            for i in range(6000)
        ]

        self.c.executemany(
            """
            INSERT INTO jobs
            (clave, tipo, area, estado, payload, creado, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            filas,
        )
        self.c.commit()

        self.assertTrue(self.indice("jobs", ["clave"]))

        def consultar():
            for i in range(0, 6000, 7):
                fila = self.c.execute(
                    "SELECT id FROM jobs WHERE clave=?",
                    (f"job-rendimiento-{i}",),
                ).fetchone()
                self.assertIsNotNone(fila)

        self.medir(consultar, 2.0)

    def test_consulta_rama_por_nombre(self):
        """Evita escanear cientos de ramas para recuperar su estado."""
        self.ramas(500)

        self.assertTrue(self.indice("ramas", ["rama"]))

        def consultar():
            for _ in range(10):
                for i in range(500):
                    rama = f"gpt-qa/rendimiento-{i:05d}"
                    self.assertIsNotNone(
                        self.c.execute(
                            "SELECT sha FROM ramas WHERE rama=?",
                            (rama,),
                        ).fetchone()
                    )

        self.medir(consultar, 2.0)

    def test_reapertura_no_duplica_tecnicas(self):
        """Evita multiplicar las técnicas semilla al reiniciar el servicio."""
        inicial = self.c.execute(
            "SELECT COUNT(*) FROM tecnicas"
        ).fetchone()[0]

        def reabrir():
            for _ in range(12):
                conexion = q.db()
                conexion.close()

        self.medir(reabrir, 4.0)

        final = self.c.execute(
            "SELECT COUNT(*) FROM tecnicas"
        ).fetchone()[0]

        self.assertEqual(final, inicial)

    def test_reapertura_no_duplica_propuestas(self):
        """Evita que las migraciones repliquen propuestas tras reinicios."""
        self.propuestas(3000)

        for _ in range(5):
            conexion = q.db()
            conexion.close()

        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM propuestas"
            ).fetchone()[0],
            3000,
        )

    def test_actualizacion_masiva_de_estados(self):
        """Evita degradación excesiva al cerrar miles de propuestas."""
        self.propuestas(5000)

        def actualizar():
            self.c.execute(
                """
                UPDATE propuestas
                SET estado='ejecutada', actualizado=?
                WHERE estado='aceptada'
                """,
                (self.fecha,),
            )
            self.c.commit()

        self.medir(actualizar, 3.0)

        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM propuestas WHERE estado='ejecutada'"
            ).fetchone()[0],
            5000,
        )

    def test_consulta_estado_sin_corrupcion(self):
        """Evita resultados incoherentes al consultar miles de estados mixtos."""
        self.propuestas(6000)

        self.c.execute(
            "UPDATE propuestas SET estado='preparada' WHERE id % 3=0"
        )
        self.c.execute(
            "UPDATE propuestas SET estado='ejecutada' WHERE id % 3=1"
        )
        self.c.commit()

        def contar():
            return dict(
                self.c.execute(
                    """
                    SELECT estado, COUNT(*)
                    FROM propuestas
                    GROUP BY estado
                    """
                ).fetchall()
            )

        resultado = self.medir(contar, 2.0)

        self.assertEqual(sum(resultado.values()), 6000)
        self.assertEqual(resultado["preparada"], 2000)
        self.assertEqual(resultado["ejecutada"], 2000)
        self.assertEqual(resultado["aceptada"], 2000)


class RendimientoCobertura(BaseRendimiento):

    def test_normalizacion_unicode_masiva(self):
        """Evita degradación al normalizar miles de nombres con acentos."""
        textos = [
            f"Validación número {i}: información, ejecución y Ñandú"
            for i in range(10000)
        ]

        resultado = self.medir(
            lambda: [cob.norm(t) for t in textos],
            2.0,
        )

        self.assertEqual(len(resultado), 10000)
        self.assertIn("validacion", resultado[0])

    def test_tokenizacion_miles_de_descripciones(self):
        """Evita tokenización excesivamente costosa en propuestas largas."""
        textos = [
            (
                f"Validar comportamiento {i} ante errores de estado "
                "y recuperación de ejecución automática"
            )
            for i in range(5000)
        ]

        resultado = self.medir(
            lambda: [cob.tokens(t) for t in textos],
            2.0,
        )

        self.assertEqual(len(resultado), 5000)
        self.assertTrue(all(isinstance(x, set) for x in resultado))

    def test_huellas_conductuales_masivas(self):
        """Evita crecimiento cuadrático al calcular huellas de propuestas."""
        propuestas = [
            {
                "titulo": f"Validar funcionalidad {i}",
                "funcionalidad": f"Comportamiento número {i}",
                "invariante": "El estado final debe ser coherente",
                "tecnica": {"id": "regresion"},
                "ficheros_fuente": [
                    {"ruta": f"assets/modulo-{i % 50}.js"}
                ],
            }
            for i in range(5000)
        ]

        resultado = self.medir(
            lambda: [cob.datos_prop(p) for p in propuestas],
            3.0,
        )

        self.assertEqual(len(resultado), 5000)
        self.assertTrue(all(x["huella"] for x in resultado))

    def test_normalizar_comandos_miles_de_tests(self):
        """Evita búsquedas repetidas innecesarias al normalizar comandos."""
        propuesta = {
            "ficheros_nuevos": [
                {
                    "ruta": f"tests/test_rendimiento_{i}.py",
                    "contenido": "assert True\n",
                }
                for i in range(2000)
            ],
            "como_ejecutar": "",
        }

        self.medir(
            lambda: cob.normalizar_comandos(propuesta),
            3.0,
        )

        self.assertEqual(len(propuesta["pasos"]), 2000)
        self.assertTrue(
            all(p["argv"][0] == "python" for p in propuesta["pasos"])
        )

    def test_registro_masivo_tecnicas_sin_duplicados(self):
        """
        Verifica el registro y la idempotencia de 500 técnicas.

        registrar_tecnica realiza un commit SQLite por técnica nueva.
        En Windows, 500 commits durables pueden superar cuatro segundos
        por latencia de disco, antivirus y sincronización del journal.

        El límite original de cuatro segundos confundía el coste de
        durabilidad de SQLite con una regresión algorítmica. No es un
        defecto funcional: cada registro se confirma individualmente.

        Se mantiene el volumen de 500 técnicas y se concede un margen
        de doce segundos para la primera pasada. La segunda pasada,
        que únicamente comprueba IDs existentes, conserva un límite
        estricto de cuatro segundos.
        """

        def registrar():
            nuevas = 0
            for i in range(500):
                if cob.registrar_tecnica(
                    self.c,
                    {
                        "id": f"tecnica-rendimiento-{i}",
                        "nombre": f"Técnica de rendimiento {i}",
                        "palabras_clave": ["rendimiento", "regresion"],
                    },
                    self.fecha,
                ):
                    nuevas += 1
            return nuevas

        nuevas = self.medir(registrar, 12.0)
        self.assertEqual(nuevas, 500)

        cantidad = self.c.execute(
            """
            SELECT COUNT(*)
            FROM tecnicas
            WHERE id LIKE 'tecnica-rendimiento-%'
            """
        ).fetchone()[0]

        self.assertEqual(cantidad, 500)

        duplicadas = self.medir(registrar, 4.0)
        self.assertEqual(duplicadas, 0)

        cantidad2 = self.c.execute(
            """
            SELECT COUNT(*)
            FROM tecnicas
            WHERE id LIKE 'tecnica-rendimiento-%'
            """
        ).fetchone()[0]

        self.assertEqual(cantidad2, 500)

    def test_lectura_masiva_tecnicas(self):
        """Evita degradación al cargar el catálogo de técnicas."""
        for i in range(500):
            self.c.execute(
                """
                INSERT OR IGNORE INTO tecnicas
                (id, nombre, kw, aplica, origen, creada, nota)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"rendimiento-{i}",
                    f"Técnica {i}",
                    '["estado","regresion"]',
                    '["js","html"]',
                    "descubierta",
                    self.fecha,
                    "",
                ),
            )
        self.c.commit()

        resultado = self.medir(
            lambda: cob.tecnicas(self.c),
            2.0,
        )

        self.assertGreaterEqual(len(resultado), 500)

    def test_inventario_miles_de_rutas(self):
        """Evita crecimiento cuadrático al agrupar rutas del inventario."""
        rutas = [
            f"familia-{i % 80}/subdir/archivo-{i}.js"
            for i in range(8000)
        ]

        with patch.object(
            cob,
            "_git",
            return_value="\n".join(rutas),
        ):
            familias = self.medir(
                lambda: cob.familias_de(self.repo),
                2.0,
            )

        self.assertEqual(len(familias), 80)
        self.assertEqual(
            sum(len(x) for x in familias.values()),
            8000,
        )

    def test_cache_git_no_repite_consulta(self):
        """Evita relanzar git miles de veces para la misma lectura histórica."""
        cob.olvidar_git()

        contador = Mock()
        contador.return_value = Mock(
            returncode=0,
            stdout="archivo.py\n",
            stderr="",
        )

        with patch.object(cob, "run", contador):
            with patch.object(
                cob,
                "_cabeza",
                return_value="head|main",
            ):
                def consultar():
                    return [
                        cob._git(self.repo, "ls-files")
                        for _ in range(500)
                    ]

                resultado = self.medir(consultar, 3.0)

        self.assertEqual(len(resultado), 500)
        self.assertEqual(contador.call_count, 1)


class RendimientoPR(BaseRendimiento):

    def test_validacion_parche_grande(self):
        """Evita lentitud al validar reemplazos en archivos de tamaño realista."""
        contenido = (
            "function ejecutar() { return true; }\n"
            + "const dato = 123;\n" * 15000
        )

        parche = {
            "ficheros": [
                {
                    "ruta": "assets/rendimiento.js",
                    "reemplazos": [
                        {
                            "buscar": "function ejecutar() { return true; }",
                            "por": "function ejecutar() { return false; }",
                        }
                    ],
                }
            ]
        }

        ok, problemas, normalizado = self.medir(
            lambda: P.validar_parche(
                parche,
                lambda ruta: contenido,
            ),
            3.0,
        )

        self.assertTrue(ok, problemas)
        self.assertIsNotNone(normalizado)

    def test_validacion_parche_limita_ficheros(self):
        """Evita procesar parches enormes que superan el límite de seguridad."""
        parche = {
            "ficheros": [
                {
                    "ruta": f"assets/archivo-{i}.js",
                    "reemplazos": [
                        {"buscar": "a", "por": "b"}
                    ],
                }
                for i in range(1000)
            ]
        }

        lector = Mock(return_value="a")

        ok, problemas, normalizado = self.medir(
            lambda: P.validar_parche(parche, lector),
            1.0,
        )

        self.assertFalse(ok)
        self.assertTrue(problemas)
        self.assertIsNone(normalizado)
        lector.assert_not_called()

    def test_validacion_miles_de_rutas(self):
        """Evita expresiones regulares costosas al comprobar rutas de parches."""
        rutas = [
            f"assets/zona-{i % 50}/archivo-{i}.js"
            for i in range(10000)
        ]

        resultado = self.medir(
            lambda: [P.ruta_segura(r) for r in rutas],
            2.0,
        )

        self.assertTrue(all(x is None for x in resultado))

    def test_seleccion_candidatas_pr_con_volumen(self):
        """Evita consultas lentas al seleccionar causas aprobadas para PR."""
        filas = self.c.execute(
            "PRAGMA table_info(triaje)"
        ).fetchall()

        columnas = {fila[1] for fila in filas}

        necesarias = {
            "decision",
            "clase",
            "parche",
            "pr_estado",
        }

        self.assertTrue(
            necesarias.issubset(columnas),
            f"Esquema triaje incompleto: {columnas}",
        )

        disponibles = [
            col for col in (
                "decision",
                "clase",
                "parche",
                "pr_estado",
                "prioridad",
            )
            if col in columnas
        ]

        valores = {
            "decision": "corregir",
            "clase": "defecto_web",
            "parche": '{"ficheros":[]}',
            "pr_estado": "",
            "prioridad": "3",
        }

        sql = (
            f"INSERT INTO triaje ({','.join(disponibles)}) "
            f"VALUES ({','.join('?' for _ in disponibles)})"
        )

        self.c.executemany(
            sql,
            [
                tuple(valores[col] for col in disponibles)
                for _ in range(1500)
            ],
        )
        self.c.commit()

        pr = P.Pr(
            q,
            Mock(),
            Mock(return_value=(0, "")),
            out=lambda _: None,
        )

        resultado = self.medir(
            lambda: pr.candidatas(self.c),
            3.0,
        )

        self.assertEqual(len(resultado), 1500)

    def test_rutas_tests_pr_miles_de_propuestas(self):
        """Evita consultas excesivas al recuperar tests asociados a propuestas."""
        self.propuestas(3000)

        pr = P.Pr(
            q,
            Mock(),
            Mock(return_value=(0, "")),
            out=lambda _: None,
        )

        ids = list(range(1, 3001))

        resultado = self.medir(
            lambda: pr._rutas_tests(self.c, ids),
            4.0,
        )

        self.assertEqual(len(resultado), 3000)
        self.assertEqual(len(set(resultado)), 3000)


class RendimientoLote(BaseRendimiento):

    def test_busqueda_item_por_clave(self):
        """Evita escaneos completos al recuperar un item entre miles."""
        self.c.execute(
            """
            INSERT INTO lotes(inicio, estado)
            VALUES (?, 'en_curso')
            """,
            (self.fecha,),
        )
        lid = self.c.execute(
            "SELECT MAX(id) FROM lotes"
        ).fetchone()[0]

        filas = [
            (
                f"rama-{i}@{i:012x}",
                lid,
                f"rama-{i}",
                f"{i:040x}",
                "zona:rendimiento",
                "[]",
                "preparada",
                "{}",
                self.fecha,
                self.fecha,
            )
            for i in range(5000)
        ]

        self.c.executemany(
            """
            INSERT INTO lote_items
            (clave, lote_id, rama, sha, area, propuestas,
             estado, runs, creado, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            filas,
        )
        self.c.commit()

        lo = self.lote()

        def consultar():
            for i in range(0, 5000, 5):
                clave = f"rama-{i}@{i:012x}"
                self.assertIsNotNone(lo.item(clave))

        self.medir(consultar, 3.0)

        self.assertTrue(
            self.indice("lote_items", ["clave"])
        )

    def test_listado_items_lote_grande(self):
        """Evita lentitud al recuperar miles de items de un lote."""
        self.c.execute(
            """
            INSERT INTO lotes(inicio, estado)
            VALUES (?, 'en_curso')
            """,
            (self.fecha,),
        )
        lid = self.c.execute(
            "SELECT MAX(id) FROM lotes"
        ).fetchone()[0]

        filas = [
            (
                f"rendimiento-{i}@{i:012x}",
                lid,
                f"rendimiento-{i}",
                f"{i:040x}",
                "zona:rendimiento",
                "[]",
                "preparada",
                "{}",
                self.fecha,
                self.fecha,
            )
            for i in range(3000)
        ]

        self.c.executemany(
            """
            INSERT INTO lote_items
            (clave, lote_id, rama, sha, area, propuestas,
             estado, runs, creado, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            filas,
        )
        self.c.commit()

        lo = self.lote()

        resultado = self.medir(
            lambda: lo.items(lid),
            3.0,
        )

        self.assertEqual(len(resultado), 3000)

    def test_seleccion_ramas_preparadas(self):
        """Evita lentitud al localizar cientos de ramas pendientes de ejecución."""
        self.ramas(500)

        resultado = self.medir(
            lambda: self.c.execute(
                """
                SELECT rama, sha
                FROM ramas
                WHERE estado IN ('preparada', 'aprobada')
                """
            ).fetchall(),
            2.0,
        )

        self.assertEqual(len(resultado), 500)

    def test_lote_vacio_no_crea_items(self):
        """Evita trabajo innecesario y estados colgados cuando no hay propuestas."""
        lo = self.lote()

        with patch.object(q, "reparar_perdidas"):
            lid = self.medir(
                lo.abrir_lote,
                2.0,
            )

        cantidad = self.c.execute(
            "SELECT COUNT(*) FROM lote_items WHERE lote_id=?",
            (lid,),
        ).fetchone()[0]

        self.assertEqual(cantidad, 0)

    def test_consulta_propuestas_de_item(self):
        """Evita crecimiento cuadrático al resolver miles de IDs de un item."""
        self.propuestas(2500)

        self.c.execute(
            """
            INSERT INTO lotes(inicio, estado)
            VALUES (?, 'en_curso')
            """,
            (self.fecha,),
        )
        lid = self.c.execute(
            "SELECT MAX(id) FROM lotes"
        ).fetchone()[0]

        ids = list(range(1, 2501))

        self.c.execute(
            """
            INSERT INTO lote_items
            (clave, lote_id, rama, sha, area, propuestas,
             estado, runs, creado, actualizado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "rendimiento@123456789abc",
                lid,
                "rendimiento",
                "123456789abcdef",
                "zona:rendimiento",
                json.dumps(ids),
                "preparada",
                "{}",
                self.fecha,
                self.fecha,
            ),
        )
        self.c.commit()

        lo = self.lote()
        item = lo.item("rendimiento@123456789abc")

        resultado = self.medir(
            lambda: lo.propuestas_de(item),
            4.0,
        )

        self.assertEqual(len(resultado), 2500)
        self.assertTrue(all(r is not None for r in resultado))


if __name__ == "__main__":
    unittest.main()
