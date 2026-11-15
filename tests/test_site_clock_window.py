"""Ventana de reloj: tolerante en PR, estricta donde se decide y vigila la frescura."""
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from site_clock import GRACIA_DIAS, clock_window  # noqa: E402

NOW = datetime(2026, 11, 15, 23, 30, tzinfo=timezone.utc)  # 00:30 del 16 en Madrid


class ClockWindow(unittest.TestCase):
    def test_tolerante_hoy_primero_y_gracia(self):
        with mock.patch.dict(os.environ, {"RELOJ_ESTRICTO": ""}):
            days = clock_window(NOW)
        self.assertEqual(days[0].isoformat(), "2026-11-16")
        self.assertEqual(len(days), GRACIA_DIAS + 1)
        self.assertEqual(days[-1].isoformat(), "2026-11-14")

    def test_estricto_solo_hoy(self):
        with mock.patch.dict(os.environ, {"RELOJ_ESTRICTO": "1"}):
            self.assertEqual([d.isoformat() for d in clock_window(NOW)], ["2026-11-16"])

    def test_quien_decide_refrescar_es_estricto(self):
        # Si el refresco fuese tolerante, vería «al día» unos generados de ayer y no regeneraría.
        for wf in ("radar-clock-refresh.yml", "postdeploy-deep-audit.yml"):
            text = (ROOT / ".github" / "workflows" / wf).read_text(encoding="utf-8")
            self.assertIn('RELOJ_ESTRICTO: "1"', text, wf)


if __name__ == "__main__":
    unittest.main()
