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
        a = self.args.read_text(); self.assertIn("--tools Read,Grep,Glob", a); self.assertIn("--json-schema", a); self.assertIn(f"--max-budget-usd {mw.CFG['claude']['max_usd_llamada']}", a); self.assertIn("--no-session-persistence", a)
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

    def test_exit_1_con_json_dice_la_causa_real_y_el_limite_de_turnos_se_distingue(self):
        self.falso('echo \'{"type":"result","subtype":"error_max_turns","is_error":true,"result":"Reached max turns (6)","usage":{"service_tier":"standard"}}\'; exit 1')
        with self.assertRaises(claude_cli.ClaudeLimiteLlamada) as cm: self.llamar()
        self.assertIn("error_max_turns", str(cm.exception)); self.assertNotIn("service_tier", str(cm.exception))  # antes solo se veia la cola del JSON
        self.falso('echo \'{"subtype":"error_during_execution","result":"boom"}\'; exit 1')
        with self.assertRaises(claude_cli.ClaudeError) as cm: self.llamar(clave="k2")
        self.assertNotIsInstance(cm.exception, claude_cli.ClaudeLimiteLlamada); self.assertIn("error_during_execution", str(cm.exception))

    def test_investigar_repite_una_vez_con_mas_margen_si_agota_turnos(self):
        marca = Path(self.tmp.name) / "n"
        self.falso(f'if [ -f {marca} ]; then echo \'{{"structured_output": {{"decision": "aprobar"}}, "total_cost_usd": 0.2}}\'; else touch {marca}; echo \'{{"subtype":"error_max_turns","is_error":true,"result":"x"}}\'; exit 1; fi')
        import investigar
        investigar.CLAUDE_HOOK = None
        with mock.patch.object(mw, "preparar_src", return_value=Path(self.tmp.name)):
            r = investigar.claude(self.c, "k9", "contraste", "s", "e", ESQ)
        self.assertEqual(r, {"decision": "aprobar"})
        a = self.args.read_text().splitlines(); self.assertEqual(len(a), 2)
        t1 = int(a[0].split("--max-turns ")[1].split()[0]); t2 = int(a[1].split("--max-turns ")[1].split()[0]); self.assertGreater(t2, t1)

    def test_limite_semanal_pausa_claude_sin_gastar_mas_llamadas_ni_marcar_fallos(self):
        claude_cli._AGOTADA.clear(); self.addCleanup(claude_cli._AGOTADA.clear)
        resp = Path(self.tmp.name) / "resp.json"; resp.write_text(json.dumps({"subtype": "success", "is_error": True, "result": "You've hit your weekly limit \u00b7 resets Oct 30, 5am (Europe/Madrid)"}), encoding="utf-8")
        self.falso(f"cat {resp}; exit 1")
        with self.assertRaises(claude_cli.ClaudeSinCuota) as cm: self.llamar()
        self.assertIn("pausa hasta", str(cm.exception)); self.assertTrue(claude_cli.en_pausa(mw))
        n = self.args.read_text().count("\n")
        with self.assertRaises(claude_cli.ClaudeSinCuota): self.llamar(clave="otra")
        self.assertEqual(self.args.read_text().count("\n"), n)  # en pausa: ni se invoca a claude
        # un expediente esperando no cuenta fallo ni pasa a claude_fallo
        import investigar
        self.exp_preparado("MW-0001", estado="investigado"); e = self.c.execute("SELECT * FROM expedientes").fetchone()
        for _ in range(4): investigar._fallo_claude(self.c, e, claude_cli.ClaudeSinCuota("sin cuota"))
        self.assertEqual(self.c.execute("SELECT estado FROM expedientes").fetchone()[0], "investigado")
        self.assertNotIn("claude_fallos", json.loads(self.c.execute("SELECT datos FROM expedientes").fetchone()[0]))
        self.assertFalse(investigar.paso(self.c) and self.c.execute("SELECT estado FROM expedientes").fetchone()[0] != "investigado")  # no contrasta en pausa

    def test_reinicio_limite_entiende_el_aviso_y_si_no_devuelve_none(self):
        import datetime as dt
        ahora = dt.datetime(2026, 10, 28, 22, 0, tzinfo=dt.timezone.utc).timestamp()
        t = claude_cli.reinicio_limite("hit your weekly limit · resets Oct 30, 5am (UTC)", ahora)
        self.assertEqual(dt.datetime.fromtimestamp(t, dt.timezone.utc), dt.datetime(2026, 10, 30, 5, 0, tzinfo=dt.timezone.utc))
        self.assertEqual(dt.datetime.fromtimestamp(claude_cli.reinicio_limite("resets 3:30pm (UTC)", ahora), dt.timezone.utc), dt.datetime(2026, 10, 29, 15, 30, tzinfo=dt.timezone.utc))
        self.assertIsNone(claude_cli.reinicio_limite("sin fecha", ahora))

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
