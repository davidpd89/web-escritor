import sqlite3, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import qa_contratos, qa_viaa


class Q:
    @staticmethod
    def now(): return "2026-10-23T00:00:00"


def conexion():
    c = sqlite3.connect(":memory:"); c.row_factory = sqlite3.Row; qa_viaa.migrar(c); return c


G = {"contrato": "seo-title", "causa": "x", "familia": "libros", "paginas": 3, "urls": ["/a/", "/b/", "/c/"], "ejemplos": ["/a/ 1"]}
RES = {"paginas": 10, "contratos": 15, "aserciones": 150, "fallos_brutos": 3, "fallos_unicos": 1, "segundos": 0.1, "familias": {"libros": 10}}


class Hallazgos(unittest.TestCase):
    def test_un_grupo_con_todas_las_paginas(self):
        c = conexion(); qa_viaa.registrar(c, Q, "estatico", RES, [G], "abc12345", "cmd")
        r = c.execute("SELECT * FROM hallazgos").fetchall()
        self.assertEqual(len(r), 1); self.assertEqual(r[0]["paginas"], 3); self.assertEqual(r[0]["estado"], "a_triar")

    def test_upsert_conserva_clasificacion_y_cierra_resueltos(self):
        c = conexion(); qa_viaa.registrar(c, Q, "estatico", RES, [G], "a", "cmd")
        c.execute("UPDATE hallazgos SET estado='falso_positivo'"); qa_viaa.registrar(c, Q, "estatico", RES, [G], "b", "cmd")
        self.assertEqual(c.execute("SELECT estado FROM hallazgos").fetchone()[0], "falso_positivo")
        c.execute("UPDATE hallazgos SET estado='a_triar'"); qa_viaa.registrar(c, Q, "estatico", RES, [], "c", "cmd")
        self.assertEqual(c.execute("SELECT estado FROM hallazgos").fetchone()[0], "resuelto")

    def test_navegador_no_cierra_por_ausencia(self):
        c = conexion(); qa_viaa.registrar(c, Q, "navegador", RES, [G], "a", "cmd"); qa_viaa.registrar(c, Q, "navegador", RES, [], "b", "cmd")
        self.assertEqual(c.execute("SELECT estado FROM hallazgos").fetchone()[0], "a_triar")


class Familias(unittest.TestCase):
    def test_familia_de(self):
        f = qa_contratos.familia_de
        self.assertEqual(f("https://x.com/recomendaciones/libros/abc/"), "libros")
        self.assertEqual(f("https://x.com/editoriales/foo/"), "editoriales")
        self.assertEqual(f("https://x.com/cuaderno/post/"), "cuaderno")
        self.assertEqual(f("https://x.com/premios.html"), "generales")
        self.assertEqual(f("https://x.com/recomendaciones/"), "generales")


if __name__ == "__main__":
    unittest.main()
