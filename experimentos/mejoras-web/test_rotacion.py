#!/usr/bin/env python3
"""Pruebas sin red del selector de propuestas. Ejecutar: python -m unittest discover -s experimentos/mejoras-web -p 'test_*.py' -v"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MOD = Path(__file__).with_name("rotacion.py")
spec = importlib.util.spec_from_file_location("selector_mejoras", MOD)
rot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rot)


def item(id, canal, prioridad="P1", familia=None):
    return {
        "id": id, "titulo": "Investigar " + id, "familia": familia or id.split("-")[0],
        "canal": canal, "prioridad": prioridad, "estado": "candidata",
        "hipotesis": "Hipótesis verificable en la web " + id,
        "antiduplicacion": "Comprobar el código existente y las PR anteriores",
        "criterio_medicion": "Métrica real antes y después: " + id,
    }


def datos():
    return {"schema_version": 1, "ideas": [
        item("A-01", "auditoria_local"),
        item("B-01", "github"),
        item("C-01", "web"),
        item("D-01", "api"),
        item("E-01", "sector"),
        item("A-02", "auditoria_local"),
        item("B-02", "github"),
    ]}


def vacio():
    return {"schema": 1, "pendiente": None, "historial": []}


class RotacionPruebas(unittest.TestCase):
    def test_01_cinco_canales_consecutivos_antes_de_repetir(self):
        d, st = datos(), vacio()
        observados = []
        for _ in range(5):
            elegido = rot.seleccionar(d, st)
            observados.append(elegido["canal"])
            st["historial"].append({k: elegido[k] for k in ("id", "canal", "familia")})
        self.assertEqual(observados, list(rot.ORDEN_CANALES))

    def test_02_no_repite_expedientes_cerrados(self):
        d, st = datos(), vacio()
        seleccionados = []
        for _ in d["ideas"]:
            x = rot.seleccionar(d, st)
            seleccionados.append(x["id"])
            st["historial"].append({k: x[k] for k in ("id", "canal", "familia")})
        self.assertEqual(len(seleccionados), len(set(seleccionados)))
        self.assertIsNone(rot.seleccionar(d, st))

    def test_03_prioridad_dentro_de_familia(self):
        d = {"schema_version": 1, "ideas": [
            item("A-01", "web", "P3"), item("A-02", "web", "P1")]}
        self.assertEqual(rot.seleccionar(d, vacio())["id"], "A-02")

    def test_04_filtro_canal(self):
        self.assertEqual(rot.seleccionar(datos(), vacio(), canal="api")["id"], "D-01")

    def test_05_filtro_familia(self):
        self.assertEqual(rot.seleccionar(datos(), vacio(), familia="E")["id"], "E-01")

    def test_06_eleccion_manual(self):
        self.assertEqual(rot.seleccionar(datos(), vacio(), elegir="B-02")["id"], "B-02")

    def test_07_reserva_idempotente(self):
        st = vacio()
        st["pendiente"] = rot.tarea(item("D-01", "api"))
        self.assertEqual(rot.seleccionar(datos(), st)["id"], "D-01")
        with self.assertRaises(ValueError):
            rot.seleccionar(datos(), st, elegir="A-01")

    def test_08_no_reabre_sin_autorizacion(self):
        st = vacio()
        st["historial"].append({"id": "B-01", "canal": "github", "familia": "B"})
        with self.assertRaises(ValueError):
            rot.seleccionar(datos(), st, elegir="B-01")

    def test_09_guardar_cargar_igual(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "estado.json"
            st = vacio()
            st["pendiente"] = rot.tarea(item("C-01", "web"))
            rot.guardar(path, st)
            self.assertEqual(rot.estado(path), st)

    def test_10_cli_inicio_recuperacion_cierre_y_vista(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogo = root / "catalogo.json"
            estado = root / "estado.json"
            catalogo.write_text(json.dumps(datos()), encoding="utf-8")
            def cli(*args):
                run = subprocess.run(
                    [sys.executable, str(MOD), "--catalogo", str(catalogo),
                     "--estado-archivo", str(estado), *args],
                    capture_output=True, text=True, timeout=8)
                self.assertEqual(run.returncode, 0, run.stderr)
                return json.loads(run.stdout)
            self.assertFalse(estado.exists())
            anterior = cli("--vista")["tarea"]["id"]
            self.assertFalse(estado.exists(), "Vista no debe escribir estado")
            self.assertEqual(cli("--siguiente")["tarea"]["id"], anterior)
            self.assertTrue(estado.exists())
            self.assertTrue(cli("--siguiente")["recuperada"])
            self.assertEqual(cli("--resultado", "sin_evidencia")["cerrada"], anterior)
            self.assertNotEqual(cli("--siguiente")["tarea"]["id"], anterior)
            self.assertEqual(cli("--ver-estado")["cerradas"], 1)

    def test_11_archivo_invalido_se_rechaza_sin_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "estado.json"
            path.write_text('{"schema":99,"historial":[],"pendiente":null}', encoding="utf-8")
            with self.assertRaises(ValueError):
                rot.estado(path)
            self.assertIn('"schema":99', path.read_text(encoding="utf-8"))

    def test_12_catalogo_real_tiene_variedad_y_campos(self):
        c = rot.catalogo()
        self.assertGreaterEqual(len(c["ideas"]), 50)
        self.assertGreaterEqual(len({a["familia"] for a in c["ideas"]}), 20)
        self.assertEqual({x["canal"] for x in c["ideas"]}, set(rot.ORDEN_CANALES))
        for x in c["ideas"]:
            self.assertTrue(x["antiduplicacion"])
            self.assertTrue(x["criterio_medicion"])


if __name__ == "__main__":
    unittest.main()
