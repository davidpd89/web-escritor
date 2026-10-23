import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import qa_contratos, qa_gpt


class Contratos(unittest.TestCase):
    def test_muestra_determinista(self):
        a = qa_contratos.muestra(qa_gpt.ROOT, "editoriales/*/index.html", 5)
        self.assertEqual(a, qa_contratos.muestra(qa_gpt.ROOT, "editoriales/*/index.html", 5))
        self.assertLessEqual(len(a), 5)

    def test_agrupa_fallos(self):
        r = qa_contratos.ejecutar(qa_gpt.ROOT, familias={"editoriales": ("editoriales/*/index.html", 6)})
        self.assertGreater(r["aserciones"], r["contratos"])
        self.assertLessEqual(r["fallos_unicos"], r["fallos_brutos"])


class ViaB(unittest.TestCase):
    def test_modo_lote(self):
        old = dict(qa_gpt.CFG)
        try:
            qa_gpt.CFG["modo_generacion"] = "lote"; qa_gpt.CFG["max_propuestas_lote"] = 15
            self.assertTrue(qa_gpt.lote_activo()); self.assertEqual(qa_gpt.tope_propuestas(), 15)
            qa_gpt.CFG["modo_generacion"] = "estricto"
            self.assertEqual(qa_gpt.tope_propuestas(), qa_gpt.CFG["max_propuestas"])
        finally:
            qa_gpt.CFG.clear(); qa_gpt.CFG.update(old)


if __name__ == "__main__":
    unittest.main()
