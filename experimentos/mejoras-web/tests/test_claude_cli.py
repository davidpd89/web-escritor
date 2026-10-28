"""claude_cli con un ejecutable `claude` FALSO (script): comprueba el cableado real de la llamada (argumentos, esquema, coste, cache, limites) sin gastar nada."""
import json, os, stat, sys, unittest
from pathlib import Path
import util
import mw, claude_cli

ESQ = {"type": "object", "required": ["decision"], "properties": {"decision": {"type": "string", "enum": ["aprobar", "rechazar"]}}}


@unittest.skipIf(os.name == "nt", "script posix")
class Cli(util.Caso):
    def falso(self, cuerpo):
        f = Path(self.tmp.name) / "claude"; self.args = Path(self.tmp.name) / "args.txt"
        f.write_text(f"#!/bin/sh\necho \"$@\" >> {self.args}\ncat > /dev/null\n{cuerpo}\n"); f.chmod(f.stat().st_mode | stat.S_IEXEC)
        os.environ["MEJORAS_WEB_CLAUDE_EXE"] = str(f); claude_cli._CLAUDE_EXE = None
        self.addCleanup(lambda: (os.environ.pop("MEJORAS_WEB_CLAUDE_EXE", None), setattr(claude_cli, "_CLAUDE_EXE", None)))

    def llamar(self, **kw): return claude_cli.llamar(mw, self.c, kw.pop("clave", "k1"), "contraste", "sistema", "entrada", ESQ, **kw)

    def test_llamada_correcta_registra_coste_y_cachea(self):
        self.falso('echo \'{"structured_output": {"decision": "aprobar"}, "total_cost_usd": 0.0123, "num_turns": 2, "usage": {"input_tokens": 10, "output_tokens": 5}}\'')
        r, meta = self.llamar(herramientas="Read,Grep,Glob", cwd=self.tmp.name)
        self.assertEqual(r, {"decision": "aprobar"})
        a = self.args.read_text(); self.assertIn("--tools Read,Grep,Glob", a); self.assertIn("--json-schema", a); self.assertIn("--max-budget-usd 0.5", a); self.assertIn("--no-session-persistence", a)
        self.assertNotRegex(a, r"Edit|Write|Bash")  # Claude solo lee
        row = self.c.execute("SELECT * FROM claude_llamadas").fetchone(); self.assertEqual((row["ok"], row["coste_usd"], row["tok_out"]), (1, 0.0123, 5))
        r2, meta2 = self.llamar(herramientas="Read,Grep,Glob", cwd=self.tmp.name); self.assertTrue(meta2.get("cache"))  # misma evidencia = mismo veredicto, sin nueva llamada
        self.assertEqual(self.args.read_text().count("\n"), 1)
        self.assertEqual(claude_cli.resumen_consumo(self.c)["usd"], 0.012)

    def test_salida_fuera_de_esquema_o_error_nunca_es_decision(self):
        self.falso('echo \'{"structured_output": {"decision": "quizas"}, "total_cost_usd": 0.01}\'')
        with self.assertRaises(claude_cli.ClaudeError): self.llamar()
        self.falso('echo boom >&2; exit 3')
        with self.assertRaises(claude_cli.ClaudeError): self.llamar(clave="k2")
        self.falso('echo \'{"is_error": true, "result": "Overloaded"}\'')
        with self.assertRaises(claude_cli.ClaudeError): self.llamar(clave="k3")
        self.assertEqual(self.c.execute("SELECT COUNT(*) FROM claude_llamadas WHERE ok=0").fetchone()[0], 3)

    def test_tope_diario_se_aplica_antes_de_llamar(self):
        self.falso('echo ejecutado >> ' + str(Path(self.tmp.name) / "marca") + '; echo \'{"structured_output": {"decision": "aprobar"}}\'')
        self.c.execute("INSERT INTO claude_llamadas(fecha,clave,tipo,coste_usd,ok) VALUES(?,?,?,?,1)", (mw.now(), "x", "t", 11.0)); self.c.commit()
        mw.CFG["claude"]["max_usd_dia"] = 10
        with self.assertRaisesRegex(claude_cli.ClaudeError, "tope diario"): self.llamar()
        self.assertFalse((Path(self.tmp.name) / "marca").exists())  # ni se invoco al ejecutable

    def test_sin_ejecutable_error_claro(self):
        os.environ["MEJORAS_WEB_CLAUDE_EXE"] = "/no/existe/claude"; claude_cli._CLAUDE_EXE = None
        self.addCleanup(lambda: os.environ.pop("MEJORAS_WEB_CLAUDE_EXE", None))
        with mock.patch("shutil.which", return_value=None), mock.patch.object(Path, "home", return_value=Path(self.tmp.name)):
            with self.assertRaisesRegex(claude_cli.ClaudeError, "no encontrado"): claude_cli.exe()


from unittest import mock  # noqa: E402

if __name__ == "__main__":
    unittest.main()
