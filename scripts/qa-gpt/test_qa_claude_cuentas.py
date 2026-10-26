"""Cuentas de Claude de respaldo: un limite de uso salta a la siguiente cuenta; cualquier otro error no."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qa_claude as claude

ESQUEMA = {"type": "object", "properties": {"ok": {"type": "string"}}, "required": ["ok"]}
OK = json.dumps({"is_error": False, "structured_output": {"ok": "si"}, "usage": {}})
LIMITE = json.dumps({"is_error": True, "result": "Claude AI usage limit reached|1793000000", "usage": {}})


class TestCuentas(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name); (self.base / "claude").mkdir()
        self.extra = self.base / "cuenta2"; self.extra.mkdir()
        self.q = SimpleNamespace(STATE=self.base, now=lambda: "2026-10-26T12:00:00",
                                 CFG={"claude": {"cuentas_extra": [str(self.extra), str(self.base / "sin_login")]}})
        self.c = sqlite3.connect(":memory:"); self.addCleanup(self.c.close); claude.migrar(self.c)
        self.envs = []
        for p in (patch.object(claude, "exe", return_value="claude.exe"), patch.dict(claude._AGOTADA, clear=True)):
            p.start(); self.addCleanup(p.stop)

    def correr(self, salidas):
        def run(args, env=None, **kw):
            self.envs.append((env or {}).get("CLAUDE_CONFIG_DIR", ""))
            return subprocess.CompletedProcess(args, 0, salidas.pop(0), "")
        with patch.object(claude.subprocess, "run", side_effect=run):
            return claude.llamar(self.q, self.c, "k", "decision", "s", "e", ESQUEMA, usar_cache=False)

    def test_limite_salta_a_la_siguiente_y_la_recuerda(self):
        self.assertEqual(self.correr([LIMITE, OK])[0], {"ok": "si"})
        self.assertEqual(self.envs, ["", str(self.extra)])  # el dir sin crear (sin login) no se usa
        self.correr([OK])
        self.assertEqual(self.envs[-1], str(self.extra))  # la agotada no se reintenta durante la pausa

    def test_error_normal_no_cambia_de_cuenta(self):
        malo = json.dumps({"is_error": True, "result": "algo fallo", "usage": {}})
        with self.assertRaises(claude.ClaudeError): self.correr([malo, OK])
        self.assertEqual(self.envs, [""])

    def test_todas_en_limite_falla_y_reintenta_luego(self):
        with self.assertRaisesRegex(claude.ClaudeError, "en limite"): self.correr([LIMITE, LIMITE])
        self.assertEqual(self.correr([OK])[0], {"ok": "si"})  # sigue probando la que antes vuelve a estar libre


if __name__ == "__main__":
    unittest.main()
