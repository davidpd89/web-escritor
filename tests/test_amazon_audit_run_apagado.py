"""El bucle `run` que lee amazon.es desde la IP de casa no arranca sin permiso expreso (19/11)."""
import importlib.util, os, pathlib, sys, unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('audit', ROOT / 'scripts/reading-amazon-audit.py')
audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)


class RunApagado(unittest.TestCase):
    def test_sin_permiso_no_entra_en_el_bucle(self):
        env = {k: v for k, v in os.environ.items() if k != audit.PERMISO_SCRAPING}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(audit, 'loop') as loop:
            with self.assertRaises(SystemExit):
                audit.main(['run'])
            loop.assert_not_called()

    def test_con_permiso_entra(self):
        with mock.patch.dict(os.environ, {audit.PERMISO_SCRAPING: '1'}), mock.patch.object(audit, 'loop') as loop:
            audit.main(['run'])
            loop.assert_called_once()


if __name__ == '__main__':
    unittest.main()
