"""Regresiones aisladas de ci_grupo: validacion, procesos, CI y resultados."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
import os
import subprocess
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import ci_grupo as ci
import qa_clases


class CiGrupoRegresiones(unittest.TestCase):
    def setUp(self):
        """Aisla ficheros, directorio de trabajo y estado global."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

        old_cwd = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, old_cwd)

        old_timeout = ci.TIMEOUT
        old_posix = ci.POSIX
        self.addCleanup(setattr, ci, "TIMEOUT", old_timeout)
        self.addCleanup(setattr, ci, "POSIX", old_posix)

        # Nunca utilizar STATE, DB_PATH, ROOT ni Lock.path reales.
        try:
            import qa_gpt as q
        except ImportError:
            q = None

        if q is not None:
            for name, value in (
                ("STATE", self.root / "estado"),
                ("DB_PATH", self.root / "estado" / "qa.db"),
                ("ROOT", self.root),
            ):
                if hasattr(q, name):
                    old = getattr(q, name)
                    setattr(q, name, value)
                    self.addCleanup(setattr, q, name, old)

            if hasattr(q, "Lock") and hasattr(q.Lock, "path"):
                old = q.Lock.path
                q.Lock.path = self.root / "estado" / "worker.lock"
                self.addCleanup(setattr, q.Lock, "path", old)

        self.salida = self.root / "resultados.json"

    def fichero(self, ruta, contenido="print('OK')\n"):
        p = self.root / ruta
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenido, encoding="utf-8")
        return p

    def ejecutar_main(self, modo, *tests):
        return ci.main(
            ["ci_grupo.py", str(self.salida), modo, *tests]
        )

    def resultado(self):
        return json.loads(self.salida.read_text(encoding="utf-8"))

    def proceso(self, rc=0, salida="OK\n"):
        proc = Mock()
        proc.pid = 12345
        proc.returncode = rc
        proc.communicate.return_value = (salida, None)
        proc.poll.return_value = rc
        proc.wait.return_value = rc
        return proc

    def test_validar_rechaza_traversal_con_directorios_intermedios(self):
        """Impide ejecutar archivos fuera del repositorio mediante rutas relativas."""
        malos = (
            "python:tests/../../secreto.py",
            "python:tests/../secreto.py",
            "node:qa/../../secreto.mjs",
            "python:./../secreto.py",
        )
        for valor in malos:
            with self.subTest(valor=valor):
                self.assertIsNone(ci.validar(valor))

    def test_validar_rechaza_inyeccion_de_argumentos(self):
        """Evita que un test generado introduzca opciones o comandos adicionales."""
        malos = (
            "python:-c.py",
            "node:--eval.js",
            "python:test.py;echo",
            "python:test.py|cat",
            "python:test.py&&echo",
            "python:test.py$(whoami)",
            "python:test.py`whoami`",
            "python:test.py\nnode:otro.js",
        )
        for valor in malos:
            with self.subTest(valor=valor):
                self.assertIsNone(ci.validar(valor))

    def test_validar_rechaza_rutas_windows_absolutas(self):
        """Evita acceder a unidades Windows o rutas UNC fuera del checkout."""
        malos = (
            "python:C:/Windows/test.py",
            r"python:C:\Windows\test.py",
            r"python:\\servidor\share\test.py",
            "node:/tmp/test.mjs",
        )
        for valor in malos:
            with self.subTest(valor=valor):
                self.assertIsNone(ci.validar(valor))

    # BUG: validar comprueba por separado el ejecutor y la extension,
    # pero no verifica que sean compatibles. Acepta python:archivo.mjs
    # y node:archivo.py; correr los envia al interprete equivocado.
    # Esto produce fallos artificiales que el pipeline puede registrar
    # como infraestructura o hallazgos, contaminando los resultados.
    # Arreglo minimo: exigir .py para python y .js/.mjs para node.
    def test_validar_no_acepta_ejecutor_incompatible_con_extension(self):
        """Rechaza combinaciones de interprete y extension incompatibles."""
        casos = (
            "python:qa/prueba.mjs",
            "python:qa/prueba.js",
            "node:tests/prueba.py",
        )
        for valor in casos:
            with self.subTest(valor=valor):
                self.assertIsNone(ci.validar(valor))

    def test_validar_acepta_rutas_normales_anidadas(self):
        """Mantiene ejecutables los tests legitimos de carpetas QA y tests."""
        casos = {
            "python:tests/test_sitemap.py": (
                "python", "tests/test_sitemap.py"
            ),
            "node:qa/browser-test.mjs": (
                "node", "qa/browser-test.mjs"
            ),
            "node:assets/check.js": (
                "node", "assets/check.js"
            ),
        }
        for entrada, esperado in casos.items():
            with self.subTest(entrada=entrada):
                self.assertEqual(ci.validar(entrada), esperado)

    def test_main_preserva_orden_y_resultados_de_grupo_mixto(self):
        """Impide perder o reordenar resultados al combinar Python y Node."""
        self.fichero("tests/a.py")
        self.fichero("qa/b.mjs")
        self.fichero("tests/c.py")

        with patch.object(ci, "correr", side_effect=[
            (0, "OK"),
            (1, "AssertionError: defecto"),
            (0, "OK"),
        ]) as correr:
            rc = self.ejecutar_main(
                "exploratorio",
                "python:tests/a.py",
                "node:qa/b.mjs",
                "python:tests/c.py",
            )

        data = self.resultado()
        self.assertEqual(rc, 0)
        self.assertEqual(
            [r["ruta"] for r in data["tests"]],
            ["tests/a.py", "qa/b.mjs", "tests/c.py"],
        )
        self.assertEqual(
            [r["clase"] for r in data["tests"]],
            ["ok", "hallazgo", "ok"],
        )
        self.assertEqual(correr.call_count, 3)

    def test_main_continua_tras_resultado_infraestructura(self):
        """Evita perder evidencia posterior a un fallo de infraestructura."""
        with patch.object(ci, "correr", side_effect=[
            (124, "TimeoutExpired tras 300s"),
            (0, "OK"),
            (1, "AssertionError: defecto"),
        ]) as correr:
            rc = self.ejecutar_main(
                "exploratorio",
                "python:a.py",
                "python:b.py",
                "python:c.py",
            )

        data = self.resultado()
        self.assertEqual(rc, 1)
        self.assertEqual(correr.call_count, 3)
        self.assertEqual(len(data["tests"]), 3)
        self.assertEqual(data["resumen"]["infra"], 1)
        self.assertEqual(data["resumen"]["ok"], 1)
        self.assertEqual(data["resumen"]["hallazgo"], 1)

    def test_main_conserva_unicode_y_recorta_salida_larga(self):
        """Evita artefactos enormes y perdida de diagnosticos Unicode."""
        salida = "x" * 12000 + "Error: ñá漢字\n"

        with patch.object(ci, "correr", return_value=(1, salida)):
            self.ejecutar_main("exploratorio", "python:fallo.py")

        data = self.resultado()
        registro = data["tests"][0]
        self.assertLessEqual(len(registro["salida"]), 4000)
        self.assertTrue(registro["salida"].endswith("ñá漢字\n"))
        self.assertNotIn("\\u00f1", self.salida.read_text(encoding="utf-8"))

    def test_main_tiempos_no_negativos_y_esquema_estable(self):
        """Impide publicar duraciones negativas o resultados incompletos."""
        with patch.object(ci, "correr", return_value=(0, "OK")):
            with patch.object(ci.time, "time", side_effect=[
                1000.0, 1000.25
            ]):
                rc = self.ejecutar_main("regresion", "python:a.py")

        data = self.resultado()
        self.assertEqual(rc, 0)
        self.assertEqual(set(data), {"modo", "resumen", "tests"})
        self.assertEqual(
            set(data["tests"][0]),
            {"ruta", "exe", "rc", "clase", "segundos", "salida"},
        )
        self.assertEqual(data["tests"][0]["segundos"], 0.2)

    def test_main_miles_de_resultados_sin_crecimiento_cuadratico(self):
        """Evita que el resumen de miles de tests tenga complejidad cuadratica."""
        n = 4000
        entradas = [f"python:tests/t{i}.py" for i in range(n)]

        with patch.object(ci, "correr", return_value=(0, "")):
            inicio = time.monotonic()
            rc = self.ejecutar_main("exploratorio", *entradas)
            duracion = time.monotonic() - inicio

        data = self.resultado()
        self.assertEqual(rc, 0)
        self.assertEqual(data["resumen"], {"ok": n})
        self.assertEqual(len(data["tests"]), n)
        self.assertLess(duracion, 5.0)

    def test_correr_fichero_ausente_no_lanza_subprocess(self):
        """Evita ejecutar interpretes para rutas desaparecidas."""
        with patch.object(ci.subprocess, "Popen") as popen:
            rc, out = ci.correr("python", "tests/inexistente.py")

        self.assertEqual(rc, 127)
        self.assertIn("can't open file", out)
        popen.assert_not_called()

    def test_correr_python_no_arranca_servidor_http(self):
        """Evita procesos auxiliares para pruebas Python."""
        self.fichero(
            "tests/t.py",
            "print('playwright process.env.TEST_BASE_URL')\n",
        )
        proc = self.proceso()

        with patch.object(ci.subprocess, "Popen", return_value=proc) as popen:
            rc, out = ci.correr("python", "tests/t.py")

        self.assertEqual((rc, out), (0, "OK\n"))
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(popen.call_args.args[0][0], sys.executable)

    def test_correr_node_sin_navegador_no_arranca_servidor(self):
        """Evita lanzar HTTP para scripts Node que no lo necesitan."""
        self.fichero("qa/test.mjs", "console.log('OK');\n")
        proc = self.proceso()

        with patch.object(ci.subprocess, "Popen", return_value=proc) as popen:
            rc, out = ci.correr("node", "qa/test.mjs")

        self.assertEqual((rc, out), (0, "OK\n"))
        self.assertEqual(popen.call_count, 1)
        self.assertEqual(popen.call_args.args[0][0], "node")

    def test_correr_node_propaga_url_al_servidor_asignado(self):
        """Evita que Playwright apunte a otro puerto."""
        self.fichero(
            "qa/browser.mjs",
            "const base = process.env.RECOMMENDATIONS_BASE_URL;\n"
            "import { chromium } from 'playwright';\n",
        )

        servidor = self.proceso()
        test = self.proceso()
        procesos = []

        def crear(argv, **kwargs):
            procesos.append((argv, kwargs))
            return servidor if len(procesos) == 1 else test

        with (
            patch.object(ci, "puerto_libre", return_value=4321),
            patch.object(ci, "esperar_puerto", return_value=True),
            patch.object(ci.subprocess, "Popen", side_effect=crear),
        ):
            rc, _ = ci.correr("node", "qa/browser.mjs")

        self.assertEqual(rc, 0)
        self.assertEqual(len(procesos), 2)
        self.assertEqual(
            procesos[1][1]["env"]["RECOMMENDATIONS_BASE_URL"],
            "http://127.0.0.1:4321",
        )
        self.assertEqual(
            procesos[0][0][-3:],
            ["4321", "--bind", "127.0.0.1"],
        )

    def test_correr_sin_puertos_libres_no_lanza_procesos(self):
        """Evita ejecutar navegadores sin servidor disponible."""
        self.fichero("qa/browser.mjs", "import 'playwright';\n")

        with (
            patch.object(ci, "puerto_libre", return_value=None),
            patch.object(ci.subprocess, "Popen") as popen,
        ):
            rc, out = ci.correr("node", "qa/browser.mjs")

        self.assertNotEqual(rc, 0)
        self.assertIn("EADDRINUSE", out)
        popen.assert_not_called()

    def test_correr_servidor_no_arranca_y_se_limpia(self):
        """Evita dejar HTTP huerfano cuando no llega a estar listo."""
        self.fichero("qa/browser.mjs", "import 'playwright';\n")
        servidor = self.proceso()

        with (
            patch.object(ci, "puerto_libre", return_value=4321),
            patch.object(ci, "esperar_puerto", return_value=False),
            patch.object(ci, "matar") as matar,
            patch.object(ci.subprocess, "Popen", return_value=servidor) as popen,
        ):
            rc, out = ci.correr("node", "qa/browser.mjs")

        self.assertNotEqual(rc, 0)
        self.assertIn("ETIMEDOUT", out)
        popen.assert_called_once()
        matar.assert_called_once_with(servidor)

    def test_correr_timeout_mata_test_y_servidor(self):
        """Evita que un timeout deje Chromium y HTTP vivos."""
        self.fichero("qa/browser.mjs", "import 'playwright';\n")
        servidor = self.proceso()
        test = self.proceso()
        test.communicate.side_effect = subprocess.TimeoutExpired(
            ["node", "qa/browser.mjs"], 1
        )
        ci.TIMEOUT = 1

        with (
            patch.object(ci, "puerto_libre", return_value=4321),
            patch.object(ci, "esperar_puerto", return_value=True),
            patch.object(
                ci.subprocess, "Popen", side_effect=[servidor, test]
            ),
            patch.object(ci, "matar") as matar,
        ):
            rc, out = ci.correr("node", "qa/browser.mjs")

        self.assertEqual(rc, 124)
        self.assertIn("TimeoutExpired", out)
        matar.assert_any_call(test)
        matar.assert_any_call(servidor)

    def test_correr_error_al_lanzar_test_limpia_servidor(self):
        """Evita procesos HTTP huerfanos si Node no puede iniciarse."""
        self.fichero("qa/browser.mjs", "import 'playwright';\n")
        servidor = self.proceso()

        with (
            patch.object(ci, "puerto_libre", return_value=4321),
            patch.object(ci, "esperar_puerto", return_value=True),
            patch.object(
                ci.subprocess,
                "Popen",
                side_effect=[
                    servidor,
                    OSError("disco o ejecutor no disponible"),
                ],
            ),
            patch.object(ci, "matar") as matar,
        ):
            with self.assertRaises(OSError):
                ci.correr("node", "qa/browser.mjs")

        matar.assert_called_once_with(servidor)

    def test_matar_windows_termina_arbol_completo(self):
        """Evita dejar hijos de Chromium activos en Windows."""
        ci.POSIX = False
        proc = self.proceso()
        proc.poll.return_value = None

        with patch.object(ci.subprocess, "run") as run:
            ci.matar(proc)

        run.assert_called_once()
        argv = run.call_args.args[0]
        self.assertEqual(
            argv,
            ["taskkill", "/F", "/T", "/PID", "12345"],
        )
        proc.wait.assert_called_once()

    def test_matar_windows_fallback_si_taskkill_falla(self):
        """Evita perder la limpieza cuando taskkill lanza OSError."""
        ci.POSIX = False
        proc = self.proceso()
        proc.poll.return_value = None

        with patch.object(
            ci.subprocess,
            "run",
            side_effect=OSError("taskkill no disponible"),
        ):
            ci.matar(proc)

        proc.kill.assert_called_once()
        proc.wait.assert_called_once()

    def test_matar_proceso_ya_terminado_no_invoca_taskkill(self):
        """Evita matar un PID reutilizado."""
        ci.POSIX = False
        proc = self.proceso()
        proc.poll.return_value = 0

        with patch.object(ci.subprocess, "run") as run:
            ci.matar(proc)

        run.assert_not_called()
        proc.kill.assert_not_called()
        proc.wait.assert_called_once()

    def test_esperar_puerto_acota_intentos(self):
        """Evita esperas infinitas si HTTP nunca abre el puerto."""
        reloj = iter([0.0, 0.0, 0.5, 1.0, 1.5])
        sock = Mock()
        sock.__enter__ = Mock(return_value=sock)
        sock.__exit__ = Mock(return_value=False)
        sock.connect_ex.return_value = 111

        with (
            patch.object(
                ci.time, "time", side_effect=lambda: next(reloj)
            ),
            patch.object(ci.time, "sleep") as dormir,
            patch.object(ci.socket, "socket", return_value=sock),
        ):
            disponible = ci.esperar_puerto(4321, segundos=1)

        self.assertFalse(disponible)
        self.assertLessEqual(dormir.call_count, 3)

    def test_puerto_libre_no_sale_del_rango_reservado(self):
        """Evita barridos ilimitados de puertos ocupados."""
        sock = Mock()
        sock.__enter__ = Mock(return_value=sock)
        sock.__exit__ = Mock(return_value=False)
        sock.connect_ex.return_value = 0

        with patch.object(ci.socket, "socket", return_value=sock):
            puerto = ci.puerto_libre(base=4500)

        self.assertIsNone(puerto)
        self.assertEqual(sock.connect_ex.call_count, 40)

    def test_entorno_url_deduplica_variables_repetidas(self):
        """Evita configuraciones inconsistentes al reutilizar variables."""
        texto = (
            "process.env.READING_BASE_URL;\n"
            "process.env.READING_BASE_URL;\n"
            "process.env.SITE_ORIGIN;\n"
            "process.env.API_BASE;\n"
        )
        env = ci.entorno_url(texto, 4321)

        self.assertEqual(env, {
            "READING_BASE_URL": "http://127.0.0.1:4321",
            "SITE_ORIGIN": "http://127.0.0.1:4321",
            "API_BASE": "http://127.0.0.1:4321",
        })

    # BUG: main no captura las excepciones OSError de correr.
    # Si falla Popen, la lectura del script o el sistema de archivos,
    # se interrumpe el grupo sin generar resultados.json.
    # Esto impide distinguir una incidencia de infraestructura de
    # un fallo del producto y pierde los resultados posteriores.
    # Arreglo minimo: capturar OSError por test, generar un registro
    # de infraestructura y continuar con los siguientes elementos.
    def test_error_os_al_lanzar_test_conserva_resultados(self):
        """Evita perder el artefacto por un error de disco o ejecutor."""
        with patch.object(
            ci,
            "correr",
            side_effect=[
                OSError("disco no disponible"),
                (0, "OK"),
            ],
        ):
            rc = self.ejecutar_main(
                "exploratorio",
                "python:a.py",
                "python:b.py",
            )

        self.assertEqual(rc, 1)
        data = self.resultado()
        self.assertEqual(len(data["tests"]), 2)
        self.assertEqual(data["tests"][0]["clase"], "infra")
        self.assertEqual(data["tests"][1]["clase"], "ok")


    # BUG: correr inicia el servidor HTTP y llama a esperar_puerto
    # antes de entrar en el try/finally que termina srv.
    # Si esperar_puerto lanza OSError, el servidor queda vivo.
    # En Windows puede mantener ocupado el puerto y afectar a
    # grupos posteriores, especialmente en un runner persistente.
    # Arreglo minimo: incluir la creacion y espera del servidor
    # dentro del try/finally que garantiza matar(srv).
    def test_excepcion_en_espera_de_puerto_limpia_servidor(self):
        """Evita servidores huerfanos ante errores de socket."""
        self.fichero("qa/browser.mjs", "import 'playwright';\n")
        servidor = self.proceso()

        with (
            patch.object(ci, "puerto_libre", return_value=4321),
            patch.object(
                ci,
                "esperar_puerto",
                side_effect=OSError("socket no disponible"),
            ),
            patch.object(ci.subprocess, "Popen", return_value=servidor),
            patch.object(ci, "matar") as matar,
        ):
            with self.assertRaises(OSError):
                ci.correr("node", "qa/browser.mjs")

        matar.assert_called_once_with(servidor)

    def test_colision_de_puerto_devuelve_error_y_limpia_servidor(self):
        """Respeta el contrato: fallo de arranque, sin ejecutar el test."""
        self.fichero("qa/browser.mjs", "import 'playwright';\n")
        servidor = self.proceso()

        # No se exige reintento: ci_grupo no promete recuperar
        # automaticamente una colision. El contrato actual exige
        # devolver error, no ejecutar el test y limpiar el servidor.
        # esperar_puerto=False tambien puede indicar un fallo distinto
        # de EADDRINUSE, por lo que reintentar no siempre seria correcto.
        with (
            patch.object(
                ci, "puerto_libre", return_value=4321
            ) as puertos,
            patch.object(
                ci, "esperar_puerto", return_value=False
            ) as esperar,
            patch.object(
                ci.subprocess, "Popen", return_value=servidor
            ) as popen,
            patch.object(ci, "matar") as matar,
        ):
            rc, out = ci.correr("node", "qa/browser.mjs")

        self.assertEqual(rc, 1)
        self.assertIn("ETIMEDOUT", out)
        puertos.assert_called_once_with()
        esperar.assert_called_once_with(4321)
        popen.assert_called_once()
        matar.assert_called_once_with(servidor)

    def test_main_conserva_ejecuciones_repetidas_y_su_orden(self):
        """Verifica que main procesa cada entrada recibida."""
        # El contrato de main no establece deduplicacion.
        # Repetir una ruta puede ser deliberado para detectar
        # inestabilidad o fallos intermitentes.
        # No corresponde imponer una politica de deduplicacion
        # desde este test ni clasificar su ausencia como bug.
        with patch.object(
            ci, "correr", return_value=(0, "OK")
        ) as correr:
            rc = self.ejecutar_main(
                "exploratorio",
                "python:tests/a.py",
                "python:tests/a.py",
                "node:qa/b.mjs",
                "python:tests/a.py",
            )

        self.assertEqual(rc, 0)
        self.assertEqual(correr.call_count, 4)
        self.assertEqual(
            correr.call_args_list,
            [
                unittest.mock.call("python", "tests/a.py"),
                unittest.mock.call("python", "tests/a.py"),
                unittest.mock.call("node", "qa/b.mjs"),
                unittest.mock.call("python", "tests/a.py"),
            ],
        )
        self.assertEqual(
            [r["ruta"] for r in self.resultado()["tests"]],
            [
                "tests/a.py",
                "tests/a.py",
                "qa/b.mjs",
                "tests/a.py",
            ],
        )

    # BUG: matar usa subprocess.run(taskkill) sin check=True
    # y sin comprobar returncode. Si taskkill devuelve un codigo
    # distinto de cero, no se ejecuta proc.kill como respaldo.
    # Despues espera hasta 10 segundos, ignora TimeoutExpired
    # y puede dejar procesos vivos en el runner de Windows.
    # Arreglo minimo: comprobar el codigo de taskkill y, si falla,
    # llamar a proc.kill; verificar despues la terminacion.
    def test_taskkill_fallido_no_deja_proceso_vivo(self):
        """Evita procesos huerfanos si taskkill devuelve error."""
        ci.POSIX = False
        proc = self.proceso()
        proc.poll.return_value = None

        fallo = subprocess.CompletedProcess(
            ["taskkill"],
            1,
            stdout=b"",
            stderr=b"Access denied",
        )

        with patch.object(ci.subprocess, "run", return_value=fallo):
            ci.matar(proc)

        proc.kill.assert_called_once()

    def test_ejecucion_silenciosa_exit_cero_respeta_contrato(self):
        """Acepta tests validos que no emiten stdout."""
        self.fichero(
            "tests/silencioso.py",
            "assert 2 + 2 == 4\n",
        )
        proc = self.proceso(rc=0, salida="")

        with patch.object(ci.subprocess, "Popen", return_value=proc):
            rc, out = ci.correr(
                "python", "tests/silencioso.py"
            )

        self.assertEqual((rc, out), (0, ""))
        self.assertEqual(
            qa_clases.clasificar_salida(rc, out),
            "ok",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
