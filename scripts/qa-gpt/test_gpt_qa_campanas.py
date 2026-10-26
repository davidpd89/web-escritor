import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

"""Regresiones aisladas de qa_campanas: plantillas, cuotas, persistencia y seguridad."""

import json
import re
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

import qa_campanas as camp
import qa_gpt as q
import qa_triaje


class CampanasBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / "state"
        self.state.mkdir()

        for attr, value in (
            ("ROOT", self.root),
            ("STATE", self.state),
            ("DB_PATH", self.state / "estado.db"),
            ("WT", self.state / "wt"),
        ):
            if hasattr(q, attr):
                old = getattr(q, attr)
                setattr(q, attr, value)
                self.addCleanup(setattr, q, attr, old)

        if hasattr(q, "Lock") and hasattr(q.Lock, "path"):
            old = q.Lock.path
            q.Lock.path = self.state / "lock"
            self.addCleanup(setattr, q.Lock, "path", old)

        self.c = sqlite3.connect(":memory:")
        self.c.row_factory = sqlite3.Row
        self.addCleanup(self.c.close)

        qa_triaje.migrar(self.c)
        self.c.executescript("""
            CREATE TABLE propuestas (
                id INTEGER PRIMARY KEY,
                huella TEXT UNIQUE,
                area TEXT,
                titulo TEXT,
                datos TEXT,
                estado TEXT,
                creado TEXT,
                actualizado TEXT,
                tecnica TEXT,
                funcionalidad TEXT
            );

            CREATE TABLE hallazgos (
                clave TEXT PRIMARY KEY,
                tipo TEXT,
                contrato TEXT,
                causa TEXT,
                familia TEXT,
                paginas INTEGER,
                urls TEXT,
                ejemplos TEXT,
                estado TEXT,
                nota TEXT,
                evidencia TEXT
            );
        """)

        self.logs = []

    def hallazgo(
        self,
        clave="h1",
        contrato="seo-description",
        familia="libros",
        urls=None,
        estado="a_triar",
        causa="Defecto reproducible",
        paginas=None,
    ):
        if urls is None:
            urls = ["/libros/"]

        if paginas is None:
            paginas = len(urls)

        self.c.execute(
            """
            INSERT INTO hallazgos
            (clave,tipo,contrato,causa,familia,paginas,urls,
             ejemplos,estado,nota,evidencia)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                clave,
                "estatico",
                contrato,
                causa,
                familia,
                paginas,
                json.dumps(urls),
                "Ejemplo reproducible",
                estado,
                None,
                "Evidencia local",
            ),
        )
        self.c.commit()

    def sembrar(self):
        return camp.sembrar(q, self.c, out=self.logs.append)

    def propuestas(self):
        return self.c.execute(
            "SELECT * FROM propuestas ORDER BY id"
        ).fetchall()

    def datos(self, index=0):
        return json.loads(self.propuestas()[index]["datos"])

    def estado(self, clave="h1"):
        return self.c.execute(
            "SELECT estado FROM hallazgos WHERE clave=?",
            (clave,),
        ).fetchone()[0]

    def plantilla(self, contrato, urls=None, familia="libros"):
        if urls is None:
            urls = ["/libros/"]

        return camp.PLANTILLAS[contrato](
            {"familia": familia},
            urls,
        )

    def ejecutar_plantilla(self, contrato, archivos, urls=None):
        """Ejecuta una plantilla Python sin red ni procesos externos."""
        if urls is None:
            urls = ["/libros/"]

        ruta, contenido, _ = self.plantilla(contrato, urls)
        self.assertTrue(ruta.endswith(".py"))

        repo = self.root / "repo"
        repo.mkdir(exist_ok=True)

        for rel, texto in archivos.items():
            destino = repo / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(texto, encoding="utf-8")

        script = repo / ruta
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text(contenido, encoding="utf-8")

        with patch("subprocess.run") as mocked:
            # No se permite ejecutar procesos externos desde el test.
            # La plantilla se ejecuta en el proceso actual, sustituyendo
            # únicamente __file__ y capturando SystemExit.
            mocked.side_effect = AssertionError(
                "La plantilla no debe lanzar procesos externos"
            )

            namespace = {
                "__name__": "__main__",
                "__file__": str(script),
            }

            try:
                exec(
                    compile(contenido, str(script), "exec"),
                    namespace,
                )
            except SystemExit as exc:
                return exc.code

        return 0


class TestSiembraCampanas(CampanasBase):
    def test_smoke_campana_genera_propuesta_y_triaje(self):
        """Evita que un hallazgo determinista quede sin entrar en corrección."""
        self.hallazgo()

        self.assertEqual(self.sembrar(), 1)
        self.assertEqual(len(self.propuestas()), 1)
        self.assertEqual(self.estado(), "en_campana")

        datos = self.datos()
        self.assertEqual(datos["via"], "campana")
        self.assertEqual(datos["categoria"], "regresion")
        self.assertEqual(len(datos["ficheros_nuevos"]), 1)

        triaje = self.c.execute(
            "SELECT decision,prioridad FROM triaje"
        ).fetchone()

        self.assertEqual(triaje["decision"], "corregir")
        self.assertEqual(triaje["prioridad"], "1")

    def test_reinicio_no_duplica_campana(self):
        """Evita duplicar propuestas y causas al reiniciar INICIAR."""
        self.hallazgo()

        self.assertEqual(self.sembrar(), 1)
        self.assertEqual(self.sembrar(), 0)

        self.assertEqual(len(self.propuestas()), 1)
        self.assertEqual(
            self.c.execute("SELECT COUNT(*) FROM triaje").fetchone()[0],
            1,
        )

    def test_hallazgo_sin_plantilla_permanece_pendiente(self):
        """Evita marcar como procesado un defecto sin generador disponible."""
        self.hallazgo(contrato="contrato-no-implementado")

        self.assertEqual(self.sembrar(), 0)
        self.assertEqual(self.estado(), "a_triar")
        self.assertFalse(self.propuestas())

    def test_hallazgo_sin_urls_no_genera_prueba_vacia(self):
        """Evita aprobar pruebas que no verifican ninguna página."""
        self.hallazgo(urls=[])

        self.assertEqual(self.sembrar(), 0)
        self.assertEqual(self.estado(), "a_triar")
        self.assertFalse(self.propuestas())

    def test_hallazgo_ya_procesado_no_se_reabre(self):
        """Evita reabrir campañas terminadas durante una recuperación."""
        self.hallazgo(estado="en_campana")

        self.assertEqual(self.sembrar(), 0)
        self.assertFalse(self.propuestas())

    def test_varios_contratos_generan_propuestas_independientes(self):
        """Evita perder defectos distintos al procesar una misma familia."""
        contratos = [
            "seo-description",
            "a11y-imagenes",
            "navegacion-enlaces",
            "datos-jsonld",
            "seo-sitemap",
            "ux-objetivos-tactiles",
        ]

        for i, contrato in enumerate(contratos):
            self.hallazgo(
                clave=f"h{i}",
                contrato=contrato,
                urls=[f"/pagina-{i}/"],
            )

        self.assertEqual(self.sembrar(), len(contratos))
        self.assertEqual(len(self.propuestas()), len(contratos))

        huellas = [p["huella"] for p in self.propuestas()]
        self.assertEqual(len(huellas), len(set(huellas)))

    def test_cuota_maxima_urls_y_deduplicacion(self):
        """Evita campañas excesivas por URLs repetidas o miles de páginas."""
        urls = ["/repetida/"] * 30
        urls += [f"/pagina-{i}/" for i in range(100)]

        self.hallazgo(urls=urls)

        self.assertEqual(self.sembrar(), 1)

        contenido = self.datos()["ficheros_nuevos"][0]["contenido"]
        match = re.search(r"^PAGINAS = (.+)$", contenido, re.M)

        self.assertIsNotNone(match)

        paginas = json.loads(match.group(1))

        self.assertEqual(len(paginas), camp.MAX_URLS)
        self.assertEqual(len(paginas), len(set(paginas)))
        self.assertEqual(paginas[0], "repetida/index.html")

    def test_orden_por_paginas_prioriza_defectos_extensos(self):
        """Evita que defectos de una página desplacen campañas más graves."""
        self.hallazgo(
            clave="pequena",
            paginas=1,
            urls=["/pequena/"],
        )
        self.hallazgo(
            clave="grande",
            paginas=100,
            urls=["/grande/"],
        )

        self.assertEqual(self.sembrar(), 2)

        # El log informa del contrato, la familia y el número de páginas,
        # no de la clave del hallazgo ni de su URL.
        # La prioridad se comprueba por el alcance registrado.
        self.assertIn("100 paginas", self.logs[0])
        self.assertIn("1 paginas", self.logs[1])

        self.assertEqual(len(self.propuestas()), 2)

        primera = self.datos(0)
        segunda = self.datos(1)

        contenido_primera = primera["ficheros_nuevos"][0]["contenido"]
        contenido_segunda = segunda["ficheros_nuevos"][0]["contenido"]

        self.assertIn("grande/index.html", contenido_primera)
        self.assertIn("pequena/index.html", contenido_segunda)

    def test_fallo_guardado_triaje_no_marca_hallazgo_procesado(self):
        """Evita perder un hallazgo cuando falla la persistencia del triaje."""
        self.hallazgo()

        with patch.object(
            qa_triaje,
            "guardar",
            side_effect=sqlite3.OperationalError("disk I/O error"),
        ):
            with self.assertRaises(sqlite3.OperationalError):
                self.sembrar()

        self.assertEqual(self.estado(), "a_triar")

    def test_reanudacion_tras_fallo_transitorio(self):
        """Evita dejar una campaña bloqueada tras recuperar SQLite."""
        self.hallazgo()

        original = qa_triaje.guardar
        llamadas = 0

        def guardar_intermitente(*args, **kwargs):
            nonlocal llamadas
            llamadas += 1

            if llamadas == 1:
                raise sqlite3.OperationalError("database is locked")

            return original(*args, **kwargs)

        with patch.object(
            qa_triaje,
            "guardar",
            side_effect=guardar_intermitente,
        ):
            with self.assertRaises(sqlite3.OperationalError):
                self.sembrar()

            self.assertEqual(self.sembrar(), 1)

        self.assertEqual(self.estado(), "en_campana")
        self.assertEqual(len(self.propuestas()), 1)

    def test_propuesta_contiene_comando_correcto(self):
        """Evita enviar pruebas Python al ejecutor Node o viceversa."""
        for contrato in camp.PLANTILLAS:
            with self.subTest(contrato=contrato):
                self.c.execute("DELETE FROM hallazgos")
                self.c.execute("DELETE FROM propuestas")
                self.c.execute("DELETE FROM triaje")
                self.c.commit()

                self.hallazgo(contrato=contrato)
                self.assertEqual(self.sembrar(), 1)

                datos = self.datos()
                ruta = datos["ficheros_nuevos"][0]["ruta"]

                esperado = (
                    "node " if ruta.endswith(".mjs") else "python "
                ) + ruta

                self.assertEqual(datos["como_ejecutar"], esperado)

    def test_miles_de_hallazgos_sin_plantilla_terminan_rapido(self):
        """Evita degradación extrema al recorrer miles de hallazgos."""
        filas = [
            (
                f"h{i}",
                "estatico",
                "sin-plantilla",
                "causa",
                "familia",
                1,
                '["/pagina/"]',
                "ejemplo",
                "a_triar",
                None,
                "",
            )
            for i in range(3000)
        ]

        self.c.executemany(
            "INSERT INTO hallazgos VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            filas,
        )
        self.c.commit()

        inicio = time.monotonic()
        resultado = self.sembrar()
        duracion = time.monotonic() - inicio

        self.assertEqual(resultado, 0)
        self.assertLess(duracion, 5)
        self.assertFalse(self.propuestas())


class TestPlantillas(CampanasBase):
    def test_todas_las_plantillas_producen_artefactos(self):
        """Evita registrar contratos cuya plantilla no genera una prueba."""
        for contrato in camp.PLANTILLAS:
            with self.subTest(contrato=contrato):
                ruta, contenido, criterio = self.plantilla(contrato)

                self.assertTrue(ruta)
                self.assertTrue(contenido.strip())
                self.assertTrue(criterio.strip())

                self.assertTrue(
                    ruta.startswith(("tests/", "qa/"))
                )
                self.assertTrue(
                    ruta.endswith((".py", ".mjs"))
                )

                if ruta.endswith(".py"):
                    compile(contenido, ruta, "exec")

    def test_rutas_html_home_y_directorios(self):
        """Evita generar rutas inexistentes para la home y directorios."""
        casos = {
            "/": "index.html",
            "/libros/": "libros/index.html",
            "/libros/obra/": "libros/obra/index.html",
            "/archivo.html": "archivo.html",
            "https://example.org/libros/": "libros/index.html",
        }

        for url, esperado in casos.items():
            with self.subTest(url=url):
                self.assertEqual(camp._ruta_html(url), esperado)

    def test_meta_description_acepta_longitud_valida(self):
        """Evita falsos positivos con descripciones dentro del contrato."""
        descripcion = "D" * 100

        html = (
            '<html><head><meta name="description" '
            f'content="{descripcion}"></head></html>'
        )

        self.assertEqual(
            self.ejecutar_plantilla(
                "seo-description",
                {"libros/index.html": html},
            ),
            0,
        )

    def test_meta_description_rechaza_descripcion_corta(self):
        """Evita publicar páginas con descripciones SEO insuficientes."""
        html = (
            '<html><head><meta name="description" '
            'content="Corta"></head></html>'
        )

        self.assertEqual(
            self.ejecutar_plantilla(
                "seo-description",
                {"libros/index.html": html},
            ),
            1,
        )

    def test_meta_description_rechaza_descripcion_larga(self):
        """Evita aceptar descripciones que exceden el máximo establecido."""
        html = (
            '<meta name="description" content="'
            + "D" * 201
            + '">'
        )

        self.assertEqual(
            self.ejecutar_plantilla(
                "seo-description",
                {"libros/index.html": html},
            ),
            1,
        )

    def test_axe_detecta_imagen_sin_alt(self):
        """Evita perder regresiones de accesibilidad en imágenes."""
        html = (
            '<html lang="es"><h1>Libro</h1>'
            '<img src="/portada.jpg"></html>'
        )

        self.assertEqual(
            self.ejecutar_plantilla(
                "a11y-imagenes",
                {"libros/index.html": html},
            ),
            1,
        )

    def test_axe_acepta_imagen_decorativa(self):
        """Evita exigir texto alternativo a imágenes decorativas."""
        html = (
            '<html lang="es"><h1>Libro</h1>'
            '<img src="/adorno.svg" alt=""></html>'
        )

        self.assertEqual(
            self.ejecutar_plantilla(
                "a11y-imagenes",
                {"libros/index.html": html},
            ),
            0,
        )

    def test_enlaces_detecta_destino_inexistente(self):
        """Evita publicar navegación interna hacia páginas inexistentes."""
        html = '<html><a href="/no-existe/">Abrir</a></html>'

        self.assertEqual(
            self.ejecutar_plantilla(
                "navegacion-enlaces",
                {"libros/index.html": html},
            ),
            1,
        )

    def test_enlaces_acepta_destino_local_existente(self):
        """Evita falsos positivos con enlaces internos válidos."""
        html = '<html><a href="/destino/">Abrir</a></html>'

        self.assertEqual(
            self.ejecutar_plantilla(
                "navegacion-enlaces",
                {
                    "libros/index.html": html,
                    "destino/index.html": "<html></html>",
                },
            ),
            0,
        )

    def test_jsonld_rechaza_json_malformado(self):
        """Evita aceptar datos estructurados que los buscadores no parsean."""
        html = (
            '<script type="application/ld+json">'
            '{"@context":'
            "</script>"
        )

        self.assertEqual(
            self.ejecutar_plantilla(
                "datos-jsonld",
                {"libros/index.html": html},
            ),
            1,
        )

    def test_jsonld_acepta_objeto_valido(self):
        """Evita rechazar JSON-LD correctamente formado."""
        html = (
            '<script type="application/ld+json">'
            '{"@context":"https://schema.org","@type":"Book"}'
            "</script>"
        )

        self.assertEqual(
            self.ejecutar_plantilla(
                "datos-jsonld",
                {"libros/index.html": html},
            ),
            0,
        )

    def test_sitemap_detecta_ruta_ausente(self):
        """Evita que páginas publicadas desaparezcan del sitemap."""
        self.assertEqual(
            self.ejecutar_plantilla(
                "seo-sitemap",
                {"sitemap.xml": "<urlset></urlset>"},
            ),
            1,
        )

    def test_sitemap_acepta_ruta_presente(self):
        """Evita falsos positivos cuando la ruta figura en el sitemap."""
        self.assertEqual(
            self.ejecutar_plantilla(
                "seo-sitemap",
                {"sitemap.xml": "<urlset>/libros/</urlset>"},
            ),
            0,
        )

    def test_tactiles_limita_paginas_y_cierra_navegador(self):
        """Evita fugas de Chromium y campañas móviles sin límite."""
        urls = [f"/pagina-{i}/" for i in range(camp.MAX_URLS)]

        ruta, js, criterio = self.plantilla(
            "ux-objetivos-tactiles",
            urls,
        )

        self.assertTrue(ruta.endswith(".mjs"))
        self.assertIn("chromium.launch()", js)
        self.assertIn("browser.close()", js)
        self.assertIn("page.close()", js)
        self.assertIn("timeout: 30000", js)
        self.assertIn("24", criterio)

        match = re.search(r"const URLS = (.+);", js)
        self.assertIsNotNone(match)
        self.assertEqual(len(json.loads(match.group(1))), len(urls))


if __name__ == "__main__":
    unittest.main()
