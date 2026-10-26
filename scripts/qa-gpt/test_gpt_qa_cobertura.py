import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
import os
import sqlite3
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import qa_cobertura as cob
import qa_gpt as q


class CoberturaRobustez(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "repo"
        self.root.mkdir()
        self.state = self.base / "state"
        self.state.mkdir()

        for obj, attr, value in (
            (q, "STATE", self.state),
            (q, "DB_PATH", self.state / "estado.db"),
            (q, "ROOT", self.root),
            (q, "WT", self.state / "wt"),
            (q.Lock, "path", self.state / "worker.lock"),
            (cob, "_CACHE_DIR", self.state / "cache"),
        ):
            old = getattr(obj, attr)
            setattr(obj, attr, value)
            self.addCleanup(setattr, obj, attr, old)

        cob.olvidar_git()
        self.addCleanup(cob.olvidar_git)
        self.c = q.db()
        self.addCleanup(self.c.close)
        self.cfg = {
            "areas": [
                {"id": "zona-a", "riesgo": 5, "fuentes": ["zona-a/"]},
                {"id": "zona-b", "riesgo": 3, "fuentes": ["zona-b/"]},
            ],
            "tipos": [
                {"id": "unitaria", "nombre": "Unitaria",
                 "kw": ["assert", "unittest"], "aplica": ["js", "generador"]},
                {"id": "integracion", "nombre": "Integracion",
                 "kw": ["integracion"], "aplica": ["html", "js"]},
            ],
            "tecnicas_semilla": [],
        }
        cob.sembrar_tecnicas(self.c, self.cfg, q.now())

    def fichero(self, ruta, texto=""):
        p = self.root / ruta
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8")
        return p

    def git_falso(self, archivos, tests=(), head="abc123", commits="2"):
        def respuesta(root, *args):
            if args[:2] == ("rev-parse", "--short"):
                return head
            if args and args[0] == "ls-files":
                if len(args) == 1:
                    return "\n".join(archivos)
                return "\n".join(tests)
            if args and args[0] == "log":
                return "feed123"
            if args and args[0] == "rev-list":
                return commits
            return ""
        return respuesta

    def construir(self, archivos, tests=(), head="abc123", forzar=False,
                  commits="2"):
        with patch.object(
            cob, "_git",
            side_effect=self.git_falso(archivos, tests, head, commits)
        ):
            return cob.construir(
                self.c, self.root, self.cfg, q.now(), forzar=forzar
            )

    def test_inventario_no_incluye_carpetas_operativas(self):
        """Evita gastar peticiones GPT en tests, artefactos y dependencias."""
        rutas = [
            "zona-a/index.html",
            "tests/test_zona.py",
            "qa/check.mjs",
            ".github/workflows/qa.yml",
            "node_modules/lib/index.js",
            "docs/guia.html",
            "artifacts/informe.json",
        ]
        with patch.object(cob, "_git", return_value="\n".join(rutas)):
            familias = cob.familias_de(self.root)
        self.assertEqual(familias, {"zona-a": ["zona-a/index.html"]})

    def test_inventario_con_git_sin_archivos(self):
        """Evita fabricar familias cuando git devuelve un inventario vacío."""
        with patch.object(cob, "_git", return_value=""):
            self.assertEqual(cob.familias_de(self.root), {})

    def test_git_fallido_no_persiste_salida_parcial(self):
        """Evita que un git fallido contamine la caché de cobertura."""
        fallido = subprocess.CompletedProcess(
            [], 128, stdout="zona-fantasma/index.html\n", stderr="fatal"
        )
        correcto = subprocess.CompletedProcess(
            [], 0, stdout="zona-a/index.html\n", stderr=""
        )
        cabeza = subprocess.CompletedProcess(
            [], 0, stdout="abc123\nfed456\n", stderr=""
        )
        with patch.object(cob, "run", side_effect=[cabeza, fallido, correcto]) as run:
            primera = cob._git(self.root, "ls-files")
            segunda = cob._git(self.root, "ls-files")
        self.assertEqual(run.call_count, 3)
        self.assertEqual(segunda, "zona-a/index.html")
        self.assertNotIn("zona-fantasma", segunda)
        self.assertNotIn("zona-fantasma", cob._mem.get(next(
            (k for k in cob._mem if "ls-files" in k), ""
        ), ""))

    def test_cache_disco_corrupta_se_recupera(self):
        """Evita bloquear INICIAR por un JSON de caché truncado tras una caída."""
        cache = cob._fichero_cache(self.root)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text('{"vigencia":', encoding="utf-8")
        self.assertEqual(cob._leer_disco(self.root, "vigente"), {})

    def test_cache_disco_de_otra_revision_se_descarta(self):
        """Evita reutilizar resultados de una revisión anterior del repositorio."""
        cache = cob._fichero_cache(self.root)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({
            "vigencia": "revision-antigua",
            "datos": {"ls-files": "obsoleto"},
        }), encoding="utf-8")
        self.assertEqual(cob._leer_disco(self.root, "revision-nueva"), {})

    def test_cache_disco_escritura_fallida_no_deja_resultado_valido(self):
        """Evita publicar una caché incompleta cuando falla el disco."""
        with patch.object(cob.os, "replace", side_effect=OSError("disco lleno")):
            cob._guardar_disco(self.root, "revision")
        self.assertFalse(cob._fichero_cache(self.root).exists())

    def test_cache_olvidar_git_fuerza_nueva_lectura(self):
        """Evita conservar inventarios obsoletos después de un cambio de HEAD."""
        cabeza = subprocess.CompletedProcess(
            [], 0, stdout="abc\nmain\n", stderr=""
        )
        lista = subprocess.CompletedProcess(
            [], 0, stdout="zona-a/index.html\n", stderr=""
        )
        with patch.object(cob, "run", side_effect=[cabeza, lista]) as run:
            self.assertEqual(cob._git(self.root, "ls-files"),
                             "zona-a/index.html")
            self.assertEqual(cob._git(self.root, "ls-files"),
                             "zona-a/index.html")
            self.assertEqual(run.call_count, 2)
        cob.olvidar_git()
        self.assertFalse(cob._mem)
        self.assertFalse(cob._cabezas)

    def test_matriz_primera_construccion_persiste_y_recarga(self):
        """Evita perder el mapa al reiniciar el proceso entre INICIAR y EJECUTAR."""
        self.fichero("zona-a/app.js", "export const x = 1;")
        primera = self.construir(["zona-a/app.js"])
        self.assertIn("zona-a", primera)
        self.assertIn("unitaria", primera["zona-a"]["huecos"])
        self.assertEqual(primera["zona-a"]["riesgo"], 5)

        segunda = self.construir(
            ["zona-a/app.js"], head="abc123"
        )
        self.assertEqual(primera, segunda)
        self.assertEqual(
            self.c.execute("SELECT COUNT(*) FROM cobertura").fetchone()[0], 1
        )

    def test_matriz_reconstruye_al_cambiar_head(self):
        """Evita mantener huecos de una revisión anterior tras un despliegue."""
        self.fichero("zona-a/app.js")
        primera = self.construir(["zona-a/app.js"], head="viejo")
        self.fichero("zona-b/index.html")
        segunda = self.construir(
            ["zona-a/app.js", "zona-b/index.html"], head="nuevo"
        )
        self.assertEqual(set(primera), {"zona-a"})
        self.assertEqual(set(segunda), {"zona-a", "zona-b"})
        self.assertEqual(
            {r[0] for r in self.c.execute("SELECT DISTINCT head FROM cobertura")},
            {"nuevo"}
        )

    def test_matriz_forzar_detecta_tests_nuevos_sin_cambiar_head(self):
        """Evita ignorar tests recién creados durante una ejecución del pipeline."""
        self.fichero("zona-a/app.js")
        antes = self.construir(["zona-a/app.js"])
        self.assertIn("unitaria", antes["zona-a"]["huecos"])

        self.fichero(
            "tests/test_zona_a.py",
            "import unittest\n# zona-a/app.js\nassert True\n"
        )
        despues = self.construir(
            ["zona-a/app.js"], ["tests/test_zona_a.py"], forzar=True
        )
        self.assertNotIn("unitaria", despues["zona-a"]["huecos"])
        self.assertIn("unitaria", despues["zona-a"]["tecnicas_cubiertas"])

    def test_matriz_fichero_test_desaparecido_no_bloquea(self):
        """Evita detener el inventario por tests borrados entre ls-files y lectura."""
        self.fichero("zona-a/app.js")
        resultado = self.construir(
            ["zona-a/app.js"], ["tests/test_ya_borrado.py"], forzar=True
        )
        self.assertEqual(resultado["zona-a"]["tests_propios"], 0)
        self.assertIn("unitaria", resultado["zona-a"]["huecos"])

    def test_matriz_no_duplica_familias_en_recalculos(self):
        """Evita crecimiento indefinido de SQLite tras muchas rondas de análisis."""
        archivos = [f"zona-a/modulo_{i}.js" for i in range(30)]
        for ruta in archivos:
            self.fichero(ruta)
        for i in range(20):
            self.construir(
                archivos, head=f"revision-{i}", forzar=True
            )
        self.assertEqual(
            self.c.execute("SELECT COUNT(*) FROM cobertura").fetchone()[0], 1
        )

    def test_matriz_no_considera_global_un_test_sin_referencia(self):
        """Evita declarar cubiertas técnicas por tests ajenos a una familia."""
        self.fichero("zona-a/app.js")
        self.fichero(
            "tests/test_otra.py",
            "import unittest\nassert True\n"
        )
        resultado = self.construir(
            ["zona-a/app.js"], ["tests/test_otra.py"], forzar=True
        )
        self.assertIn("unitaria", resultado["zona-a"]["huecos"])
        self.assertEqual(resultado["zona-a"]["tests_propios"], 0)

    def test_matriz_cobertura_global_es_parcial(self):
        """Evita equiparar una prueba global con cobertura específica de una zona."""
        self.fichero("zona-a/app.js")
        self.fichero(
            "qa/test_global.py",
            "import unittest\n# os.walk para inspeccionar todo el sitio\n"
        )
        resultado = self.construir(
            ["zona-a/app.js"], ["qa/test_global.py"], forzar=True
        )
        self.assertIn("unitaria", resultado["zona-a"]["tecnicas_parcial"])
        self.assertNotIn("unitaria", resultado["zona-a"]["huecos"])
        self.assertEqual(resultado["zona-a"]["tests_propios"], 0)

    # BUG: Una fila de cobertura con JSON truncado provoca JSONDecodeError
    # al reutilizar la matriz y detiene INICIAR tras una escritura corrupta.
    # Arreglo mínimo: si falla json.loads, invalidar la caché y reconstruir.
    def test_matriz_json_corrupto_no_impide_reconstruir(self):
        """Evita que una fila de cobertura truncada bloquee todas las rondas."""
        self.fichero("zona-a/app.js")
        self.construir(["zona-a/app.js"], head="abc123")
        self.c.execute(
            "UPDATE cobertura SET datos=? WHERE familia=?",
            ('{"huecos":', "zona-a")
        )
        self.c.commit()

        resultado = self.construir(
            ["zona-a/app.js"], head="abc123"
        )
        self.assertIn("unitaria", resultado["zona-a"]["huecos"])

    # BUG: construir acepta una sola fila con el HEAD actual y devuelve
    # también filas de revisiones anteriores, contaminando el mapa de huecos.
    # Arreglo mínimo: reutilizar la matriz solo si todos los HEAD coinciden;
    # en caso contrario, reconstruirla y sustituir las filas antiguas.
    def test_matriz_no_reutiliza_filas_de_heads_distintos(self):
        """Evita mezclar cobertura antigua y nueva tras una actualización parcial."""
        self.fichero("zona-a/app.js")
        self.fichero("zona-b/index.html")
        self.construir(
            ["zona-a/app.js", "zona-b/index.html"], head="viejo"
        )
        self.c.execute(
            "UPDATE cobertura SET head='nuevo' WHERE familia='zona-a'"
        )
        self.c.commit()

        resultado = self.construir(
            ["zona-a/app.js"], head="nuevo"
        )
        self.assertEqual(set(resultado), {"zona-a"})
        self.assertEqual(
            {r[0] for r in self.c.execute("SELECT DISTINCT head FROM cobertura")},
            {"nuevo"}
        )

    # BUG: una salida no numérica de git rev-list provoca ValueError y
    # detiene el planificador, aunque el contador solo sea una métrica.
    # Arreglo mínimo: convertir con try/except (ValueError, TypeError)
    # y utilizar cero cuando el contador no sea válido.
    def test_matriz_rev_list_corrupto_no_rompe_planificador(self):
        """Evita detener la generación si git devuelve un contador inválido."""
        self.fichero("zona-a/app.js")
        resultado = self.construir(
            ["zona-a/app.js"], commits="fatal: bad revision"
        )
        self.assertEqual(resultado["zona-a"]["commits14d"], 0)

    def test_matriz_rendimiento_miles_de_archivos(self):
        """Evita que el cálculo crezca desproporcionadamente con miles de rutas."""
        archivos = [
            f"zona-a/seccion_{i // 100}/pagina_{i}.html"
            for i in range(3000)
        ]
        for ruta in archivos:
            self.fichero(ruta)
        inicio = time.monotonic()
        resultado = self.construir(archivos, forzar=True)
        duracion = time.monotonic() - inicio
        self.assertEqual(resultado["zona-a"]["ficheros"], 3000)
        self.assertLess(duracion, 10)

    def test_tecnica_descubierta_sobrevive_a_resiembra(self):
        """Evita perder técnicas propuestas por GPT al reiniciar INICIAR."""
        nueva = {
            "id": "recuperacion-caidas",
            "nombre": "Recuperacion de caidas",
            "palabras_clave": ["recuperacion", "caidas"],
            "aplica": ["generador"],
        }
        self.assertTrue(cob.registrar_tecnica(
            self.c, nueva, q.now(), propuesta=17
        ))
        cob.sembrar_tecnicas(self.c, self.cfg, q.now())
        registros = [
            t for t in cob.tecnicas(self.c)
            if t["id"] == "recuperacion-caidas"
        ]
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]["origen"], "descubierta")

    def test_tecnica_repetida_no_duplica_registros(self):
        """Evita crecimiento de la BD cuando GPT propone la misma técnica varias veces."""
        tecnica = {
            "id": "reintentos-acotados",
            "nombre": "Reintentos acotados",
            "palabras_clave": ["reintentos"],
        }
        self.assertTrue(cob.registrar_tecnica(self.c, tecnica, q.now()))
        for _ in range(20):
            self.assertFalse(cob.registrar_tecnica(
                self.c, tecnica, q.now()
            ))
        self.assertEqual(
            self.c.execute(
                "SELECT COUNT(*) FROM tecnicas WHERE id='reintentos-acotados'"
            ).fetchone()[0], 1
        )

    # BUG: tecnicas() deserializa todas las filas sin aislar errores;
    # una sola técnica con JSON corrupto impide leer las demás y
    # bloquea la selección de huecos del planificador.
    # Arreglo mínimo: omitir filas con JSON inválido y conservar las válidas.
    def test_tecnicas_json_corrupto_no_bloquea_lectura(self):
        """Evita bloquear el planificador por una técnica parcialmente guardada."""
        self.c.execute(
            "UPDATE tecnicas SET kw=? WHERE id=?",
            ('["assert",', "unitaria")
        )
        self.c.commit()

        resultado = cob.tecnicas(self.c)
        self.assertTrue(all(t["id"] != "unitaria" for t in resultado))
        self.assertTrue(any(t["id"] == "integracion" for t in resultado))

    def test_sha_fuentes_no_invoca_git_sin_rutas_existentes(self):
        """Evita lanzar git innecesariamente con propuestas sin fuentes válidas."""
        with patch.object(cob, "_git") as git:
            resultado = cob.sha_fuentes(
                self.root, ["no-existe.js", "", "borrado.py"]
            )
        self.assertEqual(resultado, "")
        git.assert_not_called()

    def test_deduplicacion_no_reabre_rechazada_sin_cambio_fuente(self):
        """Evita regenerar indefinidamente propuestas ya rechazadas."""
        self.fichero("zona-a/app.js", "export const x = 1;")
        propuesta = {
            "titulo": "Comprobar recuperacion tras caida",
            "funcionalidad": "Recuperacion de trabajos tras caida",
            "invariante": "El trabajo pendiente se recupera",
            "tecnica": {"id": "regresion"},
            "ficheros_fuente": [{"ruta": "zona-a/app.js"}],
        }
        datos = cob.datos_prop(propuesta)
        self.c.execute(
            """INSERT INTO propuestas
               (huella,area,titulo,datos,estado,creado,actualizado,
                huella_conductual,fuente_sha)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                "dedup-1", "zona-a", propuesta["titulo"],
                json.dumps(propuesta), "rechazada", q.now(), q.now(),
                datos["huella"], "sha-original"
            )
        )
        self.c.commit()
        with patch.object(cob, "sha_fuentes", return_value="sha-original"):
            fila, motivo = cob.buscar_duplicado(
                self.c, self.root, propuesta
            )
        self.assertIsNotNone(fila)
        self.assertIn("huella igual", motivo)

    def test_deduplicacion_reabre_rechazada_si_cambio_fuente(self):
        """Evita bloquear nuevas pruebas tras corregir el código fuente."""
        self.fichero("zona-a/app.js", "export const version = 2;")
        propuesta = {
            "titulo": "Comprobar reanudacion de jobs",
            "funcionalidad": "Reanudacion de jobs pendientes",
            "invariante": "El job vuelve a ejecutarse",
            "tecnica": {"id": "regresion"},
            "ficheros_fuente": [{"ruta": "zona-a/app.js"}],
        }
        huella = cob.datos_prop(propuesta)["huella"]
        self.c.execute(
            """INSERT INTO propuestas
               (huella,area,titulo,datos,estado,creado,actualizado,
                huella_conductual,fuente_sha)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                "dedup-2", "zona-a", propuesta["titulo"],
                json.dumps(propuesta), "rechazada", q.now(), q.now(),
                huella, "sha-anterior"
            )
        )
        self.c.commit()
        with patch.object(cob, "sha_fuentes", return_value="sha-nuevo"):
            fila, motivo = cob.buscar_duplicado(
                self.c, self.root, propuesta
            )
        self.assertIsNone(fila)
        self.assertIsNone(motivo)

    # BUG: buscar_duplicado ejecuta json.loads sobre propuestas históricas
    # sin manejar JSONDecodeError; una fila truncada detiene la deduplicación
    # y puede bloquear todas las nuevas propuestas de INICIAR.
    # Arreglo mínimo: omitir filas corruptas y continuar la búsqueda.
    def test_deduplicacion_fila_json_corrupta_no_bloquea(self):
        """Evita paralizar la generación por una propuesta histórica truncada."""
        self.c.execute(
            """INSERT INTO propuestas
               (huella,area,titulo,datos,estado,creado,actualizado,
                huella_conductual)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                "corrupta-1", "zona-a", "Histórica",
                '{"ficheros_fuente":', "rechazada",
                q.now(), q.now(), "huella-antigua"
            )
        )
        self.c.commit()
        propuesta = {
            "titulo": "Nueva prueba de integracion",
            "funcionalidad": "Validar integración entre generadores",
            "tecnica": {"id": "integracion"},
            "ficheros_fuente": [{"ruta": "zona-a/app.js"}],
        }

        fila, motivo = cob.buscar_duplicado(
            self.c, self.root, propuesta
        )
        self.assertIsNone(fila)
        self.assertIsNone(motivo)

    def test_deduplicacion_rendimiento_miles_de_propuestas(self):
        """Evita que la búsqueda conductual se dispare con miles de propuestas."""
        filas = [
            (
                f"huella-{i}", "zona-a", f"Prueba {i}",
                json.dumps({
                    "titulo": f"Verificar comportamiento {i}",
                    "funcionalidad": f"Comportamiento independiente {i}",
                    "tecnica": {"id": "unitaria"},
                    "ficheros_fuente": [
                        {"ruta": f"zona-a/modulo_{i}.js"}
                    ],
                }),
                "aceptada", q.now(), q.now(), f"hash-{i}"
            )
            for i in range(3000)
        ]
        self.c.executemany(
            """INSERT INTO propuestas
               (huella,area,titulo,datos,estado,creado,actualizado,
                huella_conductual)
               VALUES(?,?,?,?,?,?,?,?)""",
            filas
        )
        self.c.commit()
        nueva = {
            "titulo": "Recuperacion de trabajos interrumpidos",
            "funcionalidad": "Recuperacion de trabajos interrumpidos",
            "invariante": "No se pierde el estado persistente",
            "tecnica": {"id": "regresion"},
            "ficheros_fuente": [
                {"ruta": "zona-a/recuperacion.py"}
            ],
        }
        inicio = time.monotonic()
        fila, motivo = cob.buscar_duplicado(self.c, self.root, nueva)
        self.assertIsNone(fila)
        self.assertIsNone(motivo)
        self.assertLess(time.monotonic() - inicio, 5)


if __name__ == "__main__":
    unittest.main()
