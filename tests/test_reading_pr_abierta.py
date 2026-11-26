"""Una CI de la PR de datos que no acaba a tiempo no pone la carga en rojo (26/11, carga 45797789304).

Actions estaba lleno de PR y broken-links/pa11y/reflow de la PR de datos #1598 no terminaron: `publish_generated`
lanzaba TimeoutError y la carga salía roja con los datos sanos, aunque la siguiente carga reanuda esa PR
(`resume_pending`). Ahora es un aviso: la carga sale bien, el punto de guardado se conserva y la cadena sigue.
"""
import ast
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('refresh_pr_abierta', ROOT / 'scripts/refresh-reading-catalogue.py')
refresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refresh)
publication = refresh.publisher.publication


class PrAbiertaNoPoneLaCargaEnRojo(unittest.TestCase):
    def test_ci_timeout_with_open_pr_is_a_warning(self):
        exc = publication.PrAbierta("CI timed out; PR left open: ['pa11y-baseline.yml']")
        with patch.object(refresh, 'refresh', side_effect=exc), \
             patch.object(refresh, 'chain_report') as report, \
             patch.object(refresh, 'drop_checkpoint') as drop:
            refresh.main(True)  # sin SystemExit: el paso de la carga sale con 0
        report.assert_called_once()
        self.assertEqual(report.call_args.args, (0,))
        self.assertIn('pa11y-baseline.yml', report.call_args.kwargs['pr_abierta'])
        drop.assert_not_called()  # el punto de guardado sigue: la cadena continúa y la reanudación no reconsulta

    def test_other_failures_still_fail(self):
        for exc in (RuntimeError('pa11y-baseline.yml failed'), TimeoutError('Pages did not complete')):
            with self.subTest(exc=exc), patch.object(refresh, 'refresh', side_effect=exc), \
                 patch.object(refresh, 'chain_report') as report:
                with self.assertRaises(type(exc)):
                    refresh.main(True)
                report.assert_not_called()

    def test_every_open_pr_timeout_uses_pr_abierta(self):
        """Ningún TimeoutError que deje la PR abierta para el siguiente cron se queda como fallo de la carga."""
        tree = ast.parse((ROOT / 'scripts/publish-radar-refresh.py').read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                text = ast.unparse(node.exc).lower()
                if node.exc.func.id == 'TimeoutError':  # un fallo real de la CI (RuntimeError) sigue rojo
                    self.assertNotRegex(text, 'pr abierta|pr left open', ast.unparse(node))


if __name__ == '__main__':
    unittest.main()
