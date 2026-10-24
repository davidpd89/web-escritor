#!/usr/bin/env python3
"""Preflight: no red, ni Claude, ni GitHub Actions."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

LAB=Path(__file__).resolve().parent
sys.path.insert(0,str(LAB/"motor"))
import preflight
import claude_cli


class PreflightTests(unittest.TestCase):
    def test_offline_no_hace_llamadas_a_servicios(self):
        with mock.patch.object(preflight.subprocess,"run") as run:
            run.return_value.returncode=0
            run.return_value.stdout="research/mejoras-local\n"
            resultado=preflight.verificar(real=False)
        self.assertTrue(resultado["ok"],resultado)
        self.assertEqual(len(resultado["controles"]),3)
        run.assert_called_once()

    def test_offline_no_acepta_main(self):
        with mock.patch.object(preflight.subprocess,"run") as run:
            run.return_value.returncode=0
            run.return_value.stdout="main\n"
            resultado=preflight.verificar(real=False)
        self.assertFalse(resultado["ok"])

    def test_ejecutable_cmd_no_reemplaza_claude_nativo(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrapper=Path(tmp)/"claude.cmd"
            wrapper.write_text("@echo off",encoding="utf-8")
            with mock.patch.dict(os.environ,{"LAB_CLAUDE_EXE":str(wrapper)}), \
                 mock.patch.object(claude_cli,"_CLAUDE_EXE",None), \
                 mock.patch("shutil.which",return_value=None), \
                 mock.patch.object(Path,"home",return_value=Path(tmp)):
                with self.assertRaises(claude_cli.ClaudeError):
                    claude_cli.exe()


if __name__=="__main__":
    unittest.main()
